"""Provider client factories and credential selection."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
import re
from threading import Lock
import time
from typing import Callable, Iterable, Mapping

from dotenv import dotenv_values
from google import genai
from groq import AsyncGroq

from app.config import get_settings


_NUMBERED_GEMINI_KEY = re.compile(r"^GEMINI_API_KEY_([1-9][0-9]*)$")


def _dotenv_environment() -> Mapping[str, str | None]:
    """Read the same local dotenv file as Settings without emitting its values."""

    try:
        return dotenv_values(".env")
    except OSError:
        return {}


def _numbered_key_values(source: Mapping[str, object]) -> dict[int, str]:
    values: dict[int, str] = {}
    for name, raw_value in source.items():
        match = _NUMBERED_GEMINI_KEY.fullmatch(str(name).upper())
        if match is None or raw_value is None:
            continue
        value = str(raw_value).strip()
        if value:
            values[int(match.group(1))] = value
    return values


def _settings_environment(settings: object) -> dict[str, object]:
    """Expose only Gemini setting attributes, including future numbered fields."""

    values: dict[str, object] = {}
    for name in dir(settings):
        normalized = name.upper()
        if normalized == "GEMINI_API_KEY" or _NUMBERED_GEMINI_KEY.fullmatch(normalized):
            values[normalized] = getattr(settings, name)
    return values


def _bare_key_value(source: Mapping[str, object]) -> str | None:
    raw_value = source.get("GEMINI_API_KEY")
    if raw_value is None:
        return None
    value = str(raw_value).strip()
    return value or None


def configured_gemini_api_keys(
    *,
    settings: object | None = None,
    dotenv_environment: Mapping[str, object] | None = None,
    environment: Mapping[str, object] | None = None,
) -> tuple[str, ...]:
    """Return configured credentials in numeric slot order without exposing them.

    Numbered keys are collected from dotenv, declared settings, and the process
    environment. Later sources override earlier sources, matching normal runtime
    configuration precedence. Any positive slot number is accepted; this lets
    separate Gemini projects participate in a deterministic pool without a code
    change when another credential is added.
    """

    resolved_settings = settings or get_settings()
    sources: tuple[Mapping[str, object], ...] = (
        dotenv_environment
        if dotenv_environment is not None
        else _dotenv_environment(),
        _settings_environment(resolved_settings),
        environment if environment is not None else os.environ,
    )
    slots: dict[int, str] = {}
    bare_key: str | None = None
    for source in sources:
        slots.update(_numbered_key_values(source))
        source_bare_key = _bare_key_value(source)
        if source_bare_key is not None:
            bare_key = source_bare_key

    candidates = [slots[index] for index in sorted(slots)]
    if bare_key is not None:
        candidates.append(bare_key)

    ordered: list[str] = []
    seen: set[str] = set()
    for key in candidates:
        if key and key not in seen:
            seen.add(key)
            ordered.append(key)
    return tuple(ordered)


class GeminiKeyPoolExhaustedError(RuntimeError):
    """No configured credential can be retried in the current operation."""

    code = "gemini_key_pool_exhausted"

    def __init__(
        self,
        *,
        attempted_slots: Iterable[int] = (),
        retry_after_seconds: float | None = None,
        model_unavailable: bool = False,
    ) -> None:
        self.attempted_slots = tuple(sorted(set(attempted_slots)))
        self.retry_after_seconds = retry_after_seconds
        self.model_unavailable = bool(model_unavailable)
        suffix = (
            f"; retry_after_seconds={retry_after_seconds:.3f}"
            if retry_after_seconds is not None
            else ""
        )
        super().__init__(f"{self.code}{suffix}")


@dataclass
class _CredentialState:
    permanently_disabled: bool = False
    # A model can be unavailable for one Google project but healthy for a
    # different model scope using the same API key.
    model_unavailable: bool = False
    cooldown_until: float = 0.0
    transient_failure_count: int = 0
    failure_epoch: int = 0


class GeminiCredentialManager:
    """Select credentials without repeating a slot in one logical operation."""

    _DEFAULT_QUOTA_SCOPE = "__default__"
    _AUTH_FAILURE_STATUS = {401, 403}
    _MODEL_UNAVAILABLE_STATUS = {404}
    _RATE_LIMIT_STATUS = {429}
    _TRANSIENT_STATUS = {408, 500, 502, 503, 504}
    _RATE_LIMIT_BASE_SECONDS = 60.0
    _RATE_LIMIT_CAP_SECONDS = 15.0 * 60.0
    _TRANSIENT_BASE_SECONDS = 5.0
    _TRANSIENT_CAP_SECONDS = 60.0

    def __init__(
        self,
        keys: tuple[str, ...],
        *,
        clock: Callable[[], float] = time.monotonic,
    ):
        if not keys:
            raise RuntimeError("No Gemini API credential is configured.")
        self._keys = keys
        self._clock = clock
        self._active_slot = 0
        self._request_cursor = 0
        self._states = [_CredentialState() for _ in keys]
        # Gemini quota is model-scoped. A 429 for Flash-Lite must not mark the
        # same credential unavailable for a separate configured fallback model.
        self._states_by_quota_scope: dict[str, list[_CredentialState]] = {
            self._DEFAULT_QUOTA_SCOPE: self._states
        }
        # Credential authentication is independent of model quotas. A key that
        # returns 401/403 must be avoided by every model chain immediately.
        self._globally_disabled_slots: set[int] = set()
        self._clients: dict[int, genai.Client] = {}
        self._lock = Lock()

    @property
    def active_slot(self) -> int:
        return self._active_slot

    @property
    def credential_count(self) -> int:
        return len(self._keys)

    def active_client(self) -> genai.Client:
        return self.active_client_with_slot()[1]

    def _quota_scope(self, quota_scope: str | None) -> str:
        normalized = str(quota_scope or "").strip()
        return normalized or self._DEFAULT_QUOTA_SCOPE

    def _states_for_scope(self, quota_scope: str | None) -> list[_CredentialState]:
        scope = self._quota_scope(quota_scope)
        states = self._states_by_quota_scope.get(scope)
        if states is None:
            states = [_CredentialState() for _ in self._keys]
            self._states_by_quota_scope[scope] = states
        return states

    def active_client_with_slot(
        self,
        *,
        quota_scope: str | None = None,
    ) -> tuple[int, genai.Client]:
        with self._lock:
            slot = self._next_healthy_slot(
                self._active_slot,
                quota_scope=quota_scope,
            )
            if slot is None:
                raise self._pool_exhausted((), quota_scope=quota_scope)
            self._active_slot = slot
            return slot, self._client_for_slot(slot)

    def request_client_with_slot(
        self,
        *,
        attempted_slots: Iterable[int] = (),
        quota_scope: str | None = None,
    ) -> tuple[int, genai.Client]:
        """Round-robin normal requests across every healthy credential."""

        slot, client, _failure_epoch = self.request_attempt_with_slot(
            attempted_slots=attempted_slots,
            quota_scope=quota_scope,
        )
        return slot, client

    def request_attempt_with_slot(
        self,
        *,
        attempted_slots: Iterable[int] = (),
        quota_scope: str | None = None,
    ) -> tuple[int, genai.Client, int]:
        """Lease a healthy slot and its current failure epoch atomically."""

        attempted = frozenset(attempted_slots)
        with self._lock:
            slot = self._next_healthy_slot(
                self._request_cursor,
                attempted_slots=attempted,
                quota_scope=quota_scope,
            )
            if slot is None:
                raise self._pool_exhausted(attempted, quota_scope=quota_scope)
            self._request_cursor = (slot + 1) % len(self._keys)
            return (
                slot,
                self._client_for_slot(slot),
                self._states_for_scope(quota_scope)[slot].failure_epoch,
            )

    def _client_for_slot(self, slot: int) -> genai.Client:
        client = self._clients.get(slot)
        if client is None:
            client = genai.Client(api_key=self._keys[slot])
            self._clients[slot] = client
        return client

    def _next_healthy_slot(
        self,
        start: int,
        *,
        attempted_slots: frozenset[int] = frozenset(),
        quota_scope: str | None = None,
    ) -> int | None:
        now = self._clock()
        states = self._states_for_scope(quota_scope)
        for offset in range(len(self._keys)):
            slot = (start + offset) % len(self._keys)
            state = states[slot]
            if (
                slot not in attempted_slots
                and slot not in self._globally_disabled_slots
                and not state.permanently_disabled
                and not state.model_unavailable
                and state.cooldown_until <= now
            ):
                return slot
        return None

    def _pool_exhausted(
        self,
        attempted_slots: Iterable[int],
        *,
        quota_scope: str | None = None,
    ) -> GeminiKeyPoolExhaustedError:
        now = self._clock()
        states = self._states_for_scope(quota_scope)
        eligible_scope_states = [
            state
            for slot, state in enumerate(states)
            if slot not in self._globally_disabled_slots
        ]
        retry_delays = [
            max(0.0, state.cooldown_until - now)
            for slot, state in enumerate(states)
            if (
                slot not in self._globally_disabled_slots
                and not state.permanently_disabled
                and not state.model_unavailable
                and state.cooldown_until > now
            )
        ]
        return GeminiKeyPoolExhaustedError(
            attempted_slots=attempted_slots,
            retry_after_seconds=min(retry_delays) if retry_delays else None,
            model_unavailable=bool(eligible_scope_states) and all(
                state.model_unavailable for state in eligible_scope_states
            ),
        )

    def record_success(self, slot: int, *, quota_scope: str | None = None) -> None:
        with self._lock:
            self._record_success_locked(slot, quota_scope=quota_scope)

    def record_success_if_current(
        self,
        slot: int,
        failure_epoch: int,
        *,
        quota_scope: str | None = None,
    ) -> bool:
        """Ignore success from work that started before a newer slot failure."""

        with self._lock:
            if self._states_for_scope(quota_scope)[slot].failure_epoch != failure_epoch:
                return False
            self._record_success_locked(slot, quota_scope=quota_scope)
            return True

    def _record_success_locked(self, slot: int, *, quota_scope: str | None = None) -> None:
        state = self._states_for_scope(quota_scope)[slot]
        state.cooldown_until = 0.0
        state.transient_failure_count = 0
        self._active_slot = slot

    def record_failure(
        self,
        *,
        attempted_slot: int,
        status: int | None = None,
        retry_after_seconds: float | None = None,
        transport_failure: bool = False,
        quota_scope: str | None = None,
    ) -> bool:
        """Record one failed attempt and report whether another slot is eligible."""

        with self._lock:
            state = self._states_for_scope(quota_scope)[attempted_slot]
            if status in self._AUTH_FAILURE_STATUS:
                state.failure_epoch += 1
                state.permanently_disabled = True
                self._globally_disabled_slots.add(attempted_slot)
                state.cooldown_until = 0.0
            elif (
                status in self._MODEL_UNAVAILABLE_STATUS
                and quota_scope not in {None, self._DEFAULT_QUOTA_SCOPE}
            ):
                state.failure_epoch += 1
                state.model_unavailable = True
                state.cooldown_until = 0.0
            elif status in self._RATE_LIMIT_STATUS:
                state.failure_epoch += 1
                state.transient_failure_count += 1
                if retry_after_seconds is None:
                    delay = min(
                        self._RATE_LIMIT_BASE_SECONDS
                        * (2 ** (state.transient_failure_count - 1)),
                        self._RATE_LIMIT_CAP_SECONDS,
                    )
                else:
                    delay = min(
                        max(0.0, retry_after_seconds),
                        self._RATE_LIMIT_CAP_SECONDS,
                    )
                state.cooldown_until = max(
                    state.cooldown_until,
                    self._clock() + delay,
                )
            elif status in self._TRANSIENT_STATUS or transport_failure:
                state.failure_epoch += 1
                state.transient_failure_count += 1
                delay = min(
                    self._TRANSIENT_BASE_SECONDS
                    * (2 ** (state.transient_failure_count - 1)),
                    self._TRANSIENT_CAP_SECONDS,
                )
                state.cooldown_until = max(
                    state.cooldown_until,
                    self._clock() + delay,
                )
            else:
                return False

            replacement = self._next_healthy_slot(
                (attempted_slot + 1) % len(self._keys),
                quota_scope=quota_scope,
            )
            if replacement is not None:
                self._active_slot = replacement
            return replacement is not None

    def rotate_after_status(
        self,
        status: int | None,
        *,
        attempted_slot: int | None = None,
        retry_after_seconds: float | None = None,
        quota_scope: str | None = None,
    ) -> bool:
        failed_slot = self._active_slot if attempted_slot is None else attempted_slot
        return self.record_failure(
            attempted_slot=failed_slot,
            status=status,
            retry_after_seconds=retry_after_seconds,
            quota_scope=quota_scope,
        )


@lru_cache(maxsize=1)
def get_gemini_credential_manager() -> GeminiCredentialManager:
    return GeminiCredentialManager(configured_gemini_api_keys())


def get_gemini_client() -> genai.Client:
    """Compatibility accessor for the currently active Gemini credential."""
    return get_gemini_credential_manager().active_client()


def reset_ai_clients() -> None:
    """Clear cached provider clients after a settings change in tests."""

    get_gemini_credential_manager.cache_clear()
    get_groq_client.cache_clear()


@lru_cache
def get_groq_client() -> AsyncGroq:
    """Groq client (70B teach / challenge / GD peers)."""
    api_key = get_settings().groq_api_key
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set; required when calling the Groq client."
        )
    return AsyncGroq(api_key=api_key)

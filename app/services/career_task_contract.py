"""Immutable context for the exact Career Prep task visible to the learner."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class CareerTaskContract:
    prompt_id: str
    context_id: str
    active_role: str = ""
    active_topic: str = ""
    semantic_anchors: tuple[str, ...] = ()
    participant_claims: tuple[Mapping[str, str], ...] = ()
    evidence_policy: str = "learner_owned_or_sourced"
    hypothetical: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "semantic_anchors",
            tuple(str(item).strip() for item in self.semantic_anchors if str(item).strip()),
        )
        claims = tuple(
            MappingProxyType({
                str(key): str(value).strip()
                for key, value in dict(item).items()
                if str(key).strip() and str(value).strip()
            })
            for item in self.participant_claims
            if isinstance(item, Mapping)
        )
        object.__setattr__(self, "participant_claims", claims)

    def model_dump(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "context_id": self.context_id,
            "active_role": self.active_role,
            "active_topic": self.active_topic,
            "semantic_anchors": list(self.semantic_anchors),
            "participant_claims": copy.deepcopy([dict(item) for item in self.participant_claims]),
            "evidence_policy": self.evidence_policy,
            "hypothetical": self.hypothetical,
        }

    @classmethod
    def from_payload(cls, payload: Any) -> "CareerTaskContract | None":
        if not isinstance(payload, dict):
            return None
        prompt_id = str(payload.get("prompt_id") or "").strip()
        context_id = str(payload.get("context_id") or "").strip()
        if not prompt_id or not context_id:
            return None
        return cls(
            prompt_id=prompt_id,
            context_id=context_id,
            active_role=str(payload.get("active_role") or "").strip(),
            active_topic=str(payload.get("active_topic") or "").strip(),
            semantic_anchors=tuple(
                payload.get("semantic_anchors")
                if isinstance(payload.get("semantic_anchors"), (list, tuple))
                else ()
            ),
            participant_claims=tuple(
                payload.get("participant_claims")
                if isinstance(payload.get("participant_claims"), (list, tuple))
                else ()
            ),
            evidence_policy=(
                str(payload.get("evidence_policy") or "learner_owned_or_sourced").strip()
                or "learner_owned_or_sourced"
            ),
            hypothetical=bool(payload.get("hypothetical")),
        )

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> "CareerTaskContract | None":
        return cls.from_payload(state.get("active_task_contract"))

"""Operation-scoped latency policy for School open-answer evaluation.

The policy deliberately lives outside the global AI provider. Career calls keep
their existing provider budgets; School callers choose their own request and
worker behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SchoolEvaluationPolicy:
    browser_ack_timeout_seconds: float
    inline_evaluation_timeout_seconds: float | None
    worker_evaluation_timeout_seconds: float | None
    worker_stall_timeout_seconds: float | None
    max_worker_attempts: int


def school_evaluation_policy(
    settings: object,
) -> SchoolEvaluationPolicy:
    """Return the one policy used by School answer workers.

    Local Qwen remains unbounded for normal evaluation once work has been
    durably queued. It still has a long worker-only watchdog so a wedged model
    cannot monopolize the serial queue forever. Cloud evaluation is bounded so
    a provider retry can never become a child-facing request timeout.
    """

    backend: Literal["local", "cloud", "gemini"] | str = str(
        getattr(settings, "ai_backend", "local")
    )
    if backend == "local":
        return SchoolEvaluationPolicy(
            browser_ack_timeout_seconds=2.0,
            inline_evaluation_timeout_seconds=None,
            worker_evaluation_timeout_seconds=None,
            worker_stall_timeout_seconds=10 * 60,
            max_worker_attempts=1,
        )
    return SchoolEvaluationPolicy(
        browser_ack_timeout_seconds=2.0,
        inline_evaluation_timeout_seconds=6.0,
        # The browser has already received an asynchronous acknowledgement. One
        # bounded cloud pass is preferable to holding a child-facing item in a
        # retry loop for a minute or more when Gemini is quota-limited.
        worker_evaluation_timeout_seconds=12.0,
        worker_stall_timeout_seconds=None,
        max_worker_attempts=1,
    )


__all__ = ["SchoolEvaluationPolicy", "school_evaluation_policy"]

from types import SimpleNamespace

from app.services.school import evaluation_policy


def test_cloud_school_evaluation_policy_acknowledges_fast_and_finishes_async():
    policy = evaluation_policy.school_evaluation_policy(
        SimpleNamespace(ai_backend="gemini")
    )

    assert policy.browser_ack_timeout_seconds == 2.0
    assert policy.inline_evaluation_timeout_seconds == 6.0
    assert policy.worker_evaluation_timeout_seconds == 30.0
    assert policy.max_worker_attempts == 2


def test_local_school_evaluation_policy_never_cuts_off_qwen_worker():
    policy = evaluation_policy.school_evaluation_policy(
        SimpleNamespace(ai_backend="local")
    )

    assert policy.browser_ack_timeout_seconds == 2.0
    assert policy.inline_evaluation_timeout_seconds is None
    assert policy.worker_evaluation_timeout_seconds is None

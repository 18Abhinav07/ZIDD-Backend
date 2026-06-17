# tests/test_session_start_request_model.py
from app.models import SessionStartRequest


def test_confirm_defaults_false():
    req = SessionStartRequest(user_id="u1", competency_node="n1")
    assert req.confirm is False


def test_confirm_can_be_set_true():
    req = SessionStartRequest(user_id="u1", competency_node="n1", confirm=True)
    assert req.confirm is True

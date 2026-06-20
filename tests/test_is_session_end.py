"""TDD: _is_session_end — natural goodbye detection + answer-guard.

Defect: exact-match only + <=5-word gate misses multi-word goodbye variants
and longer farewell sentences.

RED tests (must all fail before fix):
  - natural goodbye variants that the old code missed
GREEN guard (must stay passing):
  - answer-guard phrases that must NOT fire session end
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("SUPABASE_POOLER_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test")

import pytest  # noqa: E402
from app.services.session_service import _is_session_end  # noqa: E402


# ---------------------------------------------------------------------------
# TRUE POSITIVES — must return True (farewell signals)
# ---------------------------------------------------------------------------

class TestFarewellVariants:
    """Natural goodbye phrases that should end the session."""

    # --- existing exact-match phrases (must stay working) ---
    def test_bare_bye(self):
        assert _is_session_end("bye") is True

    def test_bare_done(self):
        assert _is_session_end("done") is True

    def test_goodbye(self):
        assert _is_session_end("goodbye") is True

    def test_thats_all(self):
        assert _is_session_end("that's all") is True

    def test_im_done(self):
        assert _is_session_end("im done") is True

    # --- NEW variants that were broken ---
    def test_ok_bye(self):
        assert _is_session_end("ok bye") is True

    def test_bye_bye(self):
        assert _is_session_end("bye bye") is True

    def test_thanks_bye(self):
        assert _is_session_end("thanks bye") is True

    def test_im_done_for_today(self):
        assert _is_session_end("im done for today") is True

    def test_long_farewell_with_bye(self):
        assert _is_session_end("ok thanks, bye, I have to go now") is True

    def test_trailing_punctuation(self):
        assert _is_session_end("bye!") is True

    def test_mixed_case_bye(self):
        assert _is_session_end("BYE") is True

    def test_done_for_now(self):
        assert _is_session_end("done for now") is True

    def test_im_done_now(self):
        assert _is_session_end("im done now") is True


# ---------------------------------------------------------------------------
# FALSE POSITIVES — must return False (answer-guard)
# ---------------------------------------------------------------------------

class TestAnswerGuard:
    """Messages that CONTAIN goodbye words but are answers, not farewells."""

    def test_done_with_homework(self):
        assert _is_session_end("done with my homework") is False

    def test_done_chapter(self):
        assert _is_session_end("i'm done with chapter 3") is False

    def test_stop_means(self):
        assert _is_session_end("stop means to cease activity") is False

    def test_empty_string(self):
        assert _is_session_end("") is False

    def test_normal_answer(self):
        assert _is_session_end("communication is the exchange of ideas between people") is False

    def test_none_input(self):
        assert _is_session_end(None) is False  # type: ignore[arg-type]


class TestQuitExitAreContentWords:
    """Regression: substantive answers that MENTION quitting/exiting must be
    scored, not silently discarded as farewells. "quit"/"exit" are ordinary
    English content words; only a SHORT message signals a real farewell."""

    # --- substantive answers that must NOT end the session ---
    def test_explain_a_gap_answer_with_quit(self):
        # int_12_explain_a_gap's whole purpose is accounting for leaving a role.
        assert _is_session_end(
            "I had to quit my previous job because of a relocation, but I grew a lot."
        ) is False

    def test_gd_persuade_with_exit(self):
        assert _is_session_end("We should exit that market segment and refocus") is False

    def test_strength_answer_with_quit(self):
        assert _is_session_end("I never quit when a project gets hard") is False

    def test_determination_with_quit(self):
        assert _is_session_end("I will not quit no matter what happens") is False

    def test_exit_strategy_answer(self):
        assert _is_session_end("our exit strategy should be a phased rollout") is False

    # --- genuine short quit/exit intent must STILL end the session ---
    def test_bare_quit_still_ends(self):
        assert _is_session_end("quit") is True       # exact-match tier

    def test_bare_exit_still_ends(self):
        assert _is_session_end("exit") is True        # exact-match tier

    def test_short_i_quit_still_ends(self):
        assert _is_session_end("i quit") is True      # ≤3 words, ambiguous token

    def test_short_lets_exit_still_ends(self):
        assert _is_session_end("let's exit") is True

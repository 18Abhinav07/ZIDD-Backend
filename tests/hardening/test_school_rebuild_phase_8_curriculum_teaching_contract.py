import asyncio
import copy
import hashlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import school_rebuild_routes
from app.content.school_v3_schema import (
    SchoolV3RubricCriterion,
    SchoolV3RubricEvaluation,
)
from app.main import app
from app.services import school_rebuild_curriculum as curriculum
from app.services import school_rebuild_placement as placement

AUTH = {"Authorization": "Bearer test_token"}

RAINBOW_JOURNEY_PARAGRAPH = (
    "Last Sunday I travelled to Jaipur by train with my parents. We left home early and reached "
    "the station before sunrise. During the journey I watched green fields, small villages, and bright "
    "birds through the window. We visited the fort, tasted warm kachori, and walked through a busy "
    "market. I liked the colourful shops and the view from the fort, but I disliked the afternoon heat. "
    "In the evening we returned home tired, happy, and excited to share our photographs."
)

WISE_PARROT_STORY_CONTINUATION = (
    "After escaping from the golden cage, the parrot flew towards the forest and found its wise friend. "
    "It thanked the friend for showing a clever way to become free. The two birds visited the merchant "
    "garden the next morning. The parrot explained that love should not keep anyone trapped. The merchant "
    "felt sorry, opened the empty cage, and filled a feeder with fruit. From then on, many birds visited "
    "him freely, and he enjoyed their songs."
)


@pytest.fixture(autouse=True)
def _stub_school_open_answer_evaluator(monkeypatch):
    async def evaluate(activity: dict[str, Any], answer: str) -> SchoolV3RubricEvaluation:
        return SchoolV3RubricEvaluation(
            schema_version="school-v3-rubric-1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.9,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.9,
                    evidence_quote=answer[:120] or "(empty answer)",
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        evaluate,
        raising=False,
    )


def _run(coro):
    return asyncio.run(coro)


def _profile_payload(*, target_class_no: int = 3) -> dict:
    return {
        "display_name": "Open Assets Learner",
        "school_name": "Open Assets Test School",
        "board_id": "cbse",
        "target_class_no": target_class_no,
        "subject_ids": ["english"],
        "preferred_teaching_language": "hi_en",
        "english_comfort": "medium",
        "learner_goal": f"I want to understand Class {target_class_no} English chapters.",
        "parent_goal": "Build confidence without memorising answers.",
        "prior_difficulty_signals": ["reading", "vocabulary"],
    }


def _activate_school_profile(client: TestClient, payload: dict):
    saved = client.post(
        "/school/onboarding",
        headers=AUTH,
        json={
            **payload,
            "current_step": 4,
            "request_id": str(uuid4()),
        },
    )
    assert saved.status_code == 200
    draft = saved.json()["draft"]
    return client.post(
        "/school/onboarding/complete",
        headers=AUTH,
        json={
            "profile_version_id": draft["profile_version_id"],
            "expected_revision": draft["draft_revision"],
            "request_id": str(uuid4()),
        },
    )


def _seed_school_profile(store, *, target_class_no: int = 3) -> dict[str, Any]:
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    response = _activate_school_profile(
        TestClient(app),
        _profile_payload(target_class_no=target_class_no),
    )
    assert response.status_code == 200
    return response.json()["profile"]


def _seed_direct_curriculum_report_lineage(store, profile: dict[str, Any]) -> None:
    envelope = placement.new_placement_envelope(profile)
    for _ in range(30):
        item = placement.next_item(envelope)
        if item is None:
            break
        envelope = placement.apply_answer(envelope, item, "wrong")
    placement_status = placement.placement_status(envelope)
    assert placement_status != "in_progress"
    placement_session_id = "direct-curriculum-placement"
    session = {
        "session_id": placement_session_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "placement",
        "subject_id": "english",
        "class_no": int(profile["target_class_no"]),
        "current_stage": envelope.state.stage,
        "profile_version_id": profile["profile_version_id"],
        "source_placement_report_id": None,
        "state_json": placement.envelope_to_json(envelope),
    }
    _run(
        store.upsert_school_session(
            **session,
            status="active",
        )
    )
    _run(
        store.upsert_school_session(
            **session,
            status=placement_status,
        )
    )
    _run(
        store.upsert_school_placement_report(
            report_id="placement-report",
            user_id="test_user",
            profile_version_id=profile["profile_version_id"],
            placement_session_id=placement_session_id,
            placement_status="below_target",
        )
    )


def _complete_weak_placement(client: TestClient) -> None:
    current = client.post("/school/placement/start", headers=AUTH).json()
    session_id = current["session_id"]
    for _ in range(20):
        item = current["next_item"]
        if item is None:
            break
        response = client.post(
            f"/school/placement/{session_id}/answer",
            headers=AUTH,
            json={"item_id": item["item_id"], "answer": "wrong"},
        )
        assert response.status_code == 200
        current = response.json()
    assert current["status"] == "below_target"


def _correct_recap_answer(activity: dict[str, Any]) -> str:
    focus = activity["focus"].lower()
    kind = activity["kind"]
    answers = {
        ("recognize naming words", "guided_check"): "teacher",
        ("recognize naming words", "independent_check"): "flower",
        ("understand a simple sentence", "guided_check"): "mat",
        ("understand a simple sentence", "independent_check"): "mangoes",
        ("use context to understand a word", "guided_check"): "small",
        ("use context to understand a word", "independent_check"): "smart",
        ("write a complete sentence", "guided_check"): "sitting",
        ("write a complete sentence", "independent_check"): "ran",
        ("answer with a reason", "guided_check"): "dark",
        ("answer with a reason", "independent_check"): "thirsty",
        ("find the main idea", "guided_check"): "Aman caring for plants",
        ("find the main idea", "independent_check"): "children reading in a library",
        ("use because to give a reason", "guided_check"): "because",
        ("use because to give a reason", "independent_check"): "because",
        ("use past tense", "guided_check"): "went",
        ("use past tense", "independent_check"): "played",
    }
    return answers[(focus, kind)]


def _complete_recap_success_path(client: TestClient) -> dict:
    _complete_weak_placement(client)
    assert client.get("/school/placement/report", headers=AUTH).status_code == 200
    body = client.post("/school/recap/start", headers=AUTH).json()
    session_id = body["session_id"]
    guard = 0
    while body["current_activity"] is not None:
        guard += 1
        assert guard <= 40
        activity = body["current_activity"]
        response = client.post(
            f"/school/recap/{session_id}/answer",
            headers=AUTH,
            json={
                "activity_id": activity["activity_id"],
                "answer": _correct_recap_answer(activity),
            },
        )
        assert response.status_code == 200
        body = response.json()
    assert body["status"] == "complete"
    return body


def _complete_target_ready_placement(client: TestClient) -> dict:
    current = client.post("/school/placement/start", headers=AUTH).json()
    session_id = current["session_id"]
    guard = 0
    while current["next_item"] is not None:
        guard += 1
        assert guard <= 20
        item = current["next_item"]
        saved = _run(
            school_rebuild_routes.get_storage().get_school_session(
                "test_user",
                session_id,
            )
        )
        private_item = placement.find_item(
            placement.envelope_from_json(saved["state_json"]),
            item["item_id"],
        )
        answer = (
            private_item.answer_key
            or next(iter(private_item.accepted_answers), None)
            or "I used the passage clues and answered in a complete English sentence."
        )
        response = client.post(
            f"/school/placement/{session_id}/answer",
            headers=AUTH,
            json={"item_id": item["item_id"], "answer": answer},
        )
        assert response.status_code == 200
        current = response.json()
    assert current["status"] == "target_ready"
    report = client.get("/school/placement/report", headers=AUTH)
    assert report.status_code == 200
    body = report.json()
    assert body["placement_status"] == "target_ready"
    assert body["unlock_state"] == "target_unlocked"
    return body


def _assert_no_hidden_keys(payload: Any) -> None:
    forbidden = {
        "answer_key",
        "answer_rule",
        "accepted_answers",
        "model_answer",
        "rubric",
        "rubric_criteria",
        "pass_score",
        "evaluation_mode",
        "preflight_rule",
        "threshold",
        "skill_scores",
        "weak_skill_ids",
        "remediation_skill_ids",
        "failed_rubric_item_ids",
        "failed_hard_blocker_item_ids",
    }
    if isinstance(payload, dict):
        assert not (forbidden & set(payload)), f"hidden key leaked: {forbidden & set(payload)}"
        for value in payload.values():
            _assert_no_hidden_keys(value)
    elif isinstance(payload, list):
        for value in payload:
            _assert_no_hidden_keys(value)


def test_curriculum_read_reconciles_saved_certification_once(store, monkeypatch):
    profile = _seed_school_profile(store, target_class_no=5)
    _seed_direct_curriculum_report_lineage(store, profile)
    session_id = str(uuid4())
    old_state = {
        "engine_version": "school-rebuild-curriculum-2",
        "status": "active",
        "phase": "needs_support",
        "subject_id": "english",
        "target_class_no": 5,
        "active_learning_class_no": 5,
        "chapter": {
            "chapter_id": "eng_c5_ch01",
            "chapter_no": 1,
            "title": "Papa's Spectacles",
            "content_version": "chapter-v1",
            "certification_version": "certification-v1",
        },
        "levels": [],
        "completed_chapter_ids": [],
        "chapter_assessment": {"attempt_history": []},
        "support_required": {"reason": "chapter_check_attempts_exhausted"},
    }
    _run(
        store.upsert_school_session(
            session_id=session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=5,
            status="active",
            current_stage="chapter_check",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=old_state,
        )
    )
    repaired_state = {
        **old_state,
        "engine_version": curriculum.ENGINE_VERSION,
        "status": "complete",
        "phase": "complete",
        "completed_chapter_ids": ["eng_c5_ch01"],
        "support_required": None,
        "chapter_assessment": {
            "attempt_history": [
                {
                    "attempt_no": 2,
                    "score": 0.99,
                    "passed": True,
                    "skill_scores": {
                        "reading.paragraph_main_idea": 1.0,
                        "writing.summary_own_words": 0.98,
                    },
                }
            ]
        },
    }
    repair = {
        "kind": "chapter_certification_reconciled",
        "chapter_id": "eng_c5_ch01",
        "attempt_no": 2,
        "skill_scores": {
            "reading.paragraph_main_idea": 1.0,
            "writing.summary_own_words": 0.98,
        },
    }

    def reconcile(state):
        if state.get("engine_version") == curriculum.ENGINE_VERSION:
            return state, None
        return repaired_state, repair

    monkeypatch.setattr(curriculum, "reconcile_curriculum_state", reconcile)
    client = TestClient(app)

    first = client.get(f"/school/curriculum/{session_id}", headers=AUTH)
    second = client.get(f"/school/curriculum/{session_id}", headers=AUTH)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "complete"
    assert first.json()["phase"] == "complete"
    saved = _run(store.get_school_session("test_user", session_id))
    assert saved["status"] == "complete"
    assert saved["state_json"]["engine_version"] == curriculum.ENGINE_VERSION
    profiles = {
        row["skill_id"]: row
        for row in _run(store.get_learning_graph("test_user"))["profiles"]
        if row.get("domain") == "school"
    }
    for skill_id, score in (
        ("reading.paragraph_main_idea", 1.0),
        ("writing.summary_own_words", 0.98),
    ):
        profile_row = profiles[skill_id]
        assert profile_row["mastery"] == 0.0
        assert profile_row["readiness"] == 0.0
        assert profile_row["attempts"] == 0
        assert profile_row["evidence_json"]["latest_certification"] == {
            "session_id": session_id,
            "chapter_id": "eng_c5_ch01",
            "score": score,
        }


def _answer(body: dict, answer: str, client: TestClient) -> dict:
    activity = body["current_activity"]
    response = client.post(
        f"/school/curriculum/{body['session_id']}/answer",
        headers=AUTH,
        json={"activity_id": activity["activity_id"], "answer": answer},
    )
    assert response.status_code == 200
    result = response.json()
    _assert_no_hidden_keys(result)
    return result


def _correct_curriculum_answer(activity: dict[str, Any]) -> str:
    answers = {
        ("colour_sharing_reason", "guided_check"): "share",
        ("colour_sharing_reason", "independent_check"): "share",
        ("colour_word_meaning", "guided_check"): "blue",
        ("colour_word_meaning", "independent_check"): "purple",
        ("action_words_in_colour_play", "guided_check"): "jump",
        ("action_words_in_colour_play", "independent_check"): "writes",
        ("alphabetical_colour_order", "guided_check"): "blue",
        ("alphabetical_colour_order", "independent_check"): "black",
        ("word_friends", "guided_check"): "rainbow",
        ("word_friends", "independent_check"): "rainbow",
        ("badal_moti_care_reason", "guided_check"): "care for the puppy",
        ("badal_moti_care_reason", "independent_check"): "care for Moti",
        ("badal_moti_story_sequence", "guided_check"): "Badal cares for Moti",
        ("badal_moti_story_sequence", "independent_check"): "Badal and Moti become friends",
        ("badal_moti_past_tense_ed", "guided_check"): "helped",
        ("badal_moti_past_tense_ed", "independent_check"): "played",
        ("badal_moti_question_statement", "guided_check"): "Can Moti stay with us?",
        ("badal_moti_question_statement", "independent_check"): "question",
        ("badal_moti_friendship_summary", "guided_check"): "kindness and friendship can help us",
        ("badal_moti_friendship_summary", "independent_check"): "friendship",
        ("best_friends_team_reason", "guided_check"): "together",
        ("best_friends_team_reason", "independent_check"): "work together",
        ("best_friends_shape_clues", "guided_check"): "circle",
        ("best_friends_shape_clues", "independent_check"): "triangle",
        ("best_friends_a_an", "guided_check"): "an",
        ("best_friends_a_an", "independent_check"): "a",
        ("best_friends_describe_friend", "guided_check"): "kind",
        ("best_friends_describe_friend", "independent_check"): "My friend is kind.",
        ("best_friends_action_words", "guided_check"): "bark",
        ("best_friends_action_words", "independent_check"): "jump",
        ("out_garden_picture_clues", "guided_check"): "playing",
        ("out_garden_picture_clues", "independent_check"): "open space",
        ("out_garden_ball_actions", "guided_check"): "bounce",
        ("out_garden_ball_actions", "independent_check"): "catch",
        ("out_garden_kite_actions", "guided_check"): "fly",
        ("out_garden_kite_actions", "independent_check"): "pull",
        ("out_garden_and_pairs", "guided_check"): "sing and dance",
        ("out_garden_and_pairs", "independent_check"): "run and catch",
        ("out_garden_safety_reason", "guided_check"): "be careful",
        ("out_garden_safety_reason", "independent_check"): "play safely",
        ("talking_toys_story_order", "guided_check"): "toy shop",
        ("talking_toys_story_order", "independent_check"): "train",
        ("talking_toys_toy_words", "guided_check"): "doll",
        ("talking_toys_toy_words", "independent_check"): "marbles",
        ("talking_toys_describing_words", "guided_check"): "red",
        ("talking_toys_describing_words", "independent_check"): "soft elephant",
        ("talking_toys_plural_words", "guided_check"): "toys",
        ("talking_toys_plural_words", "independent_check"): "boxes",
        ("talking_toys_process_order", "guided_check"): "first",
        ("talking_toys_process_order", "independent_check"): "finally",
        ("paper_boats_story_setting", "guided_check"): "stream",
        ("paper_boats_story_setting", "independent_check"): "paper boats",
        ("paper_boats_feeling_reason", "guided_check"): "angry",
        ("paper_boats_feeling_reason", "independent_check"): "because he overturned her boats",
        ("paper_boats_help_sequence", "guided_check"): "fold",
        ("paper_boats_help_sequence", "independent_check"): "showed him how to make a boat",
        ("paper_boats_he_she", "guided_check"): "she",
        ("paper_boats_he_she", "independent_check"): "he",
        ("paper_boats_position_words", "guided_check"): "under",
        ("paper_boats_position_words", "independent_check"): "on",
        ("big_laddoo_poem_image", "guided_check"): "big laddoo",
        ("big_laddoo_poem_image", "independent_check"): "big splash",
        ("big_laddoo_round_things", "guided_check"): "laddoo",
        ("big_laddoo_round_things", "independent_check"): "ball",
        ("big_laddoo_sense_clues", "guided_check"): "touch",
        ("big_laddoo_sense_clues", "independent_check"): "round and sweet",
        ("big_laddoo_blend_words", "guided_check"): "blue",
        ("big_laddoo_blend_words", "independent_check"): "plum",
        ("big_laddoo_float_sink", "guided_check"): "float",
        ("big_laddoo_float_sink", "independent_check"): "sink",
        ("thank_god_fruit_choice", "guided_check"): "grapes",
        ("thank_god_fruit_choice", "independent_check"): "grapes were light",
        ("thank_god_story_reason", "guided_check"): "watermelons",
        ("thank_god_story_reason", "independent_check"): "watermelons would hurt more",
        ("thank_god_opposites", "guided_check"): "light",
        ("thank_god_opposites", "independent_check"): "short",
        ("thank_god_is_are", "guided_check"): "are",
        ("thank_god_is_are", "independent_check"): "is",
        ("thank_god_salad_sequence", "guided_check"): "first",
        ("thank_god_salad_sequence", "independent_check"): "finally",
        ("madhu_wish_kind_action", "guided_check"): "old man",
        ("madhu_wish_kind_action", "independent_check"): "he was kind",
        ("madhu_wish_water_need", "guided_check"): "water",
        ("madhu_wish_water_need", "independent_check"): "water is important",
        ("madhu_wish_food_groups", "guided_check"): "fruits",
        ("madhu_wish_food_groups", "independent_check"): "samosa",
        ("madhu_wish_and_but", "guided_check"): "and",
        ("madhu_wish_and_but", "independent_check"): "but",
        ("madhu_wish_because_reason", "guided_check"): "because",
        ("madhu_wish_because_reason", "independent_check"): "because he needed water",
        ("night_poem_mood", "guided_check"): "night",
        ("night_poem_mood", "independent_check"): "dark and still",
        ("night_sun_path", "guided_check"): "hill",
        ("night_sun_path", "independent_check"): "behind the hill",
        ("night_sky_words", "guided_check"): "stars",
        ("night_sky_words", "independent_check"): "moon",
        ("night_blend_sounds", "guided_check"): "star",
        ("night_blend_sounds", "independent_check"): "sky",
        ("night_sun_compounds", "guided_check"): "sunlight",
        ("night_sun_compounds", "independent_check"): "sunset",
        ("chanda_mama_moon_shape", "guided_check"): "moon",
        ("chanda_mama_moon_shape", "independent_check"): "the moon changes shape",
        ("chanda_mama_counting_problem", "guided_check"): "stars",
        ("chanda_mama_counting_problem", "independent_check"): "too many stars",
        ("chanda_mama_sun_help", "guided_check"): "sun",
        ("chanda_mama_sun_help", "independent_check"): "children and stars",
        ("chanda_mama_here_there", "guided_check"): "here",
        ("chanda_mama_here_there", "independent_check"): "there",
        ("chanda_mama_countable_groups", "guided_check"): "fingers",
        ("chanda_mama_countable_groups", "independent_check"): "hairs",
        ("chandrayaan_rani_questions", "guided_check"): "curious",
        ("chandrayaan_rani_questions", "independent_check"): "she asked many questions",
        ("chandrayaan_moon_news", "guided_check"): "moon",
        ("chandrayaan_moon_news", "independent_check"): "india reached the moon",
        ("chandrayaan_scientist_help", "guided_check"): "scientist",
        ("chandrayaan_scientist_help", "independent_check"): "a rocket",
        ("chandrayaan_word_meaning", "guided_check"): "moon vehicle",
        ("chandrayaan_word_meaning", "independent_check"): "chandra means moon",
        ("chandrayaan_date_sentence", "guided_check"): "23 august 2023",
        ("chandrayaan_date_sentence", "independent_check"): "Chandrayaan landed on 23 August 2023.",
        ("together_we_can_teamwork", "guided_check"): "teamwork",
        ("together_we_can_teamwork", "independent_check"): "teamwork",
        ("together_we_can_helping_reason", "guided_check"): "Meera could get the ball safely",
        ("together_we_can_helping_reason", "independent_check"): "she helped him find the library",
        ("together_we_can_unity_words", "guided_check"): "unity",
        ("together_we_can_unity_words", "independent_check"): "unity",
        ("together_we_can_collective_nouns", "guided_check"): "herd",
        ("together_we_can_collective_nouns", "independent_check"): "swarm",
        ("together_we_can_fair_solution", "guided_check"): "listen to both",
        ("together_we_can_fair_solution", "independent_check"): "take turns",
        ("tinkling_bells_honesty_choice", "guided_check"): "return the extra money",
        ("tinkling_bells_honesty_choice", "independent_check"): "return the extra money",
        ("tinkling_bells_story_sequence", "guided_check"): "a shopkeeper gave extra change",
        ("tinkling_bells_story_sequence", "independent_check"): "he received extra change",
        ("tinkling_bells_compare_adjectives", "guided_check"): "smallest",
        ("tinkling_bells_compare_adjectives", "independent_check"): "brighter",
        ("tinkling_bells_opposites", "guided_check"): "ugly",
        ("tinkling_bells_opposites", "independent_check"): "loudly",
        ("tinkling_bells_careful_sentence", "guided_check"): "because",
        ("tinkling_bells_careful_sentence", "independent_check"): "I should return the extra change because it is not mine.",
        ("be_safe_crossing_steps", "guided_check"): "stop and look both ways",
        ("be_safe_crossing_steps", "independent_check"): "look right left and right again",
        ("be_safe_safe_unsafe", "guided_check"): "unsafe",
        ("be_safe_safe_unsafe", "independent_check"): "safe",
        ("be_safe_sign_meaning", "guided_check"): "school ahead",
        ("be_safe_sign_meaning", "independent_check"): "no honking",
        ("be_safe_countable_nouns", "guided_check"): "buses",
        ("be_safe_countable_nouns", "independent_check"): "traffic",
        ("be_safe_promise_sentence", "guided_check"): "because",
        ("be_safe_promise_sentence", "independent_check"): "I will use the footpath because it keeps me away from traffic.",
        ("one_thing_focus_message", "guided_check"): "one task at a time",
        ("one_thing_focus_message", "independent_check"): "finish one task before starting another",
        ("one_thing_rhyme_words", "guided_check"): "day and way",
        ("one_thing_rhyme_words", "independent_check"): "bright and right",
        ("one_thing_word_meanings", "guided_check"): "strength",
        ("one_thing_word_meanings", "independent_check"): "short times",
        ("one_thing_ing_sentences", "guided_check"): "is reading",
        ("one_thing_ing_sentences", "independent_check"): "are playing",
        ("one_thing_routine_paragraph", "guided_check"): "after",
        ("one_thing_routine_paragraph", "independent_check"): "I finish my homework before I play because one thing done well is better.",
        ("old_stag_kindness_reason", "guided_check"): "kindness",
        ("old_stag_kindness_reason", "independent_check"): "he cared for everyone",
        ("old_stag_resource_choice", "guided_check"): "leave grass for him",
        ("old_stag_resource_choice", "independent_check"): "share wisely",
        ("old_stag_describing_words", "guided_check"): "tender",
        ("old_stag_describing_words", "independent_check"): "shaded spot",
        ("old_stag_adverbs_manner", "guided_check"): "slowly",
        ("old_stag_adverbs_manner", "independent_check"): "carefully",
        ("old_stag_thank_you_note", "guided_check"): "because",
        ("old_stag_thank_you_note", "independent_check"): "Thank you for bringing food because it helped me recover.",
        ("braille_touch_reading", "guided_check"): "raised dots",
        ("braille_touch_reading", "independent_check"): "reading by touch",
        ("braille_louis_invention", "guided_check"): "simplified it",
        ("braille_louis_invention", "independent_check"): "he made reading by touch easier",
        ("braille_new_words", "guided_check"): "blacksmith",
        ("braille_new_words", "independent_check"): "invented",
        ("braille_spl_words", "guided_check"): "splendid",
        ("braille_spl_words", "independent_check"): "splash",
        ("braille_was_were_ing", "guided_check"): "was reading",
        ("braille_was_were_ing", "independent_check"): "were helping",
        ("fit_body_activity_clues", "guided_check"): "hockey",
        ("fit_body_activity_clues", "independent_check"): "music",
        ("fit_body_adjectives", "guided_check"): "swift runner",
        ("fit_body_adjectives", "independent_check"): "healthy food",
        ("fit_body_rhyme_words", "guided_check"): "race and pace",
        ("fit_body_rhyme_words", "independent_check"): "joy and boy",
        ("fit_body_double_letters", "guided_check"): "running",
        ("fit_body_double_letters", "independent_check"): "balloon",
        ("fit_body_word_meanings", "guided_check"): "mistakes",
        ("fit_body_word_meanings", "independent_check"): "proudly",
        ("lagori_rules_comprehension", "guided_check"): "seven stones",
        ("lagori_rules_comprehension", "independent_check"): "stack and avoid the ball",
        ("lagori_team_sequence", "guided_check"): "referee blew the whistle",
        ("lagori_team_sequence", "independent_check"): "Prakash set the seventh stone",
        ("lagori_word_meanings", "guided_check"): "opponent",
        ("lagori_word_meanings", "independent_check"): "boundary",
        ("lagori_sentence_order", "guided_check"): "The field is marked with a boundary.",
        ("lagori_sentence_order", "independent_check"): "Everybody looked at Prakash with surprise.",
        ("lagori_sentence_question", "guided_check"): "question",
        ("lagori_sentence_question", "independent_check"): "sentence",
        ("hekko_word_meaning", "guided_check"): "challenging the tiger",
        ("hekko_word_meaning", "independent_check"): "challenge",
        ("hekko_team_rules", "guided_check"): "11",
        ("hekko_team_rules", "independent_check"): "human chain",
        ("hekko_joko_surrender", "guided_check"): "surrender",
        ("hekko_joko_surrender", "independent_check"): "the game ends",
        ("hekko_homophones", "guided_check"): "There",
        ("hekko_homophones", "independent_check"): "their",
        ("hekko_past_tense", "guided_check"): "visited",
        ("hekko_past_tense", "independent_check"): "decided",
        ("swing_view_clues", "guided_check"): "rivers and trees",
        ("swing_view_clues", "independent_check"): "garden green",
        ("swing_feeling_reason", "guided_check"): "pleasantest thing",
        ("swing_feeling_reason", "independent_check"): "he enjoys swinging",
        ("swing_sentence_stringing", "guided_check"): "Mira watched the clouds",
        ("swing_sentence_stringing", "independent_check"): "Mira watched the clouds from the swing.",
        ("swing_noun_verb", "guided_check"): "verb",
        ("swing_noun_verb", "independent_check"): "noun",
        ("swing_prepositions", "guided_check"): "between",
        ("swing_prepositions", "independent_check"): "under",
        ("mountain_story_sequence", "guided_check"): "Himalayas",
        ("mountain_story_sequence", "independent_check"): "river",
        ("mountain_vocabulary_context", "guided_check"): "Sherpa",
        ("mountain_vocabulary_context", "independent_check"): "journey",
        ("mountain_animals_and_care", "guided_check"): "milk, wool, and carrying loads",
        ("mountain_animals_and_care", "independent_check"): "protect the mountains",
        ("mountain_body_part_metaphors", "guided_check"): "foot",
        ("mountain_body_part_metaphors", "independent_check"): "mouth",
        ("mountain_conjunctions", "guided_check"): "because",
        ("mountain_conjunctions", "independent_check"): "but",
        ("maheshwar_dialogue_facts", "guided_check"): "Queen Ahilya Bai",
        ("maheshwar_dialogue_facts", "independent_check"): "Narmada River",
        ("maheshwar_fort_features", "guided_check"): "overhanging balconies",
        ("maheshwar_fort_features", "independent_check"): "red stones",
        ("maheshwar_synonyms_odd_one", "guided_check"): "thrilled",
        ("maheshwar_synonyms_odd_one", "independent_check"): "kind",
        ("maheshwar_silent_g", "guided_check"): "sign",
        ("maheshwar_silent_g", "independent_check"): "design",
        ("maheshwar_articles", "guided_check"): "an",
        ("maheshwar_articles", "independent_check"): "the",
        ("papas_spectacles_story_details", "guided_check"): "spectacles",
        ("papas_spectacles_story_details", "independent_check"): "on his head",
        ("papas_spectacles_word_meaning", "guided_check"): "eyeglasses",
        ("papas_spectacles_word_meaning", "independent_check"): "looked quickly",
        ("papas_spectacles_ordering", "guided_check"): "handkerchief",
        ("papas_spectacles_ordering", "independent_check"): "cherry",
        ("papas_spectacles_pair_phrases", "guided_check"): "shoes",
        ("papas_spectacles_pair_phrases", "independent_check"): "socks",
        ("papas_spectacles_prepositions", "guided_check"): "around",
        ("papas_spectacles_prepositions", "independent_check"): "on",
        ("gone_scooter_story_sequence", "guided_check"): "hockey ball",
        ("gone_scooter_story_sequence", "independent_check"): "scooter basket",
        ("gone_scooter_honest_owner", "guided_check"): "four months ago",
        ("gone_scooter_honest_owner", "independent_check"): "ask around",
        ("gone_scooter_action_words", "guided_check"): "small taps",
        ("gone_scooter_action_words", "independent_check"): "take suddenly",
        ("gone_scooter_connectors", "guided_check"): "because",
        ("gone_scooter_connectors", "independent_check"): "however",
        ("gone_scooter_oo_compounds", "guided_check"): "school",
        ("gone_scooter_oo_compounds", "independent_check"): "football",
        ("rainbow_image_bridge", "guided_check"): "a bridge from earth to sky",
        ("rainbow_image_bridge", "independent_check"): "it joins earth and sky",
        ("rainbow_word_meanings", "guided_check"): "over",
        ("rainbow_word_meanings", "independent_check"): "bridge",
        ("rainbow_reference_words", "guided_check"): "boats",
        ("rainbow_reference_words", "independent_check"): "ships and boats",
        ("rainbow_rhyme_sound", "guided_check"): "rain",
        ("rainbow_rhyme_sound", "independent_check"): "sky",
        ("rainbow_compound_words", "guided_check"): "rainbow",
        ("rainbow_compound_words", "independent_check"): "wristwatch",
        ("rainbow_noun_verb_use", "guided_check"): "noun",
        ("rainbow_noun_verb_use", "independent_check"): "verb",
        ("rainbow_opposites", "guided_check"): "slow",
        ("rainbow_opposites", "independent_check"): "straight",
        ("rainbow_travel_paragraph", "guided_check"): "past tense",
        ("rainbow_travel_paragraph", "independent_check"): "I travelled by bus with my family.",
        ("rainbow_journey_writing", "guided_check"): "Plan B",
        ("rainbow_journey_writing", "independent_check"): RAINBOW_JOURNEY_PARAGRAPH,
        ("rainbow_colour_order", "guided_check"): "violet",
        ("rainbow_colour_order", "independent_check"): "yellow",
        ("rainbow_natural_human_made", "guided_check"): "human-made",
        ("rainbow_natural_human_made", "independent_check"): "light and water droplets form it",
        ("wise_parrot_story_sequence", "guided_check"): "a greeting",
        ("wise_parrot_story_sequence", "independent_check"): "it became still so the trader took it out",
        ("wise_parrot_freedom_reason", "guided_check"): "it could not fly freely",
        ("wise_parrot_freedom_reason", "independent_check"): "the forest parrot because it showed an escape plan",
        ("wise_parrot_words_phrases", "guided_check"): "worried and upset",
        ("wise_parrot_words_phrases", "independent_check"): "going to soon",
        ("wise_parrot_collective_nouns", "guided_check"): "flight",
        ("wise_parrot_collective_nouns", "independent_check"): "bunch",
        ("wise_parrot_present_perfect", "guided_check"): "have visited",
        ("wise_parrot_present_perfect", "independent_check"): "have written",
        ("wise_parrot_bird_sanctuary", "guided_check"): "safe habitats help birds",
        ("wise_parrot_bird_sanctuary", "independent_check"): "they give birds food and shelter",
        ("wise_parrot_ai_oi_sounds", "guided_check"): "soil",
        ("wise_parrot_ai_oi_sounds", "independent_check"): "sail",
        ("wise_parrot_opinion_reason", "guided_check"): "let the bird fly safely",
        ("wise_parrot_opinion_reason", "independent_check"): "let it fly because freedom matters",
        ("wise_parrot_story_continuation", "guided_check"): "Plan B",
        ("wise_parrot_story_continuation", "independent_check"): WISE_PARROT_STORY_CONTINUATION,
        ("wise_parrot_bird_feeder_steps", "guided_check"): "clean the container",
        ("wise_parrot_bird_feeder_steps", "independent_check"): (
            "First clean the container, next add fresh grains and water, then place it "
            "safely, and finally clean it regularly."
        ),
        ("frog_between_two_homes", "guided_check"): "a damp stone and pond water",
        ("frog_between_two_homes", "independent_check"): (
            "It hopped on moss and later hid in the ditch filled with water."
        ),
        ("frog_between_two_homes", "masterclass"): (
            "The pond habitat provides different useful places: reeds provide shelter, "
            "and the frog dives below the surface to escape."
        ),
        ("frog_from_spawn_to_adult", "guided_check"): "a cluster of frog eggs",
        ("frog_from_spawn_to_adult", "independent_check"): (
            "Eggs hatch into tadpoles, which grow legs as their tails shrink."
        ),
        ("frog_from_spawn_to_adult", "masterclass"): (
            "Eggs hatch into tadpoles, and tadpoles grow legs before they grow into adult frogs."
        ),
        ("frog_fast_food_and_defence", "guided_check"): (
            "to catch the beetle before it escapes"
        ),
        ("frog_fast_food_and_defence", "independent_check"): (
            "Its speckles match the stones, and it slips under the root to hide."
        ),
        ("frog_fast_food_and_defence", "masterclass"): (
            "Camouflage makes it hard to see, while the frog dives underwater to escape."
        ),
        ("frog_motion_comparison", "guided_check"): (
            "long back legs and wide back feet"
        ),
        ("frog_motion_comparison", "independent_check"): (
            "Both the frog and fish swim through water. The fish uses fins and remains "
            "in water, while the frog kicks with webbed back feet and can also cross "
            "wet ground."
        ),
        ("frog_motion_comparison", "masterclass"): (
            "The frog has smoother skin than the toad and jumps farther than the toad."
        ),
        ("frog_calls_and_connectors", "guided_check"): (
            "the call grows louder because the inflated throat pouch vibrates"
        ),
        ("frog_calls_and_connectors", "independent_check"): (
            "A frog may call next to the drain or among the grass. Even though the grass "
            "is a long way from the pond, its voice carries to the water."
        ),
        ("frog_calls_and_connectors", "masterclass"): (
            "A frog may call from the reeds or the muddy bank, and its repeated croaks "
            "travel across the pond."
        ),
        ("frog_sentence_sequence", "guided_check"): (
            "The frog catches an insect."
        ),
        ("frog_sentence_sequence", "independent_check"): (
            "The frog enters the pond because the bank is dry."
        ),
        ("frog_sentence_sequence", "masterclass"): (
            "The frog slips under a leaf because the sun is hot."
        ),
        ("frog_friendly_reply", "guided_check"): (
            "Hi Kabir, I saw tiny legs on our tadpoles yesterday."
        ),
        ("frog_friendly_reply", "independent_check"): (
            "Hi Maya, I often see frogs near our garden after rain. They hide beside "
            "wet leaves and call loudly from the drain. I watch quietly without touching "
            "them. Do frogs visit the wetland near you too? Best wishes, Open Assets"
        ),
        ("frog_friendly_reply", "masterclass"): (
            "Hi Dev, I saw frogs at the park and they were jumping near the pond. "
            "Did you see frogs there yesterday?"
        ),
    }
    if activity["kind"] == "chapter_check":
        item_id = activity["activity_id"].split(":", 2)[-1]
        assessment_answers = {
            "eng_c5_ch05_assess_01": (
                "The frog rests under a fern on the muddy bank, then dives into the "
                "stream when footsteps approach."
            ),
            "eng_c5_ch05_assess_02": (
                "A larva is a young stage, like a newly hatched tadpole."
            ),
            "eng_c5_ch05_assess_03": (
                "Tadpoles hatch from eggs and tadpoles grow into adult frogs."
            ),
            "eng_c5_ch05_assess_04": (
                "The frog remains under a rock because the ground is hot and dry at midday."
            ),
            "eng_c5_ch05_assess_05": "it reaches the moth quickly without a chase",
            "eng_c5_ch05_assess_06": (
                "The frog has webbed feet, and its webbed feet help it swim by pushing water."
            ),
            "eng_c5_ch05_assess_07": (
                "A tree frog may call from a branch or from a wall."
            ),
            "eng_c5_ch05_assess_08": "the frog swims across the pond",
            "eng_c5_ch05_assess_09": "predators may fail to notice the frog",
            "eng_c5_ch05_assess_10": (
                "Calling helps frogs hear each other and communicate across the distance."
            ),
            "eng_c5_ch05_assess_11": (
                "Both the frog and fish swim through water. The fish uses fins and stays "
                "in water, while the frog kicks with webbed back feet and crosses wet ground."
            ),
            "eng_c5_ch05_assess_12": "it jumps from the brick into the trough",
            "eng_c5_ch05_assess_13": (
                "A predator is an animal that hunts other animals and eats the animals it hunts."
            ),
            "eng_c5_ch05_assess_14": "amphibian",
            "eng_c5_ch05_assess_15": (
                "A tadpole begins with a tail, later grows front and hind legs, and finally "
                "its tail becomes tiny."
            ),
            "eng_c5_ch05_assess_16": (
                "the frog opens its mouth and its sticky tongue catches a fly"
            ),
            "eng_c5_ch05_assess_17": (
                "Powerful hind legs help it leap away quickly from danger across the pond bank."
            ),
            "eng_c5_ch05_assess_18": "the pond supplies several things frogs need",
            "eng_c5_ch05_assess_19": (
                "The speckled pattern makes the frog hard to see, so the bird has trouble "
                "seeing it."
            ),
            "eng_c5_ch05_assess_20": (
                "the front legs appear and the tail becomes shorter"
            ),
            "eng_c5_ch05_assess_21": (
                "The ground below the tap is damp, and the frog chooses it because it is damp."
            ),
            "eng_c5_ch05_assess_22": (
                "Hi Aman, frogs sometimes appear near my garden after rain. I stay back and "
                "watch quietly so I do not frighten them. Did the frog near your rain barrel "
                "return the next day? Best wishes, Open Assets"
            ),
            "eng_c5_ch05_assess_23": (
                "The frog hides because a shadow crosses the pond."
            ),
            "eng_c5_ch05_assess_24": (
                "Camouflage hides the frog, webbed feet help it swim, and its quick tongue "
                "catches insects for food."
            ),
            "eng_c5_ch05_assess_25": (
                "Both the frog and toad move on land. The frog has smoother skin and more "
                "webbing for swimming, while the toad has rougher skin and takes shorter hops."
            ),
            "eng_c5_ch05_assess_26": (
                "Hi Zoya, I hear frogs near school after heavy rain. Their repeated calls "
                "travel from the grass to the pond. I listen from the playground. Do the "
                "frogs near your classroom call before sunset too? Best wishes, Open Assets"
            ),
        }
        return assessment_answers[item_id]
    return answers[(activity["level_id"], activity["kind"])]


def _complete_current_curriculum_session(
    body: dict[str, Any],
    client: TestClient,
) -> dict:
    guard = 0
    while body["current_activity"] is not None:
        guard += 1
        assert guard <= 30
        activity = body["current_activity"]
        body = _answer(body, _correct_curriculum_answer(activity), client)
        if str(activity["level_id"]).startswith("frog_"):
            assert body["last_feedback"]["correct"] is True, activity
    assert body["status"] == "complete"
    return body


def _seed_curriculum_activity_session(
    store,
    *,
    session_id: str,
    chapter: dict[str, Any],
    level_id: str,
) -> dict[str, Any]:
    profile = _seed_school_profile(store, target_class_no=5)
    _seed_direct_curriculum_report_lineage(store, profile)
    levels = copy.deepcopy(chapter["levels"])
    level_index = next(
        index for index, level in enumerate(levels) if level["level_id"] == level_id
    )
    for index, level in enumerate(levels):
        level["status"] = "complete" if index < level_index else "not_started"
        level["current_step"] = "complete" if index < level_index else "guided_check"
        level["attempts"] = []
    levels[level_index]["status"] = "in_progress"
    levels[level_index]["current_step"] = "independent_check"
    state = curriculum.normalize_curriculum_state(
        {
            "engine_version": curriculum.ENGINE_VERSION,
            "profile_version_id": profile["profile_version_id"],
            "status": "active",
            "subject_id": "english",
            "target_class_no": 5,
            "active_learning_class_no": 5,
            "source_recap_session_id": None,
            "source_placement_report_id": "placement-report",
            "chapter": {key: value for key, value in chapter.items() if key != "levels"},
            "completed_chapter_ids": [],
            "completed_chapter_versions": {},
            "carry_forward_focuses": [],
            "current_level_index": level_index,
            "levels": levels,
            "last_feedback": None,
        }
    )
    _run(
        store.upsert_school_session(
            session_id=session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=5,
            status="active",
            current_stage=str(level_index),
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=state,
        )
    )
    return state


def _seed_frog_chapter_check_session(store, *, session_id: str) -> dict[str, Any]:
    profile = _seed_school_profile(store, target_class_no=5)
    _seed_direct_curriculum_report_lineage(store, profile)
    chapter = copy.deepcopy(
        next(
            candidate
            for candidate in curriculum._available_chapters("english", 5)
            if candidate["chapter_id"] == "eng_c5_ch05"
        )
    )
    levels = copy.deepcopy(chapter["levels"])
    for level in levels:
        level["status"] = "complete"
        level["current_step"] = "complete"
        level["attempts"] = []
    state = curriculum.normalize_curriculum_state(
        {
            "engine_version": curriculum.ENGINE_VERSION,
            "profile_version_id": profile["profile_version_id"],
            "status": "active",
            "phase": "chapter_check",
            "subject_id": "english",
            "target_class_no": 5,
            "active_learning_class_no": 5,
            "source_recap_session_id": None,
            "source_placement_report_id": "placement-report",
            "chapter": {
                key: value
                for key, value in chapter.items()
                if key not in {"levels", "chapter_assessment"}
            },
            "chapter_assessment": curriculum._new_chapter_assessment_state(
                chapter["chapter_assessment"]
            ),
            "completed_chapter_ids": [
                "eng_c5_ch01",
                "eng_c5_ch02",
                "eng_c5_ch03",
                "eng_c5_ch04",
            ],
            "completed_chapter_versions": {},
            "carry_forward_focuses": [],
            "current_level_index": len(levels) - 1,
            "levels": levels,
            "last_feedback": None,
        }
    )
    state = curriculum._begin_chapter_assessment(state)
    _run(
        store.upsert_school_session(
            session_id=session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=5,
            status="active",
            current_stage="chapter_check",
            linked_session_id=None,
            profile_version_id=profile["profile_version_id"],
            source_placement_report_id="placement-report",
            state_json=state,
        )
    )
    return state


def _replace_curriculum_source_report_same_profile(
    store,
    *,
    source_report_id: str,
) -> None:
    old_report = next(
        dict(row)
        for row in store.school_placement_reports.values()
        if str(row.get("report_id")) == str(source_report_id)
    )
    old_placement = _run(
        store.get_school_session("test_user", old_report["placement_session_id"])
    )
    new_placement_session_id = "same-profile-curriculum-new-placement"
    _run(
        store.upsert_school_session(
            **{
                **old_placement,
                "session_id": new_placement_session_id,
                "status": "active",
            }
        )
    )
    _run(
        store.upsert_school_session(
            **{
                **old_placement,
                "session_id": new_placement_session_id,
                "status": "complete",
            }
        )
    )
    _run(
        store.upsert_school_placement_report(
            **{
                **old_report,
                "report_id": "same-profile-curriculum-new-report",
                "placement_session_id": new_placement_session_id,
            }
        )
    )


def _drive_frog_chapter_check(
    body: dict[str, Any],
    client: TestClient,
    *,
    fail_first: bool,
) -> dict[str, Any]:
    answered = 0
    while body["phase"] == "chapter_check":
        activity = body["current_activity"]
        assert activity is not None
        answer = (
            "wrong"
            if fail_first and answered == 0
            else _correct_curriculum_answer(activity)
        )
        body = _answer(body, answer, client)
        answered += 1
        assert answered <= 13
    assert answered == 13
    return body


def _drive_frog_remediation(
    body: dict[str, Any],
    client: TestClient,
) -> dict[str, Any]:
    answered = 0
    while body["phase"] == "remediation":
        activity = body["current_activity"]
        assert activity is not None
        assert activity["kind"] in {"masterclass", "independent_check"}
        body = _answer(body, _correct_curriculum_answer(activity), client)
        assert body["last_feedback"]["correct"] is True, activity
        answered += 1
        assert answered <= 14
    assert answered >= 2
    return body


def test_curriculum_short_answer_requires_exact_match_not_substring():
    public_profile = {
        "target_class_no": 3,
        "subject_ids": ["english"],
    }
    state = curriculum.new_curriculum_state(
        school_profile=public_profile,
        placement_report=None,
        recap_session=None,
    )
    assert public_profile["target_class_no"] == 3
    state["current_level_index"] = 3
    for index, level in enumerate(state["levels"]):
        level["status"] = "in_progress" if index == 3 else "complete"
    state["levels"][3]["current_step"] = "bridge"

    updated, evaluation = curriculum.apply_curriculum_answer(
        state,
        activity_id="alphabetical_colour_order:bridge:1",
        answer="banana",
    )

    assert evaluation["correct"] is False
    assert updated["current_level_index"] == 3
    assert updated["levels"][3]["current_step"] == "masterclass"

    state["levels"][3]["attempts"] = []
    accepted, accepted_evaluation = curriculum.apply_curriculum_answer(
        state,
        activity_id="alphabetical_colour_order:bridge:1",
        answer="b",
    )

    assert accepted_evaluation["correct"] is True
    assert accepted["levels"][3]["current_step"] == "independent_check"


def test_curriculum_phrase_match_rejects_a_negated_expected_answer():
    assert curriculum._accepted_phrase_matches("not a rainbow", "rainbow") is False
    assert curriculum._accepted_phrase_matches("this is not past tense", "past tense") is False
    assert curriculum._accepted_phrase_matches(
        "i do not believe this is a rainbow",
        "rainbow",
    ) is False
    assert curriculum._accepted_phrase_matches("this is a rainbow not a boat", "rainbow") is True


def test_independent_failure_feedback_names_the_bridge_transition():
    assert curriculum._feedback_message(
        "independent_check",
        False,
        "bridge",
    ) == "Not yet. Zidd will slow this chapter level down with a bridge check."


def test_curriculum_starts_real_class_3_colours_chapter_after_recap(store):
    _seed_school_profile(store)
    client = TestClient(app)
    recap = _complete_recap_success_path(client)

    response = client.post("/school/curriculum/start", headers=AUTH)

    assert response.status_code == 200
    body = response.json()
    assert body["flow_type"] == "curriculum"
    assert body["status"] == "active"
    assert body["source_recap_session_id"] == recap["session_id"]
    assert body["chapter"]["chapter_id"] == "eng_c3_ch01"
    assert body["chapter"]["title"] == "Colours"
    assert body["chapter"]["book_title"] == "Santoor"
    assert body["chapter"]["unit_title"] == "Fun with Friends"
    assert body["progress"] == {
        "completed_levels": 0,
        "total_levels": 5,
        "current_level_index": 0,
    }
    assert body["carry_forward_focuses"]
    assert "write a complete sentence" in body["carry_forward_focuses"]
    assert body["current_activity"]["kind"] == "guided_check"
    assert body["current_activity"]["level_id"] == "colour_sharing_reason"
    assert "Santoor Chapter" not in body["current_activity"]["teaching_block"]
    assert "share" in body["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(body)

    active_profile = _run(store.get_active_school_profile_version("test_user"))
    saved = _run(store.get_school_session("test_user", body["session_id"]))
    assert saved["profile_version_id"] == active_profile["profile_version_id"]
    assert saved["source_placement_report_id"] == body["source_placement_report_id"]
    assert saved["linked_session_id"] == recap["session_id"]
    assert saved["state_json"]["profile_version_id"] == active_profile["profile_version_id"]

    _replace_curriculum_source_report_same_profile(
        store,
        source_report_id=body["source_placement_report_id"],
    )
    obsolete_get = client.get(
        f"/school/curriculum/{body['session_id']}", headers=AUTH
    )
    obsolete_answer = client.post(
        f"/school/curriculum/{body['session_id']}/answer",
        headers=AUTH,
        json={
            "activity_id": body["current_activity"]["activity_id"],
            "answer": "obsolete report answer",
        },
    )
    assert obsolete_get.status_code == 404
    assert obsolete_answer.status_code == 404

    replacement_payload = _profile_payload(target_class_no=3)
    replacement_payload["preferred_teaching_language"] = "en"
    replacement = _activate_school_profile(client, replacement_payload)
    assert replacement.status_code == 200
    old_get = client.get(f"/school/curriculum/{body['session_id']}", headers=AUTH)
    assert old_get.status_code == 404
    old_answer = client.post(
        f"/school/curriculum/{body['session_id']}/answer",
        headers=AUTH,
        json={
            "activity_id": body["current_activity"]["activity_id"],
            "answer": "old profile answer",
        },
    )
    assert old_answer.status_code == 404


def test_curriculum_get_refreshes_learning_memory_created_after_session_start(store):
    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    _complete_target_ready_placement(client)
    started = client.post("/school/curriculum/start", headers=AUTH).json()
    assert started["memory_summary"]["strong_skills"] == []

    _run(store.upsert_learner_skill_profile(
        user_id="test_user",
        domain="school",
        skill_id="reading.inference_reason",
        module_id="eng_c5_ch01",
        task_type="school_rebuild_curriculum",
        mastery=0.0,
        readiness=0.9,
        confidence=1.0,
        attempts=3,
        strengths_json=["explain a reason from passage evidence"],
        gaps_json=[],
        evidence_json={
            "latest_quote": "I used the passage clue to explain why he searched.",
            "attempt_type": "transfer_check",
            "chapter_id": "eng_c5_ch01",
            "level_id": "papas_spectacles_humour_and_reasons",
        },
        recommended_next_action="Continue with a new independent example.",
        source_summary="Strong transfer evidence in eng_c5_ch01.",
    ))

    refreshed = client.get(
        f"/school/curriculum/{started['session_id']}",
        headers=AUTH,
    )

    assert refreshed.status_code == 200
    assert refreshed.json()["memory_summary"]["strong_skills"] == [{
        "skill_id": "reading.inference_reason",
        "latest_evidence": "I used the passage clue to explain why he searched.",
        "last_attempt_type": "transfer_check",
        "last_chapter_id": "eng_c5_ch01",
        "attempts": 3,
    }]


def test_compatible_profile_edit_keeps_active_curriculum_and_historical_report_lineage(store):
    original_profile = _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    curriculum_body = client.post("/school/curriculum/start", headers=AUTH).json()

    report_before = _run(
        store.get_school_placement_report_by_id(
            "test_user",
            curriculum_body["source_placement_report_id"],
        )
    )
    assert report_before["profile_version_id"] == original_profile["profile_version_id"]

    compatible_payload = _profile_payload()
    compatible_payload["parent_goal"] = "Build a steady weekly reading habit."
    replacement = _activate_school_profile(client, compatible_payload)
    assert replacement.status_code == 200
    replacement_profile = replacement.json()["profile"]

    saved_curriculum = _run(
        store.get_school_session("test_user", curriculum_body["session_id"])
    )
    assert saved_curriculum["status"] == "active"
    assert saved_curriculum["profile_version_id"] == replacement_profile["profile_version_id"]
    assert (
        saved_curriculum["state_json"]["profile_version_id"]
        == replacement_profile["profile_version_id"]
    )

    report_after = _run(
        store.get_school_placement_report_by_id(
            "test_user",
            curriculum_body["source_placement_report_id"],
        )
    )
    assert report_after["profile_version_id"] == original_profile["profile_version_id"]

    state = client.get("/school/state", headers=AUTH)
    assert state.status_code == 200
    assert state.json()["active_session_id"] == curriculum_body["session_id"]
    assert state.json()["next_action"] == "resume_curriculum"

    resumed = client.get(
        f"/school/curriculum/{curriculum_body['session_id']}",
        headers=AUTH,
    )
    assert resumed.status_code == 200
    assert resumed.json()["session_id"] == curriculum_body["session_id"]


def test_curriculum_bridge_masterclass_and_independent_advance_are_tracked(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    body = client.post("/school/curriculum/start", headers=AUTH).json()
    session_id = body["session_id"]

    body = _answer(body, "wrong", client)
    assert body["current_activity"]["kind"] == "bridge"
    assert body["last_feedback"]["correct"] is False
    assert "slow this chapter level down" in body["last_feedback"]["message"].lower()
    _assert_no_hidden_keys(body)

    body = _answer(body, "wrong", client)
    assert body["current_activity"]["kind"] == "masterclass"
    assert "colour clue" in body["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(body)

    body = _answer(body, "share", client)
    assert body["current_activity"]["kind"] == "independent_check"
    assert "without hints" in body["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(body)

    body = _answer(body, "share", client)
    assert body["progress"]["completed_levels"] == 1
    assert body["current_activity"]["level_id"] == "colour_word_meaning"
    assert body["current_activity"]["kind"] == "guided_check"
    assert body["session_id"] == session_id
    _assert_no_hidden_keys(body)

    curriculum_events = [
        event
        for event in store.learning_events
        if event.get("task_type") == "school_rebuild_curriculum"
    ]
    assert len(curriculum_events) == 4
    assert curriculum_events[-1]["score"] == 1.0


def test_school_state_resumes_active_curriculum_session(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    started = client.post("/school/curriculum/start", headers=AUTH).json()

    state = client.get("/school/state", headers=AUTH).json()

    assert state["active_flow"] == "curriculum"
    assert state["active_session_id"] == started["session_id"]
    assert state["next_action"] == "resume_curriculum"
    assert state["next_action_url"] == f"/school/session/{started['session_id']}"


def test_completed_curriculum_session_opens_next_chapter(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    completed_first = _complete_current_curriculum_session(first, client)

    landing = client.get("/school/curriculum", headers=AUTH).json()

    assert completed_first["chapter"]["chapter_id"] == "eng_c3_ch01"
    first_preview, second_preview = landing["chapters_preview"][:2]
    assert first_preview["title"] == "Colours"
    assert first_preview["status"] == "complete"
    assert second_preview["title"] == "Badal and Moti"
    assert second_preview["status"] == "ready"
    assert "Start Chapter 2" in landing["source_note"]

    second = client.post("/school/curriculum/start", headers=AUTH)

    assert second.status_code == 200
    body = second.json()
    assert body["status"] == "active"
    assert body["chapter"]["chapter_id"] == "eng_c3_ch02"
    assert body["chapter"]["title"] == "Badal and Moti"
    assert body["chapter"]["book_title"] == "Santoor"
    assert body["progress"] == {
        "completed_levels": 0,
        "total_levels": 5,
        "current_level_index": 0,
    }
    assert body["current_activity"]["kind"] == "guided_check"
    assert "puppy" in body["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(body)


def test_completed_second_authored_chapter_opens_best_friends(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()

    assert second["chapter"]["chapter_id"] == "eng_c3_ch02"
    completed_second = _complete_current_curriculum_session(second, client)

    assert completed_second["status"] == "complete"
    assert completed_second["next_available_chapter"]["chapter_id"] == "eng_c3_ch03"
    assert completed_second["next_available_chapter"]["title"] == "Best Friends"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    third_preview = landing["chapters_preview"][2]
    assert third_preview["title"] == "Best Friends"
    assert third_preview["status"] == "ready"

    third_response = client.post("/school/curriculum/start", headers=AUTH)
    assert third_response.status_code == 200
    third = third_response.json()
    assert third["chapter"]["chapter_id"] == "eng_c3_ch03"
    assert third["chapter"]["title"] == "Best Friends"
    assert third["current_activity"]["level_id"] == "best_friends_team_reason"
    assert "shape" in third["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(third)


def test_completed_third_authored_chapter_opens_out_in_the_garden(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()

    assert third["chapter"]["chapter_id"] == "eng_c3_ch03"
    completed_third = _complete_current_curriculum_session(third, client)

    assert completed_third["status"] == "complete"
    assert completed_third["next_available_chapter"]["chapter_id"] == "eng_c3_ch04"
    assert completed_third["next_available_chapter"]["title"] == "Out in the Garden"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    fourth_preview = landing["chapters_preview"][3]
    assert fourth_preview["title"] == "Out in the Garden"
    assert fourth_preview["status"] == "ready"

    fourth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert fourth_response.status_code == 200
    fourth = fourth_response.json()
    assert fourth["chapter"]["chapter_id"] == "eng_c3_ch04"
    assert fourth["chapter"]["title"] == "Out in the Garden"
    assert fourth["chapter"]["unit_title"] == "Toys and Games"
    assert fourth["current_activity"]["level_id"] == "out_garden_picture_clues"
    assert "garden" in fourth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(fourth)


def test_completed_fourth_authored_chapter_opens_talking_toys(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert fourth["chapter"]["chapter_id"] == "eng_c3_ch04"
    completed_fourth = _complete_current_curriculum_session(fourth, client)

    assert completed_fourth["status"] == "complete"
    assert completed_fourth["next_available_chapter"]["chapter_id"] == "eng_c3_ch05"
    assert completed_fourth["next_available_chapter"]["title"] == "Talking Toys"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    fifth_preview = landing["chapters_preview"][4]
    assert fifth_preview["title"] == "Talking Toys"
    assert fifth_preview["status"] == "ready"

    fifth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert fifth_response.status_code == 200
    fifth = fifth_response.json()
    assert fifth["chapter"]["chapter_id"] == "eng_c3_ch05"
    assert fifth["chapter"]["title"] == "Talking Toys"
    assert fifth["chapter"]["unit_title"] == "Toys and Games"
    assert fifth["current_activity"]["level_id"] == "talking_toys_story_order"
    assert "toy" in fifth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(fifth)


def test_completed_fifth_authored_chapter_opens_paper_boats(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert fifth["chapter"]["chapter_id"] == "eng_c3_ch05"
    completed_fifth = _complete_current_curriculum_session(fifth, client)

    assert completed_fifth["status"] == "complete"
    assert completed_fifth["next_available_chapter"]["chapter_id"] == "eng_c3_ch06"
    assert completed_fifth["next_available_chapter"]["title"] == "Paper Boats"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    sixth_preview = landing["chapters_preview"][5]
    assert sixth_preview["title"] == "Paper Boats"
    assert sixth_preview["status"] == "ready"

    sixth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert sixth_response.status_code == 200
    sixth = sixth_response.json()
    assert sixth["chapter"]["chapter_id"] == "eng_c3_ch06"
    assert sixth["chapter"]["title"] == "Paper Boats"
    assert sixth["chapter"]["unit_title"] == "Toys and Games"
    assert sixth["current_activity"]["level_id"] == "paper_boats_story_setting"
    assert "paper boat" in sixth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(sixth)


def test_completed_sixth_authored_chapter_opens_the_big_laddoo(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert sixth["chapter"]["chapter_id"] == "eng_c3_ch06"
    completed_sixth = _complete_current_curriculum_session(sixth, client)

    assert completed_sixth["status"] == "complete"
    assert completed_sixth["next_available_chapter"]["chapter_id"] == "eng_c3_ch07"
    assert completed_sixth["next_available_chapter"]["title"] == "The Big Laddoo"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    seventh_preview = landing["chapters_preview"][6]
    assert seventh_preview["title"] == "The Big Laddoo"
    assert seventh_preview["status"] == "ready"

    seventh_response = client.post("/school/curriculum/start", headers=AUTH)
    assert seventh_response.status_code == 200
    seventh = seventh_response.json()
    assert seventh["chapter"]["chapter_id"] == "eng_c3_ch07"
    assert seventh["chapter"]["title"] == "The Big Laddoo"
    assert seventh["chapter"]["unit_title"] == "Good Food"
    assert seventh["current_activity"]["level_id"] == "big_laddoo_poem_image"
    assert "laddoo" in seventh["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(seventh)


def test_completed_seventh_authored_chapter_opens_thank_god(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()

    assert seventh["chapter"]["chapter_id"] == "eng_c3_ch07"
    completed_seventh = _complete_current_curriculum_session(seventh, client)

    assert completed_seventh["status"] == "complete"
    assert completed_seventh["next_available_chapter"]["chapter_id"] == "eng_c3_ch08"
    assert completed_seventh["next_available_chapter"]["title"] == "Thank God!"
    state = client.get("/school/state", headers=AUTH).json()
    assert state["next_action"] == "start_curriculum"
    assert state["allowed_next_actions"] == ["start_curriculum"]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    eighth_preview = landing["chapters_preview"][7]
    assert eighth_preview["title"] == "Thank God!"
    assert eighth_preview["status"] == "ready"

    eighth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert eighth_response.status_code == 200
    eighth = eighth_response.json()
    assert eighth["chapter"]["chapter_id"] == "eng_c3_ch08"
    assert eighth["chapter"]["title"] == "Thank God!"
    assert eighth["chapter"]["unit_title"] == "Good Food"
    assert eighth["current_activity"]["level_id"] == "thank_god_fruit_choice"
    assert "grapes" in eighth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(eighth)


def test_completed_last_authored_chapter_hides_next_chapter(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(ninth, client)
    tenth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(tenth, client)
    eleventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eleventh, client)
    twelfth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert twelfth["chapter"]["chapter_id"] == "eng_c3_ch12"
    completed_twelfth = _complete_current_curriculum_session(twelfth, client)

    assert completed_twelfth["status"] == "complete"
    assert completed_twelfth["next_available_chapter"] is None
    _assert_no_hidden_keys(completed_twelfth)

    state = client.get("/school/state", headers=AUTH).json()
    assert state["status"] == "complete"
    assert state["active_flow"] == "curriculum"
    assert state["active_session_id"] == completed_twelfth["session_id"]
    assert state["next_action"] == "view_report"
    assert state["next_action_url"] == "/school/curriculum"
    assert state["allowed_next_actions"] == ["view_report"]

    next_response = client.post("/school/curriculum/start", headers=AUTH)

    assert next_response.status_code == 409
    assert next_response.json()["detail"]["code"] == "all_curriculum_chapters_complete"


def test_completed_eighth_authored_chapter_opens_madhu_wish(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert eighth["chapter"]["chapter_id"] == "eng_c3_ch08"
    completed_eighth = _complete_current_curriculum_session(eighth, client)

    assert completed_eighth["status"] == "complete"
    assert completed_eighth["next_available_chapter"]["chapter_id"] == "eng_c3_ch09"
    assert completed_eighth["next_available_chapter"]["title"] == "Madhu's Wish"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    ninth_preview = landing["chapters_preview"][8]
    assert ninth_preview["title"] == "Madhu's Wish"
    assert ninth_preview["status"] == "ready"

    ninth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert ninth_response.status_code == 200
    ninth = ninth_response.json()
    assert ninth["chapter"]["chapter_id"] == "eng_c3_ch09"
    assert ninth["chapter"]["title"] == "Madhu's Wish"
    assert ninth["chapter"]["unit_title"] == "Good Food"
    assert ninth["current_activity"]["level_id"] == "madhu_wish_kind_action"
    assert "shared" in ninth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(ninth)


def test_completed_ninth_authored_chapter_opens_night(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert ninth["chapter"]["chapter_id"] == "eng_c3_ch09"
    completed_ninth = _complete_current_curriculum_session(ninth, client)

    assert completed_ninth["status"] == "complete"
    assert completed_ninth["next_available_chapter"]["chapter_id"] == "eng_c3_ch10"
    assert completed_ninth["next_available_chapter"]["title"] == "Night"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    tenth_preview = landing["chapters_preview"][9]
    assert tenth_preview["title"] == "Night"
    assert tenth_preview["status"] == "ready"

    tenth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert tenth_response.status_code == 200
    tenth = tenth_response.json()
    assert tenth["chapter"]["chapter_id"] == "eng_c3_ch10"
    assert tenth["chapter"]["title"] == "Night"
    assert tenth["chapter"]["unit_title"] == "The Sky"
    assert tenth["current_activity"]["level_id"] == "night_poem_mood"
    assert "dark" in tenth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(tenth)


def test_completed_tenth_authored_chapter_opens_chanda_mama(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(ninth, client)
    tenth = client.post("/school/curriculum/start", headers=AUTH).json()

    assert tenth["chapter"]["chapter_id"] == "eng_c3_ch10"
    completed_tenth = _complete_current_curriculum_session(tenth, client)

    assert completed_tenth["status"] == "complete"
    assert completed_tenth["next_available_chapter"]["chapter_id"] == "eng_c3_ch11"
    assert completed_tenth["next_available_chapter"]["title"] == "Chanda Mama Counts the Stars"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    eleventh_preview = landing["chapters_preview"][10]
    assert eleventh_preview["title"] == "Chanda Mama Counts the Stars"
    assert eleventh_preview["status"] == "ready"

    eleventh_response = client.post("/school/curriculum/start", headers=AUTH)
    assert eleventh_response.status_code == 200
    eleventh = eleventh_response.json()
    assert eleventh["chapter"]["chapter_id"] == "eng_c3_ch11"
    assert eleventh["chapter"]["title"] == "Chanda Mama Counts the Stars"
    assert eleventh["chapter"]["unit_title"] == "The Sky"
    assert eleventh["current_activity"]["level_id"] == "chanda_mama_moon_shape"
    assert "moon" in eleventh["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(eleventh)


def test_completed_eleventh_authored_chapter_opens_chandrayaan(store):
    _seed_school_profile(store)
    client = TestClient(app)
    _complete_recap_success_path(client)
    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(ninth, client)
    tenth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(tenth, client)
    eleventh = client.post("/school/curriculum/start", headers=AUTH).json()

    assert eleventh["chapter"]["chapter_id"] == "eng_c3_ch11"
    completed_eleventh = _complete_current_curriculum_session(eleventh, client)

    assert completed_eleventh["status"] == "complete"
    assert completed_eleventh["next_available_chapter"]["chapter_id"] == "eng_c3_ch12"
    assert completed_eleventh["next_available_chapter"]["title"] == "Chandrayaan"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    twelfth_preview = landing["chapters_preview"][11]
    assert twelfth_preview["title"] == "Chandrayaan"
    assert twelfth_preview["status"] == "ready"

    twelfth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert twelfth_response.status_code == 200
    twelfth = twelfth_response.json()
    assert twelfth["chapter"]["chapter_id"] == "eng_c3_ch12"
    assert twelfth["chapter"]["title"] == "Chandrayaan"
    assert twelfth["chapter"]["unit_title"] == "The Sky"
    assert twelfth["current_activity"]["level_id"] == "chandrayaan_rani_questions"
    assert "curious" in twelfth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(twelfth)


def test_class_four_target_ready_placement_opens_together_we_can_curriculum(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    report = _complete_target_ready_placement(client)

    landing_response = client.get("/school/curriculum", headers=AUTH)

    assert landing_response.status_code == 200
    landing = landing_response.json()
    assert landing["target_class_no"] == 4
    assert landing["source_placement_report_id"] == report["report_id"]
    assert landing["chapters_preview"][0]["chapter_id"] == "eng_c4_ch01"
    assert landing["chapters_preview"][0]["title"] == "Together We Can"
    assert landing["chapters_preview"][0]["status"] == "ready"

    started_response = client.post("/school/curriculum/start", headers=AUTH)
    assert started_response.status_code == 200
    started = started_response.json()
    assert started["chapter"]["chapter_id"] == "eng_c4_ch01"
    assert started["chapter"]["title"] == "Together We Can"
    assert started["chapter"]["unit_title"] == "My Land"
    assert started["current_activity"]["level_id"] == "together_we_can_teamwork"
    assert "teamwork" in started["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(started)


def test_completed_class_four_first_chapter_opens_tinkling_bells(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    assert first["chapter"]["chapter_id"] == "eng_c4_ch01"
    completed_first = _complete_current_curriculum_session(first, client)

    assert completed_first["status"] == "complete"
    assert completed_first["next_available_chapter"]["chapter_id"] == "eng_c4_ch02"
    assert completed_first["next_available_chapter"]["title"] == "The Tinkling Bells"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    second_preview = landing["chapters_preview"][1]
    assert second_preview["chapter_id"] == "eng_c4_ch02"
    assert second_preview["title"] == "The Tinkling Bells"
    assert second_preview["status"] == "ready"

    second_response = client.post("/school/curriculum/start", headers=AUTH)
    assert second_response.status_code == 200
    second = second_response.json()
    assert second["chapter"]["chapter_id"] == "eng_c4_ch02"
    assert second["chapter"]["title"] == "The Tinkling Bells"
    assert second["chapter"]["unit_title"] == "My Land"
    assert second["current_activity"]["level_id"] == "tinkling_bells_honesty_choice"
    assert "honest" in second["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(second)


def test_completed_class_four_second_chapter_opens_be_smart_be_safe(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    assert second["chapter"]["chapter_id"] == "eng_c4_ch02"
    completed_second = _complete_current_curriculum_session(second, client)

    assert completed_second["status"] == "complete"
    assert completed_second["next_available_chapter"]["chapter_id"] == "eng_c4_ch03"
    assert completed_second["next_available_chapter"]["title"] == "Be Smart, Be Safe"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    third_preview = landing["chapters_preview"][2]
    assert third_preview["chapter_id"] == "eng_c4_ch03"
    assert third_preview["title"] == "Be Smart, Be Safe"
    assert third_preview["status"] == "ready"

    third_response = client.post("/school/curriculum/start", headers=AUTH)
    assert third_response.status_code == 200
    third = third_response.json()
    assert third["chapter"]["chapter_id"] == "eng_c4_ch03"
    assert third["chapter"]["title"] == "Be Smart, Be Safe"
    assert third["chapter"]["unit_title"] == "My Land"
    assert third["current_activity"]["level_id"] == "be_safe_crossing_steps"
    assert "road" in third["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(third)


def test_completed_class_four_third_chapter_opens_one_thing_at_a_time(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    assert third["chapter"]["chapter_id"] == "eng_c4_ch03"
    completed_third = _complete_current_curriculum_session(third, client)

    assert completed_third["status"] == "complete"
    assert completed_third["next_available_chapter"]["chapter_id"] == "eng_c4_ch04"
    assert completed_third["next_available_chapter"]["title"] == "One Thing at a Time"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    fourth_preview = landing["chapters_preview"][3]
    assert fourth_preview["chapter_id"] == "eng_c4_ch04"
    assert fourth_preview["title"] == "One Thing at a Time"
    assert fourth_preview["status"] == "ready"

    fourth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert fourth_response.status_code == 200
    fourth = fourth_response.json()
    assert fourth["chapter"]["chapter_id"] == "eng_c4_ch04"
    assert fourth["chapter"]["title"] == "One Thing at a Time"
    assert fourth["chapter"]["unit_title"] == "My Beautiful World"
    assert fourth["current_activity"]["level_id"] == "one_thing_focus_message"
    assert "focus" in fourth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(fourth)


def test_completed_class_four_fourth_chapter_opens_the_old_stag(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert fourth["chapter"]["chapter_id"] == "eng_c4_ch04"
    completed_fourth = _complete_current_curriculum_session(fourth, client)

    assert completed_fourth["status"] == "complete"
    assert completed_fourth["next_available_chapter"]["chapter_id"] == "eng_c4_ch05"
    assert completed_fourth["next_available_chapter"]["title"] == "The Old Stag"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    fifth_preview = landing["chapters_preview"][4]
    assert fifth_preview["chapter_id"] == "eng_c4_ch05"
    assert fifth_preview["title"] == "The Old Stag"
    assert fifth_preview["status"] == "ready"

    fifth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert fifth_response.status_code == 200
    fifth = fifth_response.json()
    assert fifth["chapter"]["chapter_id"] == "eng_c4_ch05"
    assert fifth["chapter"]["title"] == "The Old Stag"
    assert fifth["chapter"]["unit_title"] == "My Beautiful World"
    assert fifth["current_activity"]["level_id"] == "old_stag_kindness_reason"
    assert "kind" in fifth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(fifth)


def test_completed_class_four_fifth_chapter_opens_braille(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert fifth["chapter"]["chapter_id"] == "eng_c4_ch05"
    completed_fifth = _complete_current_curriculum_session(fifth, client)

    assert completed_fifth["status"] == "complete"
    assert completed_fifth["next_available_chapter"]["chapter_id"] == "eng_c4_ch06"
    assert completed_fifth["next_available_chapter"]["title"] == "Braille"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["chapter_id"] == "eng_c4_ch06"
    assert landing["chapters_preview"][5]["title"] == "Braille"
    assert landing["chapters_preview"][5]["status"] == "ready"

    sixth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert sixth_response.status_code == 200
    sixth = sixth_response.json()
    assert sixth["chapter"]["chapter_id"] == "eng_c4_ch06"
    assert sixth["chapter"]["title"] == "Braille"
    assert sixth["chapter"]["unit_title"] == "My Beautiful World"
    assert sixth["current_activity"]["level_id"] == "braille_touch_reading"
    assert "touch" in sixth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(sixth)


def test_completed_class_four_sixth_chapter_opens_fit_body(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert sixth["chapter"]["chapter_id"] == "eng_c4_ch06"
    completed_sixth = _complete_current_curriculum_session(sixth, client)

    assert completed_sixth["status"] == "complete"
    assert completed_sixth["next_available_chapter"]["chapter_id"] == "eng_c4_ch07"
    assert completed_sixth["next_available_chapter"]["title"] == "Fit Body, Fit Mind, Fit Nation"

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["status"] == "complete"
    assert landing["chapters_preview"][6]["chapter_id"] == "eng_c4_ch07"
    assert landing["chapters_preview"][6]["title"] == "Fit Body, Fit Mind, Fit Nation"
    assert landing["chapters_preview"][6]["status"] == "ready"

    seventh_response = client.post("/school/curriculum/start", headers=AUTH)
    assert seventh_response.status_code == 200
    seventh = seventh_response.json()
    assert seventh["chapter"]["chapter_id"] == "eng_c4_ch07"
    assert seventh["chapter"]["title"] == "Fit Body, Fit Mind, Fit Nation"
    assert seventh["chapter"]["unit_title"] == "Fun with Games"
    assert seventh["current_activity"]["level_id"] == "fit_body_activity_clues"
    assert "active" in seventh["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(seventh)


def test_completed_class_four_seventh_chapter_opens_lagori_champions(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    assert seventh["chapter"]["chapter_id"] == "eng_c4_ch07"
    completed_seventh = _complete_current_curriculum_session(seventh, client)

    assert completed_seventh["status"] == "complete"
    assert completed_seventh["next_available_chapter"]["chapter_id"] == "eng_c4_ch08"
    assert completed_seventh["next_available_chapter"]["title"] == "The Lagori Champions"
    assert completed_seventh["completed_chapter_ids"] == [
        "eng_c4_ch01",
        "eng_c4_ch02",
        "eng_c4_ch03",
        "eng_c4_ch04",
        "eng_c4_ch05",
        "eng_c4_ch06",
        "eng_c4_ch07",
    ]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["status"] == "complete"
    assert landing["chapters_preview"][6]["status"] == "complete"
    assert landing["chapters_preview"][7]["chapter_id"] == "eng_c4_ch08"
    assert landing["chapters_preview"][7]["title"] == "The Lagori Champions"
    assert landing["chapters_preview"][7]["status"] == "ready"

    eighth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert eighth_response.status_code == 200
    eighth = eighth_response.json()
    assert eighth["chapter"]["chapter_id"] == "eng_c4_ch08"
    assert eighth["chapter"]["title"] == "The Lagori Champions"
    assert eighth["chapter"]["unit_title"] == "Fun with Games"
    assert eighth["current_activity"]["level_id"] == "lagori_rules_comprehension"
    assert "traditional game" in eighth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(eighth)


def test_completed_class_four_eighth_chapter_opens_hekko(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert eighth["chapter"]["chapter_id"] == "eng_c4_ch08"
    completed_eighth = _complete_current_curriculum_session(eighth, client)

    assert completed_eighth["status"] == "complete"
    assert completed_eighth["next_available_chapter"]["chapter_id"] == "eng_c4_ch09"
    assert completed_eighth["next_available_chapter"]["title"] == "Hekko"
    assert completed_eighth["completed_chapter_ids"] == [
        "eng_c4_ch01",
        "eng_c4_ch02",
        "eng_c4_ch03",
        "eng_c4_ch04",
        "eng_c4_ch05",
        "eng_c4_ch06",
        "eng_c4_ch07",
        "eng_c4_ch08",
    ]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["status"] == "complete"
    assert landing["chapters_preview"][6]["status"] == "complete"
    assert landing["chapters_preview"][7]["status"] == "complete"
    assert landing["chapters_preview"][8]["chapter_id"] == "eng_c4_ch09"
    assert landing["chapters_preview"][8]["title"] == "Hekko"
    assert landing["chapters_preview"][8]["status"] == "ready"

    ninth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert ninth_response.status_code == 200
    ninth = ninth_response.json()
    assert ninth["chapter"]["chapter_id"] == "eng_c4_ch09"
    assert ninth["chapter"]["title"] == "Hekko"
    assert ninth["chapter"]["unit_title"] == "Fun with Games"
    assert ninth["current_activity"]["level_id"] == "hekko_word_meaning"
    assert "challenge" in ninth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(ninth)


def test_completed_class_four_ninth_chapter_opens_the_swing(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert ninth["chapter"]["chapter_id"] == "eng_c4_ch09"
    completed_ninth = _complete_current_curriculum_session(ninth, client)

    assert completed_ninth["status"] == "complete"
    assert completed_ninth["next_available_chapter"]["chapter_id"] == "eng_c4_ch10"
    assert completed_ninth["next_available_chapter"]["title"] == "The Swing"
    assert completed_ninth["completed_chapter_ids"] == [
        "eng_c4_ch01",
        "eng_c4_ch02",
        "eng_c4_ch03",
        "eng_c4_ch04",
        "eng_c4_ch05",
        "eng_c4_ch06",
        "eng_c4_ch07",
        "eng_c4_ch08",
        "eng_c4_ch09",
    ]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["status"] == "complete"
    assert landing["chapters_preview"][6]["status"] == "complete"
    assert landing["chapters_preview"][7]["status"] == "complete"
    assert landing["chapters_preview"][8]["status"] == "complete"
    assert landing["chapters_preview"][9]["chapter_id"] == "eng_c4_ch10"
    assert landing["chapters_preview"][9]["title"] == "The Swing"
    assert landing["chapters_preview"][9]["status"] == "ready"

    tenth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert tenth_response.status_code == 200
    tenth = tenth_response.json()
    assert tenth["chapter"]["chapter_id"] == "eng_c4_ch10"
    assert tenth["chapter"]["title"] == "The Swing"
    assert tenth["chapter"]["unit_title"] == "Up High"
    assert tenth["current_activity"]["level_id"] == "swing_view_clues"
    assert "view" in tenth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(tenth)


def test_completed_class_four_tenth_chapter_opens_magical_mountains(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(ninth, client)
    tenth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert tenth["chapter"]["chapter_id"] == "eng_c4_ch10"
    completed_tenth = _complete_current_curriculum_session(tenth, client)

    assert completed_tenth["status"] == "complete"
    assert completed_tenth["next_available_chapter"]["chapter_id"] == "eng_c4_ch11"
    assert completed_tenth["next_available_chapter"]["title"] == "A Journey to the Magical Mountains"
    assert completed_tenth["completed_chapter_ids"] == [
        "eng_c4_ch01",
        "eng_c4_ch02",
        "eng_c4_ch03",
        "eng_c4_ch04",
        "eng_c4_ch05",
        "eng_c4_ch06",
        "eng_c4_ch07",
        "eng_c4_ch08",
        "eng_c4_ch09",
        "eng_c4_ch10",
    ]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["status"] == "complete"
    assert landing["chapters_preview"][6]["status"] == "complete"
    assert landing["chapters_preview"][7]["status"] == "complete"
    assert landing["chapters_preview"][8]["status"] == "complete"
    assert landing["chapters_preview"][9]["status"] == "complete"
    assert landing["chapters_preview"][10]["chapter_id"] == "eng_c4_ch11"
    assert landing["chapters_preview"][10]["title"] == "A Journey to the Magical Mountains"
    assert landing["chapters_preview"][10]["status"] == "ready"

    eleventh_response = client.post("/school/curriculum/start", headers=AUTH)
    assert eleventh_response.status_code == 200
    eleventh = eleventh_response.json()
    assert eleventh["chapter"]["chapter_id"] == "eng_c4_ch11"
    assert eleventh["chapter"]["title"] == "A Journey to the Magical Mountains"
    assert eleventh["chapter"]["unit_title"] == "Up High"
    assert eleventh["current_activity"]["level_id"] == "mountain_story_sequence"
    assert "journey" in eleventh["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(eleventh)


def test_completed_class_four_eleventh_chapter_opens_maheshwar(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(ninth, client)
    tenth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(tenth, client)
    eleventh = client.post("/school/curriculum/start", headers=AUTH).json()
    assert eleventh["chapter"]["chapter_id"] == "eng_c4_ch11"
    completed_eleventh = _complete_current_curriculum_session(eleventh, client)

    assert completed_eleventh["status"] == "complete"
    assert completed_eleventh["next_available_chapter"]["chapter_id"] == "eng_c4_ch12"
    assert completed_eleventh["next_available_chapter"]["title"] == "Maheshwar"
    assert completed_eleventh["completed_chapter_ids"] == [
        "eng_c4_ch01",
        "eng_c4_ch02",
        "eng_c4_ch03",
        "eng_c4_ch04",
        "eng_c4_ch05",
        "eng_c4_ch06",
        "eng_c4_ch07",
        "eng_c4_ch08",
        "eng_c4_ch09",
        "eng_c4_ch10",
        "eng_c4_ch11",
    ]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["source_note"] == "Target class is unlocked. Start Chapter 12 when you are ready."
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["chapters_preview"][5]["status"] == "complete"
    assert landing["chapters_preview"][6]["status"] == "complete"
    assert landing["chapters_preview"][7]["status"] == "complete"
    assert landing["chapters_preview"][8]["status"] == "complete"
    assert landing["chapters_preview"][9]["status"] == "complete"
    assert landing["chapters_preview"][10]["status"] == "complete"
    assert landing["chapters_preview"][11]["chapter_id"] == "eng_c4_ch12"
    assert landing["chapters_preview"][11]["title"] == "Maheshwar"
    assert landing["chapters_preview"][11]["status"] == "ready"

    twelfth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert twelfth_response.status_code == 200
    twelfth = twelfth_response.json()
    assert twelfth["chapter"]["chapter_id"] == "eng_c4_ch12"
    assert twelfth["chapter"]["title"] == "Maheshwar"
    assert twelfth["chapter"]["unit_title"] == "Up High"
    assert twelfth["current_activity"]["level_id"] == "maheshwar_dialogue_facts"
    assert "dialogue" in twelfth["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(twelfth)


def test_class_four_twelfth_chapter_completion_finishes_authored_class(store):
    _seed_school_profile(store, target_class_no=4)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(third, client)
    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fourth, client)
    fifth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(fifth, client)
    sixth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(sixth, client)
    seventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(seventh, client)
    eighth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eighth, client)
    ninth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(ninth, client)
    tenth = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(tenth, client)
    eleventh = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(eleventh, client)
    twelfth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert twelfth["chapter"]["chapter_id"] == "eng_c4_ch12"
    completed_twelfth = _complete_current_curriculum_session(twelfth, client)

    assert completed_twelfth["status"] == "complete"
    assert completed_twelfth["next_available_chapter"] is None
    assert completed_twelfth["completed_chapter_ids"] == [
        "eng_c4_ch01",
        "eng_c4_ch02",
        "eng_c4_ch03",
        "eng_c4_ch04",
        "eng_c4_ch05",
        "eng_c4_ch06",
        "eng_c4_ch07",
        "eng_c4_ch08",
        "eng_c4_ch09",
        "eng_c4_ch10",
        "eng_c4_ch11",
        "eng_c4_ch12",
    ]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["source_note"] == "All available target-class chapters are complete."
    for chapter in landing["chapters_preview"]:
        assert chapter["status"] == "complete"


def test_class_five_target_ready_placement_opens_papas_spectacles(store):
    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["target_class_no"] == 5
    assert landing["book_title"] == "Santoor"
    assert landing["source_note"] == "Target class is unlocked. Start Chapter 1 when you are ready."
    assert landing["chapters_preview"][0]["chapter_id"] == "eng_c5_ch01"
    assert landing["chapters_preview"][0]["title"] == "Papa's Spectacles"
    assert landing["chapters_preview"][0]["status"] == "ready"
    assert landing["chapters_preview"][1]["chapter_id"] == "eng_c5_ch02"
    assert landing["chapters_preview"][1]["status"] == "locked_next"

    response = client.post("/school/curriculum/start", headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    assert body["chapter"]["chapter_id"] == "eng_c5_ch01"
    assert body["chapter"]["title"] == "Papa's Spectacles"
    assert body["chapter"]["unit_title"] == "Let's Have Fun"
    assert body["current_activity"]["level_id"] == "papas_spectacles_story_details"
    assert "story detail" in body["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(body)


def test_class_five_completed_first_chapter_opens_gone_with_the_scooter(store):
    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    assert first["chapter"]["chapter_id"] == "eng_c5_ch01"
    completed = _complete_current_curriculum_session(first, client)

    assert completed["status"] == "complete"
    assert completed["next_available_chapter"]["chapter_id"] == "eng_c5_ch02"
    assert completed["next_available_chapter"]["title"] == "Gone with the Scooter"
    assert completed["completed_chapter_ids"] == ["eng_c5_ch01"]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["source_note"] == "Target class is unlocked. Start Chapter 2 when you are ready."
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["chapter_id"] == "eng_c5_ch02"
    assert landing["chapters_preview"][1]["title"] == "Gone with the Scooter"
    assert landing["chapters_preview"][1]["status"] == "ready"

    second_response = client.post("/school/curriculum/start", headers=AUTH)
    assert second_response.status_code == 200
    second = second_response.json()
    assert second["chapter"]["chapter_id"] == "eng_c5_ch02"
    assert second["chapter"]["title"] == "Gone with the Scooter"
    assert second["chapter"]["unit_title"] == "Let's Have Fun"
    assert second["current_activity"]["level_id"] == "gone_scooter_story_sequence"
    assert "sequence" in second["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(second)


def test_class_five_second_chapter_completion_opens_the_rainbow(store):
    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    assert second["chapter"]["chapter_id"] == "eng_c5_ch02"
    completed = _complete_current_curriculum_session(second, client)

    assert completed["status"] == "complete"
    assert completed["next_available_chapter"]["chapter_id"] == "eng_c5_ch03"
    assert completed["next_available_chapter"]["title"] == "The Rainbow"
    assert completed["completed_chapter_ids"] == ["eng_c5_ch01", "eng_c5_ch02"]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["source_note"] == "Target class is unlocked. Start Chapter 3 when you are ready."
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["chapter_id"] == "eng_c5_ch03"
    assert landing["chapters_preview"][2]["title"] == "The Rainbow"
    assert landing["chapters_preview"][2]["status"] == "ready"

    third_response = client.post("/school/curriculum/start", headers=AUTH)
    assert third_response.status_code == 200
    third = third_response.json()
    assert third["chapter"]["chapter_id"] == "eng_c5_ch03"
    assert third["chapter"]["title"] == "The Rainbow"
    assert third["chapter"]["unit_title"] == "My Colourful World"
    assert third["current_activity"]["level_id"] == "rainbow_image_bridge"
    assert "image" in third["current_activity"]["teaching_block"].lower()
    _assert_no_hidden_keys(third)


def test_class_five_third_chapter_completion_opens_the_wise_parrot(store):
    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    first = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(first, client)
    second = client.post("/school/curriculum/start", headers=AUTH).json()
    _complete_current_curriculum_session(second, client)
    third = client.post("/school/curriculum/start", headers=AUTH).json()
    assert third["chapter"]["chapter_id"] == "eng_c5_ch03"
    completed = _complete_current_curriculum_session(third, client)

    assert completed["status"] == "complete"
    assert completed["next_available_chapter"]["chapter_id"] == "eng_c5_ch04"
    assert completed["next_available_chapter"]["title"] == "The Wise Parrot"
    assert completed["completed_chapter_ids"] == ["eng_c5_ch01", "eng_c5_ch02", "eng_c5_ch03"]

    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["source_note"] == "Target class is unlocked. Start Chapter 4 when you are ready."
    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "complete"
    assert landing["chapters_preview"][3]["chapter_id"] == "eng_c5_ch04"
    assert landing["chapters_preview"][3]["title"] == "The Wise Parrot"
    assert landing["chapters_preview"][3]["status"] == "ready"

    fourth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert fourth_response.status_code == 200
    fourth = fourth_response.json()
    assert fourth["chapter"]["chapter_id"] == "eng_c5_ch04"
    assert fourth["chapter"]["title"] == "The Wise Parrot"
    assert fourth["chapter"]["unit_title"] == "My Colourful World"
    assert fourth["current_activity"]["level_id"] == "wise_parrot_story_sequence"
    _assert_no_hidden_keys(fourth)


def test_class_five_fourth_chapter_completion_opens_and_completes_the_frog(store):
    _seed_school_profile(store, target_class_no=5)
    client = TestClient(app)
    _complete_target_ready_placement(client)

    for expected_chapter_id in ("eng_c5_ch01", "eng_c5_ch02", "eng_c5_ch03"):
        body = client.post("/school/curriculum/start", headers=AUTH).json()
        assert body["chapter"]["chapter_id"] == expected_chapter_id
        _complete_current_curriculum_session(body, client)

    fourth = client.post("/school/curriculum/start", headers=AUTH).json()
    assert fourth["chapter"]["chapter_id"] == "eng_c5_ch04"
    completed = _complete_current_curriculum_session(fourth, client)

    assert completed["status"] == "complete"
    assert completed["next_available_chapter"]["chapter_id"] == "eng_c5_ch05"
    assert completed["next_available_chapter"]["title"] == "The Frog"
    assert completed["completed_chapter_ids"] == [
        "eng_c5_ch01",
        "eng_c5_ch02",
        "eng_c5_ch03",
        "eng_c5_ch04",
    ]
    landing = client.get("/school/curriculum", headers=AUTH).json()
    assert landing["chapters_preview"][3]["status"] == "complete"
    assert landing["chapters_preview"][4]["chapter_id"] == "eng_c5_ch05"
    assert landing["chapters_preview"][4]["title"] == "The Frog"
    assert landing["chapters_preview"][4]["status"] == "ready"

    fifth_response = client.post("/school/curriculum/start", headers=AUTH)
    assert fifth_response.status_code == 200
    fifth = fifth_response.json()
    assert fifth["chapter"]["chapter_id"] == "eng_c5_ch05"
    assert fifth["chapter"]["title"] == "The Frog"
    assert fifth["chapter"]["unit_title"] == "Water"
    assert fifth["current_activity"]["level_id"] == "frog_between_two_homes"
    _assert_no_hidden_keys(fifth)

    completed_fifth = _complete_current_curriculum_session(fifth, client)

    assert completed_fifth["status"] == "complete"
    assert completed_fifth["phase"] == "complete"
    assert completed_fifth["chapter_assessment"]["status"] == "passed"
    assert completed_fifth["chapter_assessment"]["last_result"]["passed"] is True
    assert completed_fifth["next_available_chapter"] is None
    assert completed_fifth["completed_chapter_ids"] == [
        "eng_c5_ch01",
        "eng_c5_ch02",
        "eng_c5_ch03",
        "eng_c5_ch04",
        "eng_c5_ch05",
    ]
    _assert_no_hidden_keys(completed_fifth)


def test_frog_chapter_check_failure_runs_remediation_then_alternate_form(store):
    session_id = str(uuid4())
    initial = _seed_frog_chapter_check_session(store, session_id=session_id)
    first_form_ids = set(initial["chapter_assessment"]["selected_item_ids"])
    client = TestClient(app)
    response = client.get(f"/school/curriculum/{session_id}", headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    _assert_no_hidden_keys(body)

    body = _drive_frog_chapter_check(body, client, fail_first=True)

    assert body["phase"] == "remediation"
    assert body["chapter_assessment"]["status"] == "remediation"
    assert body["chapter_assessment"]["last_result"]["passed"] is False
    row = _run(store.get_school_session("test_user", session_id))
    assert row["state_json"]["chapter_assessment"]["attempt_history"][-1][
        "remediation_skill_ids"
    ]
    assert body["current_activity"]["kind"] == "masterclass"
    _assert_no_hidden_keys(body)

    body = _drive_frog_remediation(body, client)

    assert body["phase"] == "chapter_check"
    assert body["chapter_assessment"]["attempt_no"] == 2
    row = _run(store.get_school_session("test_user", session_id))
    second_form_ids = set(row["state_json"]["chapter_assessment"]["selected_item_ids"])
    assert first_form_ids.isdisjoint(second_form_ids)

    completed = _drive_frog_chapter_check(body, client, fail_first=False)

    assert completed["status"] == "complete", completed["chapter_assessment"]["last_result"]
    assert completed["phase"] == "complete"
    assert completed["chapter_assessment"]["status"] == "passed"
    assert completed["chapter_assessment"]["last_result"]["passed"] is True
    assert "eng_c5_ch05" in completed["completed_chapter_ids"]
    _assert_no_hidden_keys(completed)


def test_frog_second_failed_chapter_check_enters_needs_support_without_unlock(store):
    session_id = str(uuid4())
    _seed_frog_chapter_check_session(store, session_id=session_id)
    client = TestClient(app)
    body = client.get(f"/school/curriculum/{session_id}", headers=AUTH).json()

    body = _drive_frog_chapter_check(body, client, fail_first=True)
    body = _drive_frog_remediation(body, client)
    body = _drive_frog_chapter_check(body, client, fail_first=True)

    assert body["status"] == "active"
    assert body["phase"] == "needs_support"
    assert body["current_activity"] is None
    assert body["chapter_assessment"]["status"] == "needs_support"
    assert body["chapter_assessment"]["last_result"]["passed"] is False
    row = _run(store.get_school_session("test_user", session_id))
    assert row["state_json"]["chapter_assessment"]["attempt_history"][-1][
        "remediation_skill_ids"
    ]
    assert "eng_c5_ch05" not in body["completed_chapter_ids"]
    assert body["next_available_chapter"] is None
    _assert_no_hidden_keys(body)


def test_wise_parrot_chapter_covers_the_full_core_learning_surface():
    levels = {
        level["level_id"]: level
        for level in curriculum.CLASS_5_WISE_PARROT_CHAPTER["levels"]
    }
    required_level_ids = {
        "wise_parrot_story_sequence",
        "wise_parrot_freedom_reason",
        "wise_parrot_words_phrases",
        "wise_parrot_collective_nouns",
        "wise_parrot_present_perfect",
        "wise_parrot_bird_sanctuary",
        "wise_parrot_ai_oi_sounds",
        "wise_parrot_opinion_reason",
        "wise_parrot_story_continuation",
        "wise_parrot_bird_feeder_steps",
    }
    assert required_level_ids <= set(levels)

    continuation_check = levels["wise_parrot_story_continuation"]["checks"]["independent_check"]
    assert continuation_check["response_mode"] == "paragraph"
    assert continuation_check["evaluation_mode"] == "llm_rubric"
    assert continuation_check["pass_score"] == 0.75
    assert 60 <= len(WISE_PARROT_STORY_CONTINUATION.split()) <= 90
    assert curriculum._open_answer_preflight(
        continuation_check,
        WISE_PARROT_STORY_CONTINUATION,
    ) is True
    assert curriculum._open_answer_preflight(continuation_check, "The parrot flew away.") is False

    opinion_check = levels["wise_parrot_opinion_reason"]["checks"]["independent_check"]
    assert curriculum._answer_matches(
        opinion_check,
        "He should have unlocked the cage because animals deserve to choose where they live.",
    ) is True

    feeder_check = levels["wise_parrot_bird_feeder_steps"]["checks"]["independent_check"]
    assert "steps" in feeder_check["prompt"].lower()
    assert feeder_check["answer_rule"] == "bird_feeder_procedure"
    assert curriculum._answer_matches(
        feeder_check,
        "First clean the container, next add fresh grains and water, then place it safely, and finally clean it regularly.",
    ) is True


def test_backend_owns_the_open_answer_rubric_gate():
    activity = {
        "activity_id": "wise_parrot_story_continuation:independent_check:1",
        "skill_ids": ["writing.summary_own_words", "writing.reason_answer"],
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.75,
        "rubric_criteria": [
            {"id": "continues_story", "required": True},
            {"id": "narrative_coherence", "required": True},
            {"id": "language_control", "required": False},
        ],
    }
    inflated_model_result = {
        "schema_version": "school-v3-rubric-1",
        "item_id": activity["activity_id"],
        "skill_ids": list(activity["skill_ids"]),
        "score": 0.99,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {"id": "continues_story", "met": True, "quality": 0.9, "evidence_quote": "the parrot"},
            {"id": "narrative_coherence", "met": False, "quality": 0.2, "evidence_quote": "clock sandwich"},
            {"id": "language_control", "met": True, "quality": 0.9, "evidence_quote": "flew"},
        ],
        "misconception_tags": ["incoherent_sequence"],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "Model claimed this was nearly complete.",
    }

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        inflated_model_result,
        answer="the parrot flew through a clock sandwich",
    )

    assert decision["correct"] is False
    assert decision["score"] < 0.75
    assert decision["model_score"] == 0.99
    assert "narrative_coherence" in decision["missing_criteria"]


def test_ambiguous_concept_answer_uses_semantic_evaluator_before_progression(
    store,
    monkeypatch,
):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=next(
            chapter
            for chapter in curriculum.CLASS_5_CURRICULUM_CHAPTERS
            if chapter["chapter_id"] == "eng_c5_ch05"
        ),
        level_id="frog_between_two_homes",
    )
    answer = (
        "It hopped across moss and used the water-filled ditch, but the ditch "
        "did not cover its eyes."
    )
    captured = []

    async def semantic_evaluator(activity, learner_answer):
        captured.append(activity)
        quotes = {
            "land_evidence": "hopped across moss",
            "water_evidence": "used the water-filled ditch",
        }
        return SchoolV3RubricEvaluation(
            schema_version="school-v3-rubric-1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=1.0,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=1.0,
                    evidence_quote=quotes[criterion["id"]],
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="Both habitat uses are supported.",
        )

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        semantic_evaluator,
    )
    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "frog_between_two_homes:independent_check:1",
            "answer": answer,
        },
    )

    assert response.status_code == 200
    assert len(captured) == 1
    assert captured[0]["evaluation_mode"] == "llm_rubric"
    assert [criterion["id"] for criterion in captured[0]["rubric_criteria"]] == [
        "land_evidence",
        "water_evidence",
    ]
    assert response.json()["last_feedback"]["correct"] is True
    event = store.learning_events[-1]
    assert event["evidence_json"]["evaluation_mode"] == "semantic_llm_rubric"


def test_open_answer_provider_failure_does_not_mutate_session_or_evidence(store, monkeypatch):
    session_id = str(uuid4())
    original_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id="rainbow_journey_writing",
    )

    async def unavailable(_activity, _answer):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", unavailable)
    before_event_count = len(store.learning_events)
    client = TestClient(app)
    response = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "rainbow_journey_writing:independent_check:1",
            "answer": RAINBOW_JOURNEY_PARAGRAPH,
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "open_answer_evaluation_unavailable"
    persisted = _run(store.get_school_session("test_user", session_id))
    assert persisted["state_json"] == original_state
    assert len(store.learning_events) == before_event_count


def test_open_answer_provider_schema_failure_returns_structured_503(store, monkeypatch):
    session_id = str(uuid4())
    original_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id="rainbow_journey_writing",
    )

    async def invalid_schema(_activity, _answer):
        return SchoolV3RubricEvaluation.model_validate(
            {
                "schema_version": "school-v3-rubric-1",
                "item_id": "rainbow_journey_writing:independent_check:1",
                "skill_ids": ["writing.summary_own_words"],
                "score": 4,
                "confidence": 0.9,
                "language_detected": "en",
                "criteria": [
                    {
                        "id": "journey_structure",
                        "met": True,
                        "quality": 0.9,
                        "evidence_quote": "Last Sunday",
                    }
                ],
                "misconception_tags": [],
                "blockers": [],
                "needs_human_review": False,
                "feedback_to_learner": "Invalid provider score scale.",
            }
        )

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        invalid_schema,
    )
    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "rainbow_journey_writing:independent_check:1",
            "answer": RAINBOW_JOURNEY_PARAGRAPH,
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "open_answer_evaluation_unavailable"
    persisted = _run(store.get_school_session("test_user", session_id))
    assert persisted["state_json"] == original_state


def test_open_answer_server_deadline_prevents_late_progress_mutation(store, monkeypatch):
    session_id = str(uuid4())
    original_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id="rainbow_journey_writing",
    )

    async def too_slow(_activity, _answer):
        await asyncio.sleep(0.05)
        raise AssertionError("deadline should cancel the evaluator")

    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", too_slow)
    monkeypatch.setattr(
        school_rebuild_routes,
        "SCHOOL_OPEN_ANSWER_TIMEOUT_SECONDS",
        0.01,
        raising=False,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "_school_open_answer_timeout_seconds",
        lambda: 0.01,
        raising=False,
    )
    before_event_count = len(store.learning_events)
    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "rainbow_journey_writing:independent_check:1",
            "answer": RAINBOW_JOURNEY_PARAGRAPH,
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "open_answer_evaluation_timeout"
    persisted = _run(store.get_school_session("test_user", session_id))
    assert persisted["state_json"] == original_state
    assert len(store.learning_events) == before_event_count


def test_local_open_answer_evaluator_has_no_server_deadline(store, monkeypatch):
    session_id = str(uuid4())
    original_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id="rainbow_journey_writing",
    )

    async def slow_local_success(activity, answer):
        await asyncio.sleep(0.03)
        return SchoolV3RubricEvaluation(
            schema_version="school-v3-rubric-1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.9,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.9,
                    evidence_quote=answer[:120],
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        slow_local_success,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "SCHOOL_OPEN_ANSWER_TIMEOUT_SECONDS",
        0.01,
        raising=False,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "_school_open_answer_timeout_seconds",
        lambda: None,
        raising=False,
    )

    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "rainbow_journey_writing:independent_check:1",
            "answer": RAINBOW_JOURNEY_PARAGRAPH,
        },
    )

    assert response.status_code == 200
    assert response.json()["progress"]["completed_levels"] == (
        int(original_state["current_level_index"]) + 1
    )
    assert response.json()["last_feedback"]["correct"] is True


def test_structurally_incomplete_open_answer_skips_model_and_opens_bridge(store, monkeypatch):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id="wise_parrot_story_continuation",
    )
    call_count = 0

    async def should_not_run(_activity, _answer):
        nonlocal call_count
        call_count += 1
        raise AssertionError("preflight failure must not call the model")

    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", should_not_run)
    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "wise_parrot_story_continuation:independent_check:1",
            "answer": "The parrot flew away.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    _assert_no_hidden_keys(body)
    assert call_count == 0
    assert body["current_activity"]["kind"] == "bridge"
    assert body["progress"]["completed_levels"] == 8
    event = store.learning_events[-1]
    assert event["score"] == 0.0
    assert "open_answer_preflight_failed" in event["blockers"]


def test_inflated_open_answer_model_score_cannot_advance_required_gap(store, monkeypatch):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id="wise_parrot_story_continuation",
    )

    async def inflated(activity, answer):
        return SchoolV3RubricEvaluation(
            schema_version="school-v3-rubric-1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.99,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=criterion["id"] != "narrative_coherence",
                    quality=0.2 if criterion["id"] == "narrative_coherence" else 0.9,
                    evidence_quote="the parrot flew towards the forest",
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=["incoherent_sequence"],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The model gave this a high headline score.",
        )

    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", inflated)
    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "wise_parrot_story_continuation:independent_check:1",
            "answer": WISE_PARROT_STORY_CONTINUATION,
        },
    )

    assert response.status_code == 200
    body = response.json()
    _assert_no_hidden_keys(body)
    assert body["current_activity"]["kind"] == "bridge"
    assert body["progress"]["completed_levels"] == 8
    event = store.learning_events[-1]
    assert event["score"] < 0.75
    assert event["evidence_json"]["model_score"] == 0.99
    assert any(
        criterion["id"] == "narrative_coherence" and criterion["met"] is False
        for criterion in event["criteria_json"]
    )


def test_curriculum_attempt_store_boundary_rolls_back_event_and_state_together(store, monkeypatch):
    session_id = str(uuid4())
    original_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id="wise_parrot_opinion_reason",
    )
    session_write = {
        "session_id": session_id,
        "user_id": "test_user",
        "api_version": "rebuild",
        "flow_type": "curriculum",
        "subject_id": "english",
        "class_no": 5,
        "status": "active",
        "current_stage": "8",
        "linked_session_id": None,
        "state_json": {**original_state, "last_feedback": {"message": "should roll back"}},
    }
    learning_event = {
        "source_event_key": "school_rebuild:curriculum:atomic:test",
        "user_id": "test_user",
        "domain": "school",
        "task_type": "school_rebuild_curriculum",
        "module_id": "wise_parrot_opinion_reason",
        "session_id": session_id,
        "node_id": "activity",
        "skill_id": "curriculum.wise_parrot_opinion_reason",
        "source": "school_rebuild",
    }
    original_upsert = store.upsert_school_session

    async def fail_after_session_write(**kwargs):
        await original_upsert(**kwargs)
        raise RuntimeError("simulated session write failure")

    monkeypatch.setattr(store, "upsert_school_session", fail_after_session_write)

    with pytest.raises(RuntimeError, match="simulated session write failure"):
        _run(
            store.persist_school_curriculum_attempt(
                learning_event=learning_event,
                school_session=session_write,
                expected_state_json=original_state,
            )
        )

    persisted = _run(store.get_school_session("test_user", session_id))
    assert persisted["state_json"] == original_state
    assert not any(
        event.get("source_event_key") == learning_event["source_event_key"]
        for event in store.learning_events
    )


def test_curriculum_attempt_rejects_state_changed_by_another_submit(store):
    session_id = str(uuid4())
    expected_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id="wise_parrot_opinion_reason",
    )
    newer_state = copy.deepcopy(expected_state)
    newer_state["last_feedback"] = {"message": "another request committed first"}
    _run(
        store.upsert_school_session(
            session_id=session_id,
            user_id="test_user",
            api_version="rebuild",
            flow_type="curriculum",
            subject_id="english",
            class_no=5,
            status="active",
            current_stage="7",
            linked_session_id=None,
            state_json=newer_state,
        )
    )
    event_key = "school_rebuild:curriculum:stale:test"

    with pytest.raises(ValueError, match="stale_school_answer_session"):
        _run(
            store.persist_school_curriculum_attempt(
                learning_event={
                    "source_event_key": event_key,
                    "user_id": "test_user",
                    "domain": "school",
                    "task_type": "school_rebuild_curriculum",
                    "module_id": "wise_parrot_opinion_reason",
                    "session_id": session_id,
                    "node_id": "activity",
                    "skill_id": "curriculum.wise_parrot_opinion_reason",
                    "source": "school_rebuild",
                },
                school_session={
                    "session_id": session_id,
                    "user_id": "test_user",
                    "api_version": "rebuild",
                    "flow_type": "curriculum",
                    "subject_id": "english",
                    "class_no": 5,
                    "status": "active",
                    "current_stage": "8",
                    "linked_session_id": None,
                    "state_json": expected_state,
                },
                expected_state_json=expected_state,
            )
        )

    persisted = _run(store.get_school_session("test_user", session_id))
    assert persisted["state_json"] == newer_state
    assert not any(event.get("source_event_key") == event_key for event in store.learning_events)


def test_in_memory_curriculum_attempt_boundary_serializes_concurrent_writers(store, monkeypatch):
    session_id = str(uuid4())
    expected_state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id="wise_parrot_opinion_reason",
    )
    active_writers = 0
    max_active_writers = 0
    original_record = store.record_learning_event

    async def overlapping_record(**kwargs):
        nonlocal active_writers, max_active_writers
        active_writers += 1
        max_active_writers = max(max_active_writers, active_writers)
        await asyncio.sleep(0.02)
        await original_record(**kwargs)
        active_writers -= 1

    monkeypatch.setattr(store, "record_learning_event", overlapping_record)

    def event(label: str) -> dict[str, Any]:
        return {
            "source_event_key": f"school_rebuild:curriculum:concurrent:{label}",
            "user_id": "test_user",
            "domain": "school",
            "task_type": "school_rebuild_curriculum",
            "module_id": "wise_parrot_opinion_reason",
            "session_id": session_id,
            "node_id": f"activity-{label}",
            "skill_id": "curriculum.wise_parrot_opinion_reason",
            "source": "school_rebuild",
        }

    def session_write(label: str) -> dict[str, Any]:
        state = copy.deepcopy(expected_state)
        state["last_feedback"] = {"message": label}
        return {
            "session_id": session_id,
            "user_id": "test_user",
            "api_version": "rebuild",
            "flow_type": "curriculum",
            "subject_id": "english",
            "class_no": 5,
            "status": "active",
            "current_stage": "8",
            "linked_session_id": None,
            "state_json": state,
        }

    async def compete():
        return await asyncio.gather(
            store.persist_school_curriculum_attempt(
                learning_event=event("first"),
                school_session=session_write("first"),
                expected_state_json=expected_state,
            ),
            store.persist_school_curriculum_attempt(
                learning_event=event("second"),
                school_session=session_write("second"),
                expected_state_json=expected_state,
            ),
            return_exceptions=True,
        )

    results = _run(compete())

    assert max_active_writers == 1
    assert sum(result is None for result in results) == 1
    assert sum(
        isinstance(result, ValueError) and str(result) == "stale_school_answer_session"
        for result in results
    ) == 1
    assert len(
        [event for event in store.learning_events if "curriculum:concurrent" in event["source_event_key"]]
    ) == 1


def test_curriculum_answer_avoids_redundant_profile_and_post_commit_reads(store, monkeypatch):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id="wise_parrot_opinion_reason",
    )
    session_reads = 0
    profile_reads = 0
    original_get_session = store.get_school_session
    original_get_profile = store.get_profile

    async def count_session_read(user_id, requested_session_id):
        nonlocal session_reads
        session_reads += 1
        return await original_get_session(user_id, requested_session_id)

    async def count_profile_read(user_id):
        nonlocal profile_reads
        profile_reads += 1
        return await original_get_profile(user_id)

    monkeypatch.setattr(store, "get_school_session", count_session_read)
    monkeypatch.setattr(store, "get_profile", count_profile_read)

    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "wise_parrot_opinion_reason:independent_check:1",
            "answer": "He should unlock the cage because the parrot deserves freedom.",
        },
    )

    assert response.status_code == 200
    assert session_reads == 1
    assert profile_reads == 0


def test_rainbow_travel_check_accepts_an_original_past_tense_journey_sentence():
    travel_level = next(
        level
        for level in curriculum.CLASS_5_RAINBOW_CHAPTER["levels"]
        if level["level_id"] == "rainbow_travel_paragraph"
    )
    check = travel_level["checks"]["independent_check"]

    assert curriculum._answer_matches(check, "Yesterday I went to Jaipur by train.") is True
    assert curriculum._answer_matches(check, "I went home.") is True
    assert curriculum._answer_matches(check, "went") is False
    assert curriculum._answer_matches(check, "I will go to Jaipur tomorrow.") is False


def test_rainbow_chapter_covers_the_full_core_learning_surface():
    levels = {
        level["level_id"]: level
        for level in curriculum.CLASS_5_RAINBOW_CHAPTER["levels"]
    }
    required_level_ids = {
        "rainbow_image_bridge",
        "rainbow_word_meanings",
        "rainbow_reference_words",
        "rainbow_rhyme_sound",
        "rainbow_compound_words",
        "rainbow_noun_verb_use",
        "rainbow_opposites",
        "rainbow_travel_paragraph",
        "rainbow_journey_writing",
        "rainbow_colour_order",
        "rainbow_natural_human_made",
    }
    assert required_level_ids <= set(levels)

    comparison_check = levels["rainbow_image_bridge"]["checks"]["independent_check"]
    assert "why" in comparison_check["prompt"].lower()
    assert curriculum._answer_matches(
        comparison_check,
        "It seems to build a colourful bridge from earth to sky.",
    ) is True

    compound_checks = levels["rainbow_compound_words"]["checks"]
    assert compound_checks["masterclass"]["passage"] != compound_checks["independent_check"]["passage"]

    paragraph_check = levels["rainbow_journey_writing"]["checks"]["independent_check"]
    assert paragraph_check["response_mode"] == "paragraph"
    assert paragraph_check["evaluation_mode"] == "llm_rubric"
    assert paragraph_check["pass_score"] == 0.75
    assert len(RAINBOW_JOURNEY_PARAGRAPH.split()) == 80
    assert curriculum._open_answer_preflight(paragraph_check, RAINBOW_JOURNEY_PARAGRAPH) is True
    assert curriculum._open_answer_preflight(paragraph_check, "I went home.") is False
    repetitive_word_salad = " ".join(["I", "went", "bus"] * 27)
    assert len(repetitive_word_salad.split()) == 81
    assert curriculum._open_answer_preflight(paragraph_check, repetitive_word_salad) is False


def test_curriculum_answer_replay_returns_exact_response_and_one_event(store):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id="wise_parrot_opinion_reason",
    )
    payload = {
        "activity_id": "wise_parrot_opinion_reason:independent_check:1",
        "answer": "He should unlock the cage because the parrot deserves freedom.",
    }
    client = TestClient(app)

    first = client.post(
        f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
    )
    replay = client.post(
        f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert len([event for event in store.learning_events if event["session_id"] == session_id]) == 1


def test_curriculum_answer_same_activity_different_answer_conflicts(store):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id="wise_parrot_opinion_reason",
    )
    activity_id = "wise_parrot_opinion_reason:independent_check:1"
    client = TestClient(app)
    first = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": activity_id,
            "answer": "He should unlock the cage because the parrot deserves freedom.",
        },
    )
    conflict = client.post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={"activity_id": activity_id, "answer": "Keep the cage locked."},
    )

    assert first.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "curriculum_answer_conflict"
    assert len([event for event in store.learning_events if event["session_id"] == session_id]) == 1


def test_concurrent_identical_open_answers_invoke_evaluator_once(store, monkeypatch):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id="rainbow_journey_writing",
    )
    started = threading.Event()
    release = threading.Event()
    call_count = 0

    async def blocked_evaluator(activity, answer):
        nonlocal call_count
        call_count += 1
        started.set()
        await asyncio.to_thread(release.wait, 2)
        return SchoolV3RubricEvaluation(
            schema_version="school-v3-rubric-1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.9,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.9,
                    evidence_quote=answer[:120],
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )

    monkeypatch.setattr(
        school_rebuild_routes, "evaluate_school_open_answer", blocked_evaluator
    )
    payload = {
        "activity_id": "rainbow_journey_writing:independent_check:1",
        "answer": RAINBOW_JOURNEY_PARAGRAPH,
    }

    def submit():
        return TestClient(app).post(
            f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(submit)
        assert started.wait(2)
        concurrent = submit()
        release.set()
        first = first_future.result(timeout=3)

    assert first.status_code == 200
    assert concurrent.status_code in {200, 409}
    if concurrent.status_code == 409:
        assert concurrent.json()["detail"]["code"] == "curriculum_answer_in_progress"
    else:
        assert concurrent.json() == first.json()
    replay = submit()
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert call_count == 1
    assert len([event for event in store.learning_events if event["session_id"] == session_id]) == 1


def test_long_local_evaluation_renews_answer_claim_before_it_can_go_stale(store, monkeypatch):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id="rainbow_journey_writing",
    )
    started = threading.Event()
    call_count = 0

    async def slow_local_evaluator(activity, answer):
        nonlocal call_count
        call_count += 1
        started.set()
        await asyncio.sleep(0.08)
        return SchoolV3RubricEvaluation(
            schema_version="school-v3-rubric-1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.9,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.9,
                    evidence_quote=answer[:120],
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        slow_local_evaluator,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "_school_open_answer_timeout_seconds",
        lambda: None,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "SCHOOL_ANSWER_HEARTBEAT_SECONDS",
        0.005,
        raising=False,
    )
    store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS = 0.02
    payload = {
        "activity_id": "rainbow_journey_writing:independent_check:1",
        "answer": RAINBOW_JOURNEY_PARAGRAPH,
    }

    def submit():
        return TestClient(app).post(
            f"/school/curriculum/{session_id}/answer",
            headers=AUTH,
            json=payload,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(submit)
        assert started.wait(1)
        time.sleep(0.05)
        concurrent = submit()
        first = first_future.result(timeout=2)

    assert first.status_code == 200
    assert concurrent.status_code == 409
    assert concurrent.json()["detail"]["code"] == "curriculum_answer_in_progress"
    assert call_count == 1


def test_local_evaluation_is_cancelled_immediately_when_claim_renewal_is_lost(
    store,
    monkeypatch,
):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id="rainbow_journey_writing",
    )
    cancelled = threading.Event()

    async def evaluator_that_must_be_cancelled(_activity, _answer):
        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            cancelled.set()
            raise
        raise AssertionError("lost claim must cancel evaluator")

    async def lose_claim(*_args, **_kwargs):
        return False

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        evaluator_that_must_be_cancelled,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "_school_open_answer_timeout_seconds",
        lambda: None,
    )
    monkeypatch.setattr(
        school_rebuild_routes,
        "SCHOOL_ANSWER_HEARTBEAT_SECONDS",
        0.005,
    )
    monkeypatch.setattr(store, "renew_school_answer_request", lose_claim)

    response = TestClient(app).post(
        f"/school/curriculum/{session_id}/answer",
        headers=AUTH,
        json={
            "activity_id": "rainbow_journey_writing:independent_check:1",
            "answer": RAINBOW_JOURNEY_PARAGRAPH,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "stale_curriculum_answer"
    assert cancelled.wait(0.2)


def test_open_answer_provider_failure_can_be_retried_with_same_request(store, monkeypatch):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_RAINBOW_CHAPTER,
        level_id="rainbow_journey_writing",
    )
    attempts = 0

    async def fail_then_succeed(activity, answer):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("provider unavailable")
        return SchoolV3RubricEvaluation(
            schema_version="school-v3-rubric-1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.9,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"], met=True, quality=0.9, evidence_quote=answer[:120]
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )

    monkeypatch.setattr(
        school_rebuild_routes, "evaluate_school_open_answer", fail_then_succeed
    )
    payload = {
        "activity_id": "rainbow_journey_writing:independent_check:1",
        "answer": RAINBOW_JOURNEY_PARAGRAPH,
    }
    client = TestClient(app)
    failed = client.post(
        f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
    )
    request_row = _run(
        store.get_school_answer_request("test_user", session_id, payload["activity_id"])
    )
    retried = client.post(
        f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
    )

    assert failed.status_code == 503
    assert request_row["status"] == "failed"
    assert retried.status_code == 200
    assert attempts == 2


def test_completed_curriculum_answer_replays_after_session_completion(store):
    session_id = str(uuid4())
    _seed_frog_chapter_check_session(store, session_id=session_id)
    client = TestClient(app)
    body = client.get(f"/school/curriculum/{session_id}", headers=AUTH).json()
    for _ in range(12):
        activity = body["current_activity"]
        body = _answer(body, _correct_curriculum_answer(activity), client)
    final_activity = body["current_activity"]
    payload = {
        "activity_id": final_activity["activity_id"],
        "answer": _correct_curriculum_answer(final_activity),
    }
    before = len(store.learning_events)
    first = client.post(
        f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
    )
    replay = client.post(
        f"/school/curriculum/{session_id}/answer", headers=AUTH, json=payload
    )

    assert first.status_code == 200
    assert first.json()["status"] == "complete"
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert len(store.learning_events) == before + 1


def test_failed_curriculum_persist_does_not_complete_answer_request(store, monkeypatch):
    session_id = str(uuid4())
    state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id="wise_parrot_opinion_reason",
    )
    activity_id = "wise_parrot_opinion_reason:independent_check:1"
    answer_hash = hashlib.sha256(b"answer").hexdigest()
    claimed = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )
    assert claimed["outcome"] == "claimed"
    original_upsert = store.upsert_school_session

    async def fail_after_session_write(**kwargs):
        await original_upsert(**kwargs)
        raise RuntimeError("simulated session write failure")

    monkeypatch.setattr(store, "upsert_school_session", fail_after_session_write)
    with pytest.raises(RuntimeError, match="simulated session write failure"):
        _run(
            store.persist_school_curriculum_attempt(
                learning_event={
                    "source_event_key": "school_rebuild:curriculum:request-rollback",
                    "user_id": "test_user",
                    "domain": "school",
                    "task_type": "school_rebuild_curriculum",
                    "module_id": "wise_parrot_opinion_reason",
                    "session_id": session_id,
                    "node_id": activity_id,
                    "skill_id": "curriculum.wise_parrot_opinion_reason",
                    "source": "school_rebuild",
                },
                school_session={
                    "session_id": session_id,
                    "user_id": "test_user",
                    "api_version": "rebuild",
                    "flow_type": "curriculum",
                    "subject_id": "english",
                    "class_no": 5,
                    "status": "active",
                    "current_stage": "8",
                    "linked_session_id": None,
                    "state_json": {**state, "last_feedback": {"message": "rollback"}},
                },
                expected_state_json=state,
                request_activity_id=activity_id,
                request_answer_hash=answer_hash,
                request_claim_token=claimed["claim_token"],
                response_json={"exact": "public response"},
            )
        )

    request_row = _run(
        store.get_school_answer_request("test_user", session_id, activity_id)
    )
    assert request_row["status"] != "completed"


def test_stale_processing_school_answer_request_can_be_reclaimed(store):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id="wise_parrot_opinion_reason",
    )
    activity_id = "wise_parrot_opinion_reason:independent_check:1"
    answer_hash = hashlib.sha256(b"same answer").hexdigest()
    first = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )
    assert first["outcome"] == "claimed"
    store.school_answer_requests[(session_id, activity_id)]["updated_at"] = (
        time.time() - store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS - 1
    )

    reclaimed = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )

    assert store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS >= 60
    assert reclaimed["outcome"] == "claimed"


def test_expired_school_answer_claim_cannot_complete_newer_lease(store):
    session_id = str(uuid4())
    state = _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id="wise_parrot_opinion_reason",
    )
    activity_id = "wise_parrot_opinion_reason:independent_check:1"
    answer_hash = hashlib.sha256(b"same answer").hexdigest()
    first = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )
    store.school_answer_requests[(session_id, activity_id)]["updated_at"] = (
        time.time() - store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS - 1
    )
    newer = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )
    assert first["claim_token"] != newer["claim_token"]
    event_key = "school_rebuild:curriculum:old-completion-fenced"

    with pytest.raises(ValueError, match="stale_school_answer_request"):
        _run(
            store.persist_school_curriculum_attempt(
                learning_event={
                    "source_event_key": event_key,
                    "user_id": "test_user",
                    "domain": "school",
                    "task_type": "school_rebuild_curriculum",
                    "module_id": "wise_parrot_opinion_reason",
                    "session_id": session_id,
                    "node_id": activity_id,
                    "skill_id": "curriculum.wise_parrot_opinion_reason",
                    "source": "school_rebuild",
                },
                school_session={
                    "session_id": session_id,
                    "user_id": "test_user",
                    "api_version": "rebuild",
                    "flow_type": "curriculum",
                    "subject_id": "english",
                    "class_no": 5,
                    "status": "active",
                    "current_stage": "8",
                    "linked_session_id": None,
                    "state_json": {**state, "last_feedback": {"message": "old worker"}},
                },
                expected_state_json=state,
                request_activity_id=activity_id,
                request_answer_hash=answer_hash,
                request_claim_token=first["claim_token"],
                response_json={"worker": "old"},
            )
        )

    request_row = _run(
        store.get_school_answer_request("test_user", session_id, activity_id)
    )
    persisted = _run(store.get_school_session("test_user", session_id))
    assert request_row["status"] == "processing"
    assert request_row["claim_token"] == newer["claim_token"]
    assert persisted["state_json"] == state
    assert not any(event.get("source_event_key") == event_key for event in store.learning_events)


def test_expired_school_answer_claim_cannot_fail_newer_lease(store):
    session_id = str(uuid4())
    _seed_curriculum_activity_session(
        store,
        session_id=session_id,
        chapter=curriculum.CLASS_5_WISE_PARROT_CHAPTER,
        level_id="wise_parrot_opinion_reason",
    )
    activity_id = "wise_parrot_opinion_reason:independent_check:1"
    answer_hash = hashlib.sha256(b"same answer").hexdigest()
    first = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )
    store.school_answer_requests[(session_id, activity_id)]["updated_at"] = (
        time.time() - store.SCHOOL_ANSWER_REQUEST_STALE_SECONDS - 1
    )
    newer = _run(
        store.claim_school_answer_request(
            "test_user", session_id, activity_id, answer_hash
        )
    )

    _run(
        store.fail_school_answer_request(
            "test_user",
            session_id,
            activity_id,
            answer_hash,
            first["claim_token"],
        )
    )

    request_row = _run(
        store.get_school_answer_request("test_user", session_id, activity_id)
    )
    assert first["claim_token"] != newer["claim_token"]
    assert request_row["status"] == "processing"
    assert request_row["claim_token"] == newer["claim_token"]


def test_revised_rainbow_content_reopens_only_the_stale_chapter_completion():
    landing = curriculum.curriculum_landing(
        school_profile={"target_class_no": 5, "subject_ids": ["english"]},
        placement_report={"unlock_state": "target_unlocked", "report_id": "report-1"},
        recap_session=None,
        latest_curriculum_session={
            "status": "complete",
            "state_json": {
                "status": "complete",
                "subject_id": "english",
                "target_class_no": 5,
                "completed_chapter_ids": ["eng_c5_ch01", "eng_c5_ch02", "eng_c5_ch03"],
                "chapter": {"chapter_id": "eng_c5_ch03"},
            },
        },
    )

    assert landing["chapters_preview"][0]["status"] == "complete"
    assert landing["chapters_preview"][1]["status"] == "complete"
    assert landing["chapters_preview"][2]["status"] == "ready"


def test_non_certifying_content_revision_preserves_completed_chapter():
    completed_ids = [f"eng_c5_ch0{index}" for index in range(1, 6)]
    landing = curriculum.curriculum_landing(
        school_profile={"target_class_no": 5, "subject_ids": ["english"]},
        placement_report={"unlock_state": "target_unlocked", "report_id": "report-1"},
        recap_session=None,
        latest_curriculum_session={
            "status": "complete",
            "state_json": {
                "status": "complete",
                "subject_id": "english",
                "target_class_no": 5,
                "completed_chapter_ids": completed_ids,
                "completed_chapter_versions": {
                    "eng_c5_ch03": curriculum.CLASS_5_RAINBOW_CHAPTER["content_version"],
                    "eng_c5_ch04": curriculum.CLASS_5_WISE_PARROT_CHAPTER["content_version"],
                    "eng_c5_ch05": "2026-07-11.2",
                },
                "chapter": {
                    "chapter_id": "eng_c5_ch05",
                    "content_version": "2026-07-11.2",
                },
            },
        },
    )

    assert landing["chapters_preview"][4]["status"] == "complete"
    assert landing["source_note"] == "All available target-class chapters are complete."

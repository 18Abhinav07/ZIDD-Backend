"""Runtime content personalization for prep scaffolds.

This layer renders structured bridge exercises from topic/role context instead
of mutating unrelated authored examples with long string-rewrite chains.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.content.schema import BridgeExercise


@dataclass(frozen=True)
class TopicPack:
    canonical_topic: str
    topic_phrase: str


def _topic_from_context(career_context: dict | None) -> str:
    context = career_context or {}
    topics = context.get("gd_topics") or context.get("custom_gd_topics") or []
    if isinstance(topics, list) and topics:
        return str(topics[0]).strip()
    return str(context.get("gd_topic") or "").strip()


def _topic_phrase(topic: str) -> str:
    clean = topic.strip().strip("\"'").strip()
    if clean.endswith("?"):
        clean = clean[:-1].strip()
    # Treat the complete learner-selected topic as an opaque motion. Trying to
    # infer its subject and verb breaks as soon as the subject has multiple
    # words or the motion is phrased as an "Is ..." question.
    return f'the motion "{clean}"'


def build_topic_pack(career_context: dict | None) -> TopicPack | None:
    topic = _topic_from_context(career_context)
    if not topic:
        return None
    return TopicPack(canonical_topic=topic, topic_phrase=_topic_phrase(topic))


_FILL_BLANKS = {
    "gd_01_stake_position": "On this topic, I ___ that {topic_phrase} needs a clear position, not vague agreement.",
    "gd_02_support_with_evidence": "I support a phased approach to {topic_phrase}. ___, a pilot could compare outcomes before and after rollout.",
    "gd_03_take_the_floor": "If I could ___ to that, {topic_phrase} also raises a fairness angle we have not discussed yet.",
    "gd_04_build_on_others": "Building ___ what Maya said about {topic_phrase}, we should also consider stakeholder trust.",
    "gd_05_disagree_respectfully": "That's a fair point, ___ I'd push back because {topic_phrase} also needs safeguards for vulnerable groups.",
    "gd_06_balanced_view": "There are real risks in {topic_phrase}, but ___ I think a limited pilot is better than avoiding it entirely.",
    "gd_07_steer_back": "I think we've ___ a bit - the real question is which evidence should decide {topic_phrase}.",
    "gd_08_include_quiet": "I'd like to ___ Neha's take on {topic_phrase} - she's been quiet and may see an impact angle.",
    "gd_09_manage_dominator": "That's a strong point, Karan - let's also ___ others on {topic_phrase} before we move on.",
    "gd_10_drive_consensus": "So to ___: Maya says the evidence supports {topic_phrase}, Dev says it is still too mixed, and we agree reliable evidence should decide.",
}

_FILL_BLANKS_BY_EXERCISE = {
    "gd_08_include_quiet_bx1": (
        "I'd like to ___ Neha's take on {topic_phrase} - she's been quiet and may see a useful impact angle.",
        "hear",
    ),
    "gd_08_include_quiet_bx4": (
        "Neha, you've been quiet on {topic_phrase}; I'd like to ___ your view if you want to add.",
        "hear",
    ),
    "gd_09_manage_dominator_bx1": (
        "That's a strong point, Karan - let's also ___ what others think about {topic_phrase} before we move on.",
        "hear",
    ),
    "gd_09_manage_dominator_bx4": (
        "Those are useful points, Vik; let me ___ you there so we can bring in another view on {topic_phrase}.",
        "pause",
    ),
}

_MCQ_OPTIONS = {
    "gd_01_stake_position": (
        "I believe {topic_phrase} should be adopted carefully with clear safeguards.",
        "There are many sides and I am not sure what to say.",
        "Maybe {topic_phrase} is good, but maybe it is also bad.",
    ),
    "gd_02_support_with_evidence": (
        "{topic_phrase} could work - for instance, a pilot can compare outcome quality, decision time, and stakeholder complaints before scaling.",
        "{topic_phrase} could work because it is useful and good.",
        "I feel strongly that {topic_phrase} is important.",
    ),
    "gd_03_take_the_floor": (
        "Building on Riya's point, could I add one fairness concern about {topic_phrase}?",
        "Wait, let me talk now because I have a point.",
        "I disagree with everyone and want to change the topic.",
    ),
    "gd_04_build_on_others": (
        "That's a useful point on efficiency, and it also connects to stakeholder trust in {topic_phrase}.",
        "I agree with you completely.",
        "My point is unrelated but important.",
    ),
    "gd_05_disagree_respectfully": (
        "You make a fair point on speed, though I'd argue {topic_phrase} still needs human review for edge cases.",
        "No, that is wrong and not practical.",
        "I disagree because I just do not like it.",
    ),
    "gd_06_balanced_view": (
        "{topic_phrase} can deliver real benefits, but it can also create implementation risks that need clear safeguards.",
        "{topic_phrase} is only good and there are no real risks.",
        "{topic_phrase} is only bad, so we should reject it completely.",
    ),
    "gd_07_steer_back": (
        "These examples are useful, but let's return to {topic_phrase} and test the evidence most relevant to that claim.",
        "This is boring; let's discuss something else.",
        "Everyone is going off topic, so I will start over.",
    ),
    "gd_08_include_quiet": (
        "Neha, you have been listening closely - I'd like your view on the stakeholder-impact side of {topic_phrase}.",
        "Neha, why are you not saying anything?",
        "Someone quiet should speak now.",
    ),
    "gd_09_manage_dominator": (
        "Those are strong points, Vik; let me pause you so we can hear one more view on {topic_phrase}.",
        "Vik, stop talking so much.",
        "You have already spoken, so your point does not count.",
    ),
    "gd_10_drive_consensus": (
        "We have one case supporting {topic_phrase} and one asking for stronger evidence; we agree on defining the evidence threshold before deciding.",
        "Everyone said different things, so there is no conclusion.",
        "I think my view won, so we should end there.",
    ),
}

_SPOKEN = {
    "gd_01_stake_position": "Topic: '{topic}'. Open the discussion by stating your position in one sentence before giving reasons.",
    "gd_02_support_with_evidence": "State your position on '{topic}', then support it with one concrete fact, example, or comparison.",
    "gd_03_take_the_floor": "The group is discussing '{topic}'. Enter politely, link to the previous speaker, and add one new angle.",
    "gd_04_build_on_others": "A peer makes a useful point about '{topic}'. Credit them, then extend the idea with one fresh detail.",
    "gd_05_disagree_respectfully": "A peer strongly supports '{topic}'. Disagree respectfully: concede one valid point, then give your reason.",
    "gd_06_balanced_view": "For '{topic}', name one fair point for each side, then say which side you support overall.",
    "gd_07_steer_back": "The GD on '{topic}' has drifted into unrelated examples. Steer the group back in one calm sentence.",
    "gd_08_include_quiet": "In a discussion on '{topic}', one participant has not spoken. Invite them in naturally without pressure.",
    "gd_09_manage_dominator": "A participant keeps dominating the GD on '{topic}'. Reclaim space firmly while keeping rapport.",
    "gd_10_drive_consensus": "The GD on '{topic}' is ending. Maya says the evidence supports the motion; Dev says it is too mixed to accept without qualification. Summarize both, name their shared need for reliable evidence, and propose a decision rule.",
}

_SPOKEN_BY_EXERCISE = {
    "gd_08_include_quiet_bx3": (
        "In the GD on '{topic}', Neha has not spoken. Connect one unresolved topic angle to her perspective and invite her in without pressure."
    ),
    "gd_08_include_quiet_bx5": (
        "In the GD on '{topic}', Maya says she may have nothing new to add. Offer one specific lens and make it safe for her to pass."
    ),
    "gd_09_manage_dominator_bx3": (
        "In the GD on '{topic}', Vik has taken a long turn. Credit one useful part, set a calm boundary, and open the floor to another perspective."
    ),
    "gd_09_manage_dominator_bx5": (
        "In the GD on '{topic}', Rohan interrupts again and says he needs more time. Acknowledge his point, hold the boundary, and name whose perspective the group needs next."
    ),
}


def render_gd_bridge_exercise(
    exercise: BridgeExercise,
    node_id: str,
    career_context: dict | None,
) -> BridgeExercise:
    pack = build_topic_pack(career_context)
    if not pack:
        return exercise

    values = {"topic": pack.canonical_topic, "topic_phrase": pack.topic_phrase}
    exercise_id = str(exercise.id or "")
    if exercise.type == "fill_blank" and exercise_id in _FILL_BLANKS_BY_EXERCISE:
        sentence, answer_key = _FILL_BLANKS_BY_EXERCISE[exercise_id]
        return exercise.model_copy(
            update={
                "sentence": sentence.format(**values),
                "answer_key": answer_key,
                "accept": None,
                "context": f"Practices this GD move directly on: {pack.canonical_topic}.",
            }
        )
    if exercise.type == "fill_blank" and node_id in _FILL_BLANKS:
        return exercise.model_copy(
            update={
                "sentence": _FILL_BLANKS[node_id].format(**values),
                "context": f"Practices this GD move directly on: {pack.canonical_topic}.",
            }
        )
    if exercise.type == "multiple_choice" and node_id in _MCQ_OPTIONS:
        options = [item.format(**values) for item in _MCQ_OPTIONS[node_id]]
        return exercise.model_copy(
            update={
                "sentence": f"Which contribution handles '{pack.canonical_topic}' best for this skill?",
                "context": f"Trains the learner to identify the strongest move for: {pack.canonical_topic}.",
                "answer_key": options[0],
                "options": options,
                "accept": None,
            }
        )
    if exercise.type == "spoken" and exercise_id in _SPOKEN_BY_EXERCISE:
        return exercise.model_copy(
            update={
                "sentence": _SPOKEN_BY_EXERCISE[exercise_id].format(**values),
                "context": f"Free production practice on the active GD topic: {pack.canonical_topic}.",
                "answer_key": exercise.answer_key,
                "accept": None,
                "options": None,
            }
        )
    if exercise.type == "spoken" and node_id in _SPOKEN:
        return exercise.model_copy(
            update={
                "sentence": _SPOKEN[node_id].format(**values),
                "context": f"Free production practice on the active GD topic: {pack.canonical_topic}.",
                "answer_key": exercise.answer_key,
                "accept": None,
                "options": None,
            }
        )
    return exercise

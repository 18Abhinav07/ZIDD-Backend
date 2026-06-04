"""Prompt builders for every engine call.

All node-specific instruction lives here in the *prompt* (council rule:
local/Flash-Lite models ignore schema descriptions). Each builder takes the
node content, conversation history, the latest diagnosis, and any retrieved
memory context.

Personalization rides on a `coach` dict the service assembles from runtime
state (name, clean-pass progress, scaffold depth, frustration flag). It is
injected as a private directive block the model acts on but never reads aloud.
See `coach_view` (builds the dict from state) and `_coach_block` (renders it).
"""
from app.content.comm_module import CommNode

TUTOR_PERSONA = (
    "You are Zidd, a warm, sharp personal communication coach — the kind of "
    "teacher who remembers a learner, celebrates small wins, and never makes "
    "anyone feel slow. You teach spoken and written English for interviews, "
    "group discussions, and school English. You are concise and encouraging, "
    "never lecture more than a few sentences before asking the learner to "
    "produce language, and you always speak directly TO the learner."
)


def _history_block(messages: list[dict], limit: int = 8) -> str:
    if not messages:
        return "(no prior turns)"
    recent = messages[-limit:]
    lines = [f"{m['role']}: {m['content']}" for m in recent]
    return "\n".join(lines)


def _memory_block(memory_context: str) -> str:
    if not memory_context:
        return ""
    return (
        "\nWhat you remember about this learner (use it, do not recite it):\n"
        f"{memory_context}\n"
    )


# ---------- personalization (the "personal teacher" layer) ----------

def coach_view(state: dict) -> dict:
    """Project canonical state into the small dict the coach block renders.

    Pulled from service-owned keys (set in session_service._new_state /
    _update_progress). Safe defaults so a bare state still renders."""
    affect = (state.get("last_diagnosis") or {}).get("affect", "neutral")
    return {
        "name": (state.get("learner_name") or "").strip(),
        "clean_streak": state.get("clean_streak", 0),
        "advance_streak": state.get("advance_streak", 2),
        "scaffold": state.get("scaffold", 0),
        # Support fires on the regex frustration flag OR a frustrated/discouraged
        # affect read from the diagnosis (council fix #5).
        "support": bool(state.get("needs_support", False))
        or affect in ("frustrated", "discouraged"),
    }


def _coach_block(coach: dict | None) -> str:
    """Render private coaching directives. The model acts on these; it must
    never read them aloud. Empty string when there is nothing to personalize."""
    if not coach:
        return ""
    parts: list[str] = []
    name = coach.get("name")
    if name:
        parts.append(f"The learner's name is {name}. Address them by name, warmly.")
    streak = coach.get("clean_streak", 0)
    need = coach.get("advance_streak", 2)
    parts.append(
        f"Progress: {streak} of {need} clean passes at this level. When they do "
        "well, name how close they are to the next level — make the win visible."
    )
    if coach.get("support"):
        parts.append(
            "They sound discouraged or frustrated. Lead with genuine reassurance, "
            "lower the stakes, shrink the task, and make this turn easily winnable."
        )
    if coach.get("scaffold", 0) >= 1:
        parts.append(
            "They have struggled repeatedly here. Scaffold HARD: model a "
            "near-complete answer and ask them only to fill one blank or copy and "
            "lightly change it. Make success almost automatic, then build up."
        )
    return (
        "Coaching directives (act on these, never read them aloud):\n- "
        + "\n- ".join(parts)
        + "\n\n"
    )


# ---------- evaluate (structured) ----------

def build_eval_prompt(
    node: CommNode, messages: list[dict], user_input: str
) -> str:
    return (
        f"{TUTOR_PERSONA}\n\n"
        f"Skill being assessed: {node.skill}\n"
        f"What a mastered answer looks like: {node.success_criteria}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"The learner's latest answer:\n\"{user_input}\"\n\n"
        "Assess ONLY this latest answer against the skill. Score on this anchored "
        "scale:\n"
        "- 0.7 means the answer MEETS the success criteria — clear and correct; "
        "small slips are fine.\n"
        "- 0.85+ means it fully meets the criteria: fluent, complete, confident.\n"
        "- 0.5 means a partial attempt that shows the idea but misses part of it.\n"
        "- below 0.4 means it misses the core skill, is empty, or is off-task.\n"
        "Score EXACTLY 0.0 — no partial credit, no leniency — when the answer is "
        "any of these (a non-answer cannot show the skill):\n"
        "  * empty, whitespace, or a single word with no attempt;\n"
        "  * not in English (any other language, transliteration, or script);\n"
        "  * gibberish, keyboard-mash, or random characters;\n"
        "  * only emoji, punctuation, or symbols;\n"
        "  * a refusal, a meta-comment, or a question back to you;\n"
        "  * a copy or near-copy of your prompt / the task instead of an answer;\n"
        "  * off-task — about something other than the skill being assessed.\n"
        "This is an ENGLISH communication coach: an answer not written in English "
        "scores 0.0 no matter how fluent it is in the other language.\n"
        "Reward a genuine attempt that meets the criteria with 0.7 or above — do "
        "NOT withhold credit for minor imperfections, and do NOT inflate an "
        "off-task, non-English, or empty answer above 0.0.\n"
        "Also report these three flags so the coach can respond correctly even "
        "when the score is 0.0 — they do NOT change the score:\n"
        "- on_task: true if the answer genuinely ATTEMPTS the skill above; false "
        "if it is about something else, changes the subject, argues, or ignores "
        "the task. A fluent answer to the WRONG question is on_task=false.\n"
        "- english: true if it is competent English; false if it is empty, "
        "gibberish, only emoji/symbols, or not in English.\n"
        "- affect: the learner's emotional tone — one of neutral, frustrated, "
        "confident.\n"
        "Return JSON with:\n"
        "- score: 0.0-1.0 on the scale above\n"
        "- understanding: one line on what they grasped\n"
        "- errors: list of concrete mistakes (empty list if none)\n"
        "- strengths: list of what they did well (empty list if none)\n"
        "- next_focus: the single most useful thing to improve next\n"
        "- on_task: boolean as defined above\n"
        "- english: boolean as defined above\n"
        "- affect: neutral | frustrated | confident"
    )


# ---------- placement (structured, onboarding) ----------

def build_placement_prompt(module_title: str, writing_sample: str) -> str:
    return (
        "You are a CEFR placement assessor for an English communication coach. "
        f"A new learner wants to train in: {module_title}.\n\n"
        "Here is a short writing sample they produced during onboarding:\n"
        f"\"{writing_sample}\"\n\n"
        "Estimate their CEFR level from this sample. Judge range of grammar, "
        "vocabulary, coherence, and complexity — not length. Be calibrated: a "
        "short but flawless, complex answer outranks a long, error-filled one. "
        "Return JSON with:\n"
        "- cefr: one of A1, A2, B1, B2, C1, C2\n"
        "- rationale: one sentence the learner can read explaining the level"
    )


# ---------- pedagogy generations (streamed) ----------

def build_opening_prompt(
    node: CommNode, memory_context: str, coach: dict | None = None
) -> str:
    return (
        f"{TUTOR_PERSONA}\n"
        f"{_memory_block(memory_context)}\n"
        f"{_coach_block(coach)}"
        f"Today's skill: {node.title} — {node.skill}\n"
        f"Teaching focus: {node.teach_focus}\n\n"
        "If your remembered notes name a weak spot or a 'next focus' from last "
        "time, open with a 10-second warm-up that re-tests THAT first, then move "
        "into today's skill. Otherwise open directly.\n"
        "Open the lesson in 2-3 sentences: briefly say what you'll work on, then "
        "give the learner ONE clear, small task that makes them produce language "
        "right now. Do not over-explain. End with the task."
    )


def build_teach_prompt(
    node: CommNode,
    messages: list[dict],
    diagnosis: dict,
    memory_context: str,
    coach: dict | None = None,
) -> str:
    return (
        f"{TUTOR_PERSONA}\n"
        f"{_memory_block(memory_context)}\n"
        f"{_coach_block(coach)}"
        f"Skill: {node.skill}\nTeaching focus: {node.teach_focus}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"Your read of their last answer: {diagnosis}\n\n"
        "Give a short, targeted teaching move (2-4 sentences) as a recast "
        "sandwich: first acknowledge what genuinely worked, then gently recast "
        "the single most important error by modelling the correct form (do not "
        "scold or just label it wrong), then set the next small production task. "
        "End with the task."
    )


def build_bridge_prompt(
    node: CommNode,
    messages: list[dict],
    diagnosis: dict,
    memory_context: str,
    coach: dict | None = None,
) -> str:
    return (
        f"{TUTOR_PERSONA}\n"
        f"{_memory_block(memory_context)}\n"
        f"{_coach_block(coach)}"
        f"Skill: {node.skill}\n"
        f"Easier sub-step to scaffold down to: {node.bridge_focus}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"Your read of their last answer: {diagnosis}\n\n"
        "The learner is struggling. Do NOT repeat the full task harder. Break "
        "it into the smaller sub-step above. Reassure briefly, model one tiny "
        "example, then ask them to do just the smaller step. End with the task."
    )


def build_strengthen_prompt(
    node: CommNode,
    messages: list[dict],
    diagnosis: dict,
    memory_context: str,
    coach: dict | None = None,
) -> str:
    return (
        f"{TUTOR_PERSONA}\n"
        f"{_memory_block(memory_context)}\n"
        f"{_coach_block(coach)}"
        f"Skill: {node.skill}\nSuccess looks like: {node.success_criteria}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"Your read of their last answer: {diagnosis}\n\n"
        "The skill is shaky but present. Reinforce it as a recast sandwich: name "
        "what worked, gently model the one weak spot correctly, give a quick tip, "
        "then ask them to try a close variant of the same task. End with the task."
    )


def build_challenge_prompt(
    node: CommNode,
    messages: list[dict],
    diagnosis: dict,
    memory_context: str,
    coach: dict | None = None,
) -> str:
    return (
        f"{TUTOR_PERSONA}\n"
        f"{_memory_block(memory_context)}\n"
        f"{_coach_block(coach)}"
        f"Skill (now near-mastered): {node.skill}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"Your read of their last answer: {diagnosis}\n\n"
        "The learner is near mastery. Celebrate the win briefly, then push them: "
        "give a harder, more realistic variant of the task that stretches the "
        "same skill. Keep it to 2-3 sentences. End with the harder task."
    )


def build_redirect_prompt(
    node: CommNode,
    messages: list[dict],
    diagnosis: dict,
    memory_context: str,
    coach: dict | None = None,
) -> str:
    return (
        f"{TUTOR_PERSONA}\n"
        f"{_memory_block(memory_context)}\n"
        f"{_coach_block(coach)}"
        f"Skill being practised: {node.skill}\n"
        f"The task / success criteria: {node.success_criteria}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"Your read of their last answer: {diagnosis}\n\n"
        "The learner wrote fluent English but answered a DIFFERENT question — "
        "they did not attempt this skill. Do NOT scold and do NOT scaffold down "
        "(they are clearly capable). Warmly acknowledge what they said in one "
        "line, then steer them back: restate the actual task in one clear "
        "sentence and ask them to try THAT now. End with the task."
    )


def build_ease_prompt(
    node: CommNode,
    messages: list[dict],
    diagnosis: dict,
    memory_context: str,
    coach: dict | None = None,
) -> str:
    return (
        f"{TUTOR_PERSONA}\n"
        f"{_memory_block(memory_context)}\n"
        f"{_coach_block(coach)}"
        f"Skill: {node.skill}\n"
        f"Easiest sub-step: {node.bridge_focus}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"Your read of their last answer: {diagnosis}\n\n"
        "The learner has struggled here many times and may be losing heart. Stop "
        "drilling. Lead with genuine, specific reassurance, take the pressure "
        "fully off, and offer an off-ramp: either a much tinier win (one word or "
        "phrase to copy and tweak) or the choice to move on and revisit this "
        "later. Make them feel safe and capable. End by giving them that easy "
        "choice or tiny task."
    )


# ---------- end-of-session summary (for memory write + learner audit) ----------

def build_summary_prompt(node: CommNode, messages: list[dict]) -> str:
    return (
        "Write a short, warm end-of-session note for the learner in <=180 "
        "tokens. It doubles as a memory note for the next session, so name "
        "things precisely. Write in the second person (\"you\"). Output EXACTLY "
        "three labelled lines and nothing else:\n"
        "Strengths: <1-2 things they did well>\n"
        "Watch: <1-2 recurring errors to keep an eye on>\n"
        "Next focus: <the single concept to revisit first next time, named "
        "precisely so it can be re-tested in a warm-up>\n\n"
        f"Skill worked on: {node.skill}\n\n"
        f"Conversation:\n{_history_block(messages, limit=40)}"
    )

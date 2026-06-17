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
from app.ai.behaviors import BehaviorPack
from app.content.schema import Concept

TUTOR_PERSONA = (
    "You are Zidd, a warm, sharp personal communication coach — the kind of "
    "teacher who remembers a learner, celebrates small wins, and never makes "
    "anyone feel slow. You teach spoken and written English for interviews, "
    "group discussions, and school English. You are concise and encouraging, "
    "never lecture more than a few sentences before asking the learner to "
    "produce language, and you always speak directly TO the learner. "
    "IMPORTANT: This is a TEXT-ONLY chat interface. You CANNOT show pictures, "
    "flashcards, or point to anything. Do NOT ask the learner to 'find', 'point to', "
    "or 'look at' a letter or image. Structure all tasks for a text-only medium."
)


def _history_block(messages: list[dict], limit: int = 8) -> str:
    if not messages:
        return "(no prior turns)"
    recent = messages[-limit:]
    lines = [f"{m['role']}: {m['content']}" for m in recent]
    return "\n".join(lines)


def _memory_block(
    memory_context: "list[dict] | str", weaknesses: list | None = None
) -> str:
    """Render felt continuity: past summaries + named, aggregated weaknesses.

    `memory_context` is a list of structured dicts (from load_context), each
    with keys: node_id, score, strengths, watch, next_focus, date, raw.
    Legacy str (§-delimited) is still accepted for backward compat.
    Empty memory AND no weaknesses -> "".
    """
    parts = []

    sessions: list = []
    if isinstance(memory_context, list):
        sessions = [r for r in memory_context if r]
    elif isinstance(memory_context, str) and memory_context.strip():
        # Legacy plain-text path: parse §-chunks into minimal dicts
        for chunk in memory_context.split("§"):
            chunk = chunk.strip()
            if not chunk:
                continue
            parsed: dict[str, str] = {"raw": chunk}
            for line in chunk.splitlines():
                if line.startswith("Strengths:"):
                    parsed["strengths"] = line[len("Strengths:"):].strip()
                elif line.startswith("Watch:"):
                    parsed["watch"] = line[len("Watch:"):].strip()
                elif line.startswith("Next focus:"):
                    parsed["next_focus"] = line[len("Next focus:"):].strip()
            sessions.append(parsed)

    if sessions:
        lines = [
            "\nPRIOR SESSION MEMORY — you MUST reference at least one specific "
            "fact from these in your first response (name what they did well or "
            "struggled with):"
        ]
        for i, row in enumerate(sessions, 1):
            label = "Most recent session" if i == 1 else f"{i} sessions ago"
            node = row.get("node_id", "")
            score = row.get("score")
            strengths = row.get("strengths", "").strip()
            watch = row.get("watch", "").strip()
            next_focus = row.get("next_focus", "").strip()
            date = row.get("date", "")
            if strengths or watch or next_focus:
                score_str = f" (score {score:.2f})" if score else ""
                node_str = f" [{node}{score_str}]" if node else ""
                detail = (
                    f"STRENGTHS: {strengths or 'n/a'} | "
                    f"WATCH: {watch or 'n/a'} | "
                    f"NEXT FOCUS: {next_focus or 'n/a'}"
                )
                date_str = f" on {date}" if date else ""
                lines.append(f"  [{label}{date_str}]{node_str} {detail}")
            else:
                lines.append(f"  [{label}] {row.get('raw', '')}")
        parts.append("\n".join(lines) + "\n")

    rows = weaknesses or []
    if rows:
        lines = ["\nKnown weak spots (target these, do not read them aloud):"]
        for w in rows:
            skill = w.get("skill_id", "OTHER")
            hits = w.get("hit_count", 0)
            raw = (w.get("last_raw") or "").strip()
            tail = f' — e.g. "{raw}"' if raw else ""
            lines.append(f"- {skill} (seen {hits}x){tail}")
        parts.append("\n".join(lines) + "\n")
    return "".join(parts)


# ---------- personalization (the "personal teacher" layer) ----------

def coach_view(state: dict) -> dict:
    """Project canonical state into the small dict the coach block renders.

    Pulled from service-owned keys (set in session_service._new_state /
    _update_progress). Safe defaults so a bare state still renders."""
    # Imported lazily: route.py is import-light, but keep coach_view free of any
    # module-load ordering assumptions.
    from app.graph.route import level_kind

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
        "frustration_turns": state.get("frustration_turns", 0),
        # C20: a 'confident' affect was read by the evaluator but dropped here.
        # Surface it so the coach can stretch instead of over-praising.
        "confident": affect == "confident",
        # A7: which section the learner is in (prep/bridge/review/tester/test) and
        # whether this is remediation — both were computed but never reached the
        # coach, so re-teaching read identically to first-time teaching.
        "level_kind": level_kind(state),
        "remediation": bool(state.get("remediation", False)),
    }


def _coach_block(coach: dict | None) -> str:
    """Render private coaching directives. The model acts on these; it must
    never read them aloud. Empty string when there is nothing to personalize."""
    if not coach:
        return ""
    parts: list[str] = []
    name = coach.get("name")
    if name:
        # Directive phrasing: "MUST" forces qwen to comply, not treat it as optional.
        parts.append(
            f"The learner's name is {name}. You MUST address them as {name} at least "
            "once in this response — not 'you', not 'the learner', their actual name."
        )
    streak = coach.get("clean_streak", 0)
    need = coach.get("advance_streak", 2)
    parts.append(
        f"Progress: {streak} of {need} clean passes at this level. When they do "
        "well, name how close they are to the next level — make the win visible."
    )
    if coach.get("support"):
        parts.append(
            "They sound discouraged or frustrated. Lead with genuine reassurance, "
            "lower the stakes, shrink the task, and make this turn easily winnable. "
            "Do NOT jump straight into the exercise — acknowledge how they feel "
            "first, in one warm sentence, before giving any instruction. "
            "If the previous turn ALSO flagged frustration, explicitly check in: "
            "'Are you feeling a bit better now?' before continuing."
        )
    ft = coach.get("frustration_turns", 0)
    if ft > 0:
        parts.append(
            f"This learner has been frustrated or confused for {ft} consecutive turn(s). "
            "Explicitly acknowledge their effort: name something specific they did right "
            "even if the answer was wrong (e.g. 'You picked the right structure, just the "
            "tense slipped'). Make them feel seen before moving forward."
        )
    if coach.get("scaffold", 0) >= 1:
        parts.append(
            "They have struggled repeatedly here. Scaffold HARD: model a "
            "near-complete answer and ask them only to fill one blank or copy and "
            "lightly change it. Make success almost automatic, then build up."
        )
    # C20: confident affect — do not over-praise; stretch them.
    if coach.get("confident"):
        parts.append(
            "They sound confident and in command. Do NOT over-praise — that flattens "
            "the challenge. Acknowledge briefly, then raise the bar: stretch them with "
            "a harder angle, a sharper constraint, or a deeper follow-up."
        )
    # A7: remediation / bridge framing — this is a REVISIT, not first contact.
    if coach.get("remediation") or coach.get("level_kind") == "bridge":
        parts.append(
            "This is remediation: they have seen this material before and it did not "
            "stick. Frame it as revisiting, not first teaching — name what tripped "
            "them up last time, slow down, and rebuild the weak spot before moving on."
        )
    return (
        "Coaching directives (act on these, never read them aloud):\n- "
        + "\n- ".join(parts)
        + "\n\n"
    )


# ---------- behavior pack (per-TaskType voice + stance) ----------

def _persona(behavior: BehaviorPack | None) -> str:
    """The voice header: the pack's persona, or the legacy single voice."""
    return behavior.persona if behavior is not None else TUTOR_PERSONA


def _stance_block(behavior: BehaviorPack | None) -> str:
    """Pedagogy + rubric + output-style guidance from the pack. Empty when no
    pack (back-compat: legacy callers get the old single-voice prompt)."""
    if behavior is None:
        return ""
    return (
        f"How to teach here: {behavior.pedagogy}\n"
        f"What to weight most: {behavior.rubric_emphasis}\n"
        f"Output style: {behavior.output_style}\n\n"
    )


def _strictness_gate(behavior: BehaviorPack | None) -> str:
    """Tighten/loosen the evaluator's language gate per the pack's strictness.
    'standard' (and no pack) leaves the base rubric unchanged."""
    if behavior is None:
        return ""
    s = behavior.language_strictness
    if s == "strict":
        return (
            "\nGrading stance: hold a HIGH BAR. This is an assessment, not "
            "coaching — minor errors cost credit and you do not award marks for "
            "effort alone. Do not be generous.\n"
        )
    if s == "lenient":
        return (
            "\nGrading stance: be GENEROUS with a young learner's attempt. "
            "Reward effort and the target skill for the grade level; do not "
            "penalise simple vocabulary or small slips.\n"
        )
    return ""


# ---------- evaluate (structured) ----------

def build_eval_prompt(
    node: Concept,
    messages: list[dict],
    user_input: str,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
) -> str:
    return (
        f"{_persona(behavior)}\n"
        f"{_strictness_gate(behavior)}\n"
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
        "Worked example (do not praise broken English): an answer like \"me name "
        "rahul, i is go office daily\" is code-mixed / broken English — the "
        "grammar fails repeatedly, so it scores at most 0.3 and english=false. "
        "Being partly in English is NOT enough; the language itself must be "
        "competent. Do not call broken or code-mixed English good.\n"
        "Also report these three flags so the coach can respond correctly even "
        "when the score is 0.0 — they do NOT change the score:\n"
        "- on_task: true if the answer genuinely ATTEMPTS the skill above; false "
        "if it is about something else, changes the subject, argues, or ignores "
        "the task. A fluent answer to the WRONG question is on_task=false.\n"
        "- english: true if it is competent English; false if it is empty, "
        "gibberish, only emoji/symbols, or not in English.\n"
        "- affect: the learner's emotional tone — one of neutral, frustrated, "
        "confident, confused.\n"
        "- goodbye: true if the learner is clearly ending the session (e.g. 'I need "
        "to go', 'see you tomorrow', 'I'm done for today', 'talk later', 'bye'); "
        "false for anything that could be a task answer or question.\n"
        "Calibration examples (apply the same SCALE to whatever skill you are "
        "assessing — do not copy-paste these scores blindly):\n"
        "  score 0.9 — 'I'm Priya, a software analyst at TechCorp. I've been there "
        "two years and focus on backend systems.' Fluent, complete, confident, every "
        "part of the skill demonstrated.\n"
        "  score 0.7 — 'My name is Priya and I work at a software company.' Clear "
        "and correct, meets the criteria, minor vocabulary gap but no error that "
        "blocks comprehension.\n"
        "  score 0.5 — 'I am Priya. Work software.' Attempted the skill, shows the "
        "idea, but structurally incomplete — misses key parts of the success "
        "criteria.\n"
        "  score 0.2 — 'Me name Priya, I is go office.' Broken English throughout; "
        "the skill attempt is present but the language fails so badly it barely "
        "communicates.\n"
        "Return JSON with:\n"
        "- score: 0.0-1.0 on the scale above\n"
        "- understanding: one line on what they grasped\n"
        "- errors: list of concrete mistakes (empty list if none)\n"
        "- strengths: list of what they did well (empty list if none)\n"
        "- next_focus: the single most useful thing to improve next\n"
        "- on_task: boolean as defined above\n"
        "- english: boolean as defined above\n"
        "- affect: neutral | frustrated | confident | confused\n"
        "- goodbye: boolean as defined above"
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


# ---------- simulation scoring (structured, end of a TEST session) ----------

def build_simulation_score_prompt(
    behavior: BehaviorPack | None,
    topic: str,
    messages: list[dict],
) -> str:
    """Score a whole TEST-mode simulation transcript at the end.

    Unlike build_eval_prompt (one answer), this judges the learner's WHOLE
    contribution across the session — their stance, evidence, and handling of
    pressure — and returns the deferred feedback that was withheld mid-stream.
    """
    return (
        f"{_persona(behavior)}\n"
        f"{_strictness_gate(behavior)}\n"
        f"Topic of the session: {topic}\n\n"
        f"Full transcript (assistant lines are the simulated participants / "
        f"interviewer; user lines are the learner being assessed):\n"
        f"{_history_block(messages, limit=40)}\n\n"
        "Score ONLY the learner's contribution across the whole session, not the "
        "simulated voices. Judge what this task weights most. Use this anchored "
        "scale:\n"
        "- 0.7 means a solid, assessment-passing contribution overall.\n"
        "- 0.85+ means consistently strong: clear stance, concrete evidence, "
        "composed under pressure.\n"
        "- 0.5 means partial — some good moments but notable gaps.\n"
        "- below 0.4 means it failed to engage the task, was off-topic, or was "
        "not competent English.\n"
        "This is an ENGLISH assessment: contributions not in competent English "
        "cannot pass. Do not award credit for effort alone.\n"
        "For GD sessions also rate three sub-dimensions (0.0-1.0 each); set all "
        "three to 0.0 for interview sessions:\n"
        "- participation_score: did the learner claim the floor, interject, hold "
        "their space? 0.7+ means they spoke up and did not let others dominate.\n"
        "- relevance_score: did contributions stay on topic, build a coherent "
        "argument, and reference others' points? 0.7+ means consistently on-task.\n"
        "- language_score: fluency, grammar, and vocabulary under the pressure of "
        "a live discussion. 0.7+ means fluent with minor slips only.\n"
        "For interview sessions also rate two sub-dimensions (0.0-1.0 each); set "
        "both to 0.0 for GD sessions:\n"
        "- clarity_score: how clearly and concisely the learner answered — "
        "structured response, no waffle, concrete examples. 0.7+ means clear.\n"
        "- confidence_score: composure under pressure — steady delivery, no "
        "excessive hedging, handles follow-ups without deflecting. 0.7+ means "
        "composed.\n"
        "Return JSON with:\n"
        "- score: 0.0-1.0 on the scale above\n"
        "- summary: one short paragraph the learner can read\n"
        "- strengths: list of what genuinely landed (empty list if none)\n"
        "- improvements: list of the few most useful things to work on next\n"
        "- participation_score: 0.0-1.0\n"
        "- relevance_score: 0.0-1.0\n"
        "- language_score: 0.0-1.0\n"
        "- clarity_score: 0.0-1.0\n"
        "- confidence_score: 0.0-1.0"
    )


def build_test_gen_prompt(
    behavior: BehaviorPack | None,
    weaknesses: list | None,
    n_items: int = 4,
) -> str:
    """Generate a bank of assessment probe items for a TEST-mode session.

    The items are produced before the session so the simulated panel/interviewer
    has ready material. When the learner has logged prep weaknesses, the prompt
    names them so generated items concentrate exactly where they struggled;
    otherwise it asks for a balanced spread across the task's core skills.
    """
    weaknesses = weaknesses or []
    if weaknesses:
        lines = []
        for w in weaknesses[:4]:
            skill = w.get("skill_id", "")
            raw = (w.get("last_raw") or "").strip()
            lines.append(f"- {skill}: {raw}" if raw else f"- {skill}")
        weakness_block = (
            "The learner has these logged weaknesses from their prep coaching. "
            "Concentrate the items here so the assessment presses exactly where "
            "they struggle:\n" + "\n".join(lines) + "\n\n"
        )
    else:
        weakness_block = (
            "No prep history for this learner — produce a balanced spread across "
            "this task's core skills.\n\n"
        )
    return (
        f"{_persona(behavior)}\n"
        f"{_strictness_gate(behavior)}\n"
        f"{weakness_block}"
        f"Produce exactly {n_items} assessment probe items for this task. Each "
        "item must make the learner produce real spoken/written English under "
        "assessment conditions — a question, debate motion, or scenario.\n"
        "Return JSON with an `items` list; each item has:\n"
        "- skill_id: the single skill it probes (use the learner's listed skill "
        "ids where they apply)\n"
        "- prompt: the exact question / motion / scenario shown to the learner\n"
        "- aim: one short line on what a strong answer demonstrates"
    )


# ---------- pedagogy generations (streamed) ----------

def build_opening_prompt(
    node: Concept,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
) -> str:
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_stance_block(behavior)}"
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
    node: Concept,
    messages: list[dict],
    diagnosis: dict,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
) -> str:
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_stance_block(behavior)}"
        f"Skill: {node.skill}\nTeaching focus: {node.teach_focus}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"Your read of their last answer: {diagnosis}\n\n"
        "Give a short, targeted teaching move (2-4 sentences) as a recast "
        "sandwich: first acknowledge what genuinely worked, then gently recast "
        "the single most important error by modelling the correct form (do not "
        "scold or just label it wrong), then set the next small production task. "
        "End with the task."
    )


def build_teach_game_prompt(
    node: "Concept",
    diagnosis: dict,
    coach: dict | None = None,
) -> str:
    """Prompt for the gamified teach path (scaffold >= 1).

    Asks qwen to return a single JSON object conforming to FillBlankGame.
    The prompt is intentionally minimal — no conversation history, no persona
    preamble — so qwen spends its token budget on the structured output, not
    prose framing. Instructions live here (not in schema field descriptions)
    to comply with the Flash-Lite council rule."""
    coach_text = _coach_block(coach)
    focus = diagnosis.get("next_focus") or node.teach_focus
    errors = diagnosis.get("errors", [])
    error_line = (
        f"\nTop mistake to fix: {errors[0]}" if errors else ""
    )
    return (
        f"{coach_text}"
        f"Skill: {node.skill}\n"
        f"Teaching focus: {focus}{error_line}\n\n"
        "Return a single JSON object for a fill-in-the-blank practice item.\n"
        "Fields (all required):\n"
        '  "sentence": one complete, natural sentence with exactly one ___ gap\n'
        '  "hint": short grammar or vocab category label (e.g. "past simple verb") '
        "— do NOT put the answer here\n"
        '  "answer_key": the word or phrase that correctly fills the gap\n'
        '  "context": one line explaining why this gap targets the teaching focus\n\n'
        "Rules:\n"
        "- The gap must target ONLY the top mistake or teaching focus listed above.\n"
        "- The sentence must feel natural and realistic, not textbook-dry.\n"
        "- The hint must name the category, not hint at the spelling of the answer.\n"
        "- Return ONLY the JSON object — no prose, no markdown fences, no keys "
        "outside the four listed.\n"
        "Return the JSON now."
    )


def build_bridge_prompt(
    node: Concept,
    messages: list[dict],
    diagnosis: dict,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
) -> str:
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_stance_block(behavior)}"
        f"Skill: {node.skill}\n"
        f"Easier sub-step to scaffold down to: {node.bridge_focus}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"Your read of their last answer: {diagnosis}\n\n"
        "The learner is struggling. Do NOT repeat the full task harder. Break "
        "it into the smaller sub-step above. Reassure briefly, model one tiny "
        "example, then ask them to do just the smaller step. End with the task."
    )


def build_strengthen_prompt(
    node: Concept,
    messages: list[dict],
    diagnosis: dict,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
) -> str:
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_stance_block(behavior)}"
        f"Skill: {node.skill}\nSuccess looks like: {node.success_criteria}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"Your read of their last answer: {diagnosis}\n\n"
        "The skill is shaky but present. Reinforce it as a recast sandwich: name "
        "what worked, gently model the one weak spot correctly, give a quick tip, "
        "then ask them to try a close variant of the same task. End with the task."
    )


def build_challenge_prompt(
    node: Concept,
    messages: list[dict],
    diagnosis: dict,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
) -> str:
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_stance_block(behavior)}"
        f"Skill (now near-mastered): {node.skill}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"Your read of their last answer: {diagnosis}\n\n"
        "The learner is near mastery. Celebrate the win briefly, then push them: "
        "give a harder, more realistic variant of the task that stretches the "
        "same skill. Keep it to 2-3 sentences. End with the harder task."
    )


def build_redirect_prompt(
    node: Concept,
    messages: list[dict],
    diagnosis: dict,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
) -> str:
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_stance_block(behavior)}"
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


def build_clarify_prompt(
    node: Concept,
    messages: list[dict],
    diagnosis: dict,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
) -> str:
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_stance_block(behavior)}"
        f"Skill being practised: {node.skill}\n"
        f"The task / success criteria: {node.success_criteria}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"Your read of their last answer: {diagnosis}\n\n"
        "The learner's last message was not in clear English (it may be another "
        "language, empty, or unreadable). Do NOT scold, do NOT scaffold the skill "
        "down, and do NOT guess what they meant. Assume good faith. In one warm "
        "sentence say you want to make sure you understand them, then ask them to "
        "say it again in English. Briefly restate the task in one simple sentence "
        "so they know what to answer. End with that ask."
    )


def build_ease_prompt(
    node: Concept,
    messages: list[dict],
    diagnosis: dict,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
) -> str:
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_stance_block(behavior)}"
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

def build_summary_prompt(node: Concept, messages: list[dict]) -> str:
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

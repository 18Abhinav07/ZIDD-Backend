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
import json
import re

from app.ai.behaviors import BehaviorPack, behavior_for
from app.content.schema import Concept
from app.content.task_types import TaskType

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


# Byte budget for the two whole-transcript builders (score + summary). Sized for a
# local model's context: ~6k chars of transcript leaves room for the instructions.
_HISTORY_CHAR_BUDGET = 6000


_MEMORY_COPYABLE_ANSWER_RE = re.compile(
    r"\b(?:a\s+better|a\s+stronger|the\s+better|the\s+stronger)\s+version\s+would\s+be:?\s*"
    r"(?:\"[^\"]+\"|'[^']+'|[^.?!]+[.?!])",
    re.I,
)
_MEMORY_TRY_SAYING_RE = re.compile(
    r"\b(?:try\s+saying|you\s+can\s+say|say\s+it\s+like\s+this):?\s*"
    r"(?:\"[^\"]+\"|'[^']+'|[^.?!]+[.?!])",
    re.I,
)
_MEMORY_PRAISE_OPENING_RE = re.compile(
    r"^\s*(?:great\s+job|great\s+session|well\s+done|excellent|strong\s+answer|"
    r"strong\s+interview\s+close|solid\s+answer|nice\s+work)\b"
    r"[^.?!]*(?:[.?!]\s*)?",
    re.I,
)
_MEMORY_ALL_RIGHT_RE = re.compile(
    r"\byou\s+(?:hit|covered)\s+all\s+(?:of\s+)?the\s+right\s+points\b[^.?!]*(?:[.?!])?",
    re.I,
)
_MEMORY_GENERIC_PRAISE_RE = re.compile(
    r"\b(?:great\s+job|great\s+session|strong\s+answer|strong\s+interview\s+close|"
    r"well\s+done|excellent|nice\s+work)\b",
    re.I,
)
_MEMORY_READY_CLAIM_RE = re.compile(
    r"\b(?:you(?:'re| are)?\s+)?ready(?:\s+(?:for|to)\b[^.?!]*)?(?:[.?!])?",
    re.I,
)
_MEMORY_MASTERY_CLAIM_RE = re.compile(
    r"\b(?:you(?:'ve| have| are)?\s+)?(?:mastered|mastery)\b[^.?!]*(?:[.?!])?",
    re.I,
)


def _sanitize_memory_text(value: object) -> str:
    """Remove praise/model-answer residue before memory is injected into prompts."""
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return ""
    text = _MEMORY_COPYABLE_ANSWER_RE.sub(
        "Use the learner's own facts to add the missing result or evidence.",
        text,
    )
    text = _MEMORY_TRY_SAYING_RE.sub(
        "Ask for a revision using the learner's own facts.",
        text,
    )
    text = _MEMORY_PRAISE_OPENING_RE.sub("", text)
    text = _MEMORY_ALL_RIGHT_RE.sub("The answer had usable material.", text)
    text = _MEMORY_GENERIC_PRAISE_RE.sub("The answer had usable material.", text)
    text = _MEMORY_READY_CLAIM_RE.sub("Keep re-testing before advancing.", text)
    text = _MEMORY_MASTERY_CLAIM_RE.sub("Keep re-testing before calling this sustained mastery.", text)
    return " ".join(text.split()).strip()


def sanitize_memory_text(value: object) -> str:
    """Public wrapper for service code that persists or replays learner memory."""
    return _sanitize_memory_text(value)


def _history_block(
    messages: list[dict], limit: int = 8, max_chars: int | None = None
) -> str:
    if not messages:
        return "(no prior turns)"
    recent = messages[-limit:]
    lines = [f"{m['role']}: {m['content']}" for m in recent]
    # Optional size budget for the large-context builders (whole-session score,
    # memory summary) that pass limit=40: a turn count alone does not bound bytes,
    # and 40 long turns can overflow a local model. Drop the OLDEST lines until the
    # block fits, keeping the most recent context the grader/summarizer needs most.
    if max_chars is not None:
        while len(lines) > 1 and len("\n".join(lines)) > max_chars:
            lines.pop(0)
    return "\n".join(lines)


def _clean_prompt_list(values: object, *, limit: int = 4, item_limit: int = 140) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = " ".join(str(value or "").split()).strip()
        if not text:
            continue
        text = _sanitize_memory_text(text)[:item_limit]
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) >= limit:
            break
    return out


def _hot_delta_prompt_view(state: dict) -> dict:
    task_type = str(state.get("task_type") or "")
    node_id = str(state.get("competency_node") or "")
    if task_type not in {TaskType.INTERVIEW_PREP.value, TaskType.GD_PREP.value}:
        return {}
    if not (node_id.startswith("int_") or node_id.startswith("gd_")):
        return {}
    delta = state.get("session_learning_delta")
    if not isinstance(delta, dict):
        return {}
    delta_module = str(delta.get("module_id") or "").strip()
    if delta_module and delta_module != str(state.get("module_id") or "").strip():
        return {}
    delta_task = str(delta.get("task_type") or "").strip()
    if delta_task and delta_task != task_type:
        return {}
    repeated_raw = delta.get("repeated_issue_counts")
    repeated: dict[str, int] = {}
    if isinstance(repeated_raw, dict):
        for key, value in list(repeated_raw.items())[:5]:
            text = _sanitize_memory_text(key)[:120]
            if not text:
                continue
            try:
                count = int(value)
            except (TypeError, ValueError):
                continue
            if count > 0:
                repeated[text] = count
    view = {
        "active_gaps": _clean_prompt_list(delta.get("active_gaps"), limit=3),
        "growth_signals": _clean_prompt_list(delta.get("growth_signals"), limit=3),
        "resolved_candidates": _clean_prompt_list(delta.get("resolved_candidates"), limit=3),
        "latest_evidence_quotes": _clean_prompt_list(delta.get("latest_evidence_quotes"), limit=2),
        "repeated_issue_counts": repeated,
    }
    return view if any(view.values()) else {}


def _career_context_for_node(node: "Concept", career_context: dict | None) -> dict:
    if not career_context:
        return {}
    scoped = dict(career_context)
    node_id = str(getattr(node, "id", "") or "")
    if node_id.startswith("int_"):
        scoped.pop("gd_topics", None)
        scoped.pop("custom_gd_topics", None)
        primary_role = str(scoped.get("primary_role") or "").strip()
        if primary_role:
            scoped["target_roles"] = [primary_role]
    elif node_id.startswith("gd_"):
        scoped.pop("interview_goals", None)
    return scoped


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
            strengths = _sanitize_memory_text(row.get("strengths", ""))
            watch = _sanitize_memory_text(row.get("watch", ""))
            next_focus = _sanitize_memory_text(row.get("next_focus", ""))
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
                raw = _sanitize_memory_text(row.get("raw", ""))
                if raw:
                    lines.append(f"  [{label}] {raw}")
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

    diagnosis = state.get("last_diagnosis") or {}
    affect = diagnosis.get("affect", "neutral")
    has_recent_eval = bool(diagnosis) or bool(state.get("last_turn_affect"))
    recent_score = None
    if has_recent_eval:
        recent_score = state.get("last_clean_pass_score", state.get("last_eval_score"))
    scaffolded_recovery = bool(state.get("last_graded_bridge"))
    return {
        "name": (state.get("learner_name") or "").strip(),
        "clean_streak": state.get("clean_streak", 0),
        "advance_streak": state.get("advance_streak", 2),
        "scaffold": state.get("scaffold", 0),
        "recent_score": recent_score,
        "scaffolded_recovery": scaffolded_recovery,
        # Support fires on the regex frustration flag OR a frustrated/discouraged
        # affect read from the diagnosis (council fix #5).
        "support": bool(state.get("needs_support", False))
        or affect in ("frustrated", "discouraged"),
        "frustration_turns": state.get("frustration_turns", 0),
        # C20: a 'confident' affect was read by the evaluator but dropped here.
        # Surface it so the coach can stretch instead of over-praising.
        "confident": affect == "confident" and not scaffolded_recovery,
        # A7: which section the learner is in (prep/bridge/review/tester/test) and
        # whether this is remediation — both were computed but never reached the
        # coach, so re-teaching read identically to first-time teaching.
        "level_kind": level_kind(state),
        "remediation": bool(state.get("remediation", False)),
        "tutor_turn_plan": state.get("tutor_turn_plan") or {},
        "hot_session_delta": _hot_delta_prompt_view(state),
    }


def _coach_block(coach: dict | None) -> str:
    """Render private coaching directives. The model acts on these; it must
    never read them aloud. Empty string when there is nothing to personalize."""
    if not coach:
        return ""
    # Lead with the anti-template rule: the old block forced a name + a progress
    # count on EVERY turn, so qwen opened nearly every reply the same way.
    parts: list[str] = [
        "Vary how you open: do NOT start every reply the same way (praise + their "
        "name + the progress count). Lead differently each turn — sometimes react "
        "to what they just said, sometimes go straight into the task."
    ]
    name = coach.get("name")
    if name:
        # Use the name for warmth, but NOT as a forced every-turn opener — the old
        # "MUST address them once" directive made qwen start nearly every reply with
        # the name, which reads as a template. Let it land naturally instead.
        parts.append(
            f"The learner's name is {name}. Use their name naturally where it fits "
            "to keep things personal — not in every line, and not as a forced "
            "opener; plain 'you' is fine most of the time."
        )
    tutor_plan = coach.get("tutor_turn_plan") if isinstance(coach.get("tutor_turn_plan"), dict) else {}
    plan_verdict = str(tutor_plan.get("verdict") or "").strip()
    if tutor_plan:
        next_action = str(tutor_plan.get("next_action") or "").strip()
        focus = str(tutor_plan.get("focus") or "").strip()
        stage = str(tutor_plan.get("stage") or "").strip()
        tone_policy = str(tutor_plan.get("tone_policy") or "").strip()
        parts.append(
            "Latest enforced tutor plan: "
            f"verdict={plan_verdict or 'unknown'}, "
            f"next_action={next_action or 'continue'}, "
            f"stage={stage or 'practice'}, "
            f"tone_policy={tone_policy or 'measured'}, "
            f"focus={focus or 'continue the active skill'}."
        )
        if plan_verdict == "independent_pass":
            parts.append(
                "The required criteria are already covered. Do NOT ask for missing "
                "required evidence, do NOT request another same-skill rewrite, and "
                "do NOT imply the answer failed. Give measured feedback, then set "
                "one delivery, transfer, pressure, or polishing task based on the "
                "tutor plan focus."
            )
        elif plan_verdict in {"partial", "not_yet"}:
            parts.append(
                "A required part is still missing. Keep the feedback corrective and "
                "specific: name only the missing criterion from the tutor plan focus "
                "and ask for one targeted revision."
            )
        elif plan_verdict == "guided_success":
            parts.append(
                "This was scaffolded success, not mastery. Rebuild the same skill "
                "without the scaffold and avoid celebratory mastery language."
            )
    hot_delta = coach.get("hot_session_delta") if isinstance(coach.get("hot_session_delta"), dict) else {}
    if hot_delta:
        hot_parts: list[str] = ["Hot session learning delta"]
        active_gaps = hot_delta.get("active_gaps") if isinstance(hot_delta.get("active_gaps"), list) else []
        growth = hot_delta.get("growth_signals") if isinstance(hot_delta.get("growth_signals"), list) else []
        quotes = (
            hot_delta.get("latest_evidence_quotes")
            if isinstance(hot_delta.get("latest_evidence_quotes"), list)
            else []
        )
        repeated = (
            hot_delta.get("repeated_issue_counts")
            if isinstance(hot_delta.get("repeated_issue_counts"), dict)
            else {}
        )
        if active_gaps:
            hot_parts.append("active gaps: " + "; ".join(active_gaps[:3]))
        if repeated:
            pairs = [
                f"{str(key)} x{int(value)}"
                for key, value in list(repeated.items())[:3]
                if str(key).strip()
            ]
            if pairs:
                hot_parts.append("repeated gaps: " + "; ".join(pairs))
        if growth:
            hot_parts.append("growth signals: " + "; ".join(growth[:3]))
        if quotes:
            hot_parts.append("latest evidence: " + "; ".join(quotes[:2]))
        hot_parts.append(
            "Use this same-session evidence to choose the next micro-task, but "
            "do not call this mastery and do not read these private notes aloud."
        )
        parts.append(" | ".join(hot_parts))
    streak = coach.get("clean_streak", 0)
    need = coach.get("advance_streak", 2)
    # Only surface progress once a streak has actually started. Telling a fresh or
    # struggling learner "0 of 2" every single turn was the other half of the
    # formulaic opener. Near the threshold, make the win visible; mid-streak,
    # mention it only on a genuinely good turn.
    if streak > 0:
        if streak >= need - 1:
            parts.append(
                f"Progress: {streak} of {need} clean passes — they are one clean "
                "pass from the next level. When they nail this turn, make that win "
                "visible."
            )
        else:
            parts.append(
                f"Progress: {streak} of {need} clean passes at this level. When they "
                "do well, name how close they are — only when it's genuinely earned."
            )
    recent_score = coach.get("recent_score")
    if isinstance(recent_score, (int, float)) and recent_score < 0.7:
        parts.append(
            "The last answer was weak or partial. Do NOT open with celebratory "
            "praise such as 'Great job', 'Well done', 'Excellent', 'Awesome', "
            "or 'You nailed it'. Use correction first: name the one specific gap, "
            "then give one small next step. If you acknowledge effort, make it "
            "specific and separate from answer quality."
        )
    elif (
        isinstance(recent_score, (int, float))
        and recent_score < 0.85
        and plan_verdict != "independent_pass"
    ):
        parts.append(
            "The last answer was a borderline pass, not a polished answer. Do not "
            "open with celebratory praise such as 'Great job', 'Great start', "
            "'Well done', 'Excellent', 'Awesome', or 'You nailed it'. Say it is "
            "on the right track, then name the one missing quality that would make "
            "it strong. Do not give a complete sample answer or copyable sentence; "
            "ask the learner to revise in their own words."
        )
    if coach.get("scaffolded_recovery"):
        parts.append(
            "The last response was a correct scaffolded bridge answer, not a full "
            "clean pass. Do not open with celebratory praise such as 'Great job', "
            "'Great start', 'Well done', 'Excellent', 'Awesome', or 'You nailed it'. "
            "Acknowledge the recovery briefly, but do not frame it as mastery or "
            "say they nailed the whole skill. Use the next turn to rebuild the same "
            "skill without the scaffold. Do not give a near-complete answer, sample "
            "answer, or copyable sentence for the active task; ask them to produce "
            "their own full response."
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
    if coach.get("scaffold", 0) >= 1 and not coach.get("scaffolded_recovery"):
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


def _career_context_block(career_context: dict | None) -> str:
    """Render private career personalization without exposing raw profile data."""
    if not career_context:
        return ""
    role_family = (career_context.get("role_family") or "").strip()
    primary_role = (career_context.get("primary_role") or "").strip()
    target_roles = [
        str(v).strip() for v in career_context.get("target_roles", []) if str(v).strip()
    ][:5]
    goals = [
        str(v).strip() for v in career_context.get("interview_goals", []) if str(v).strip()
    ][:5]
    gd_topics = [
        str(v).strip() for v in career_context.get("gd_topics", []) if str(v).strip()
    ][:8]
    resume_facts = [
        str(v).strip() for v in career_context.get("resume_facts", []) if str(v).strip()
    ][:8]
    memory = career_context.get("career_memory_context")
    memory = memory if isinstance(memory, dict) else {}
    if not any([role_family, primary_role, target_roles, goals, gd_topics, resume_facts, memory]):
        return ""
    lines = ["Career personalization context (private; use it, never read it aloud):"]
    if role_family:
        lines.append(f"- role family: {role_family}")
    if primary_role:
        lines.append(f"- primary role focus: {primary_role}")
    if target_roles:
        lines.append(f"- target roles: {', '.join(target_roles)}")
    if goals:
        lines.append(f"- interview goals: {', '.join(goals)}")
    if gd_topics:
        lines.append(f"- preferred GD topics: {', '.join(gd_topics)}")
    if resume_facts:
        lines.append("- safe resume/project facts to draw from:")
        lines.extend(f"  - {fact}" for fact in resume_facts)
        lines.append(
            "These facts belong to the learner, not to you or any simulated "
            "persona. Use them only to ask tailored follow-ups, assess relevance, "
            "or choose realistic constraints; never claim them as your own "
            "experience or speak in first person as if they happened to you."
        )
    if memory:
        lines.append("- prior learning memory to adapt this session:")
        for label, key in (
            ("active gaps", "active_gaps"),
            ("improving gaps", "improving_gaps"),
            ("resolved gaps", "resolved_gaps"),
            ("mastered skills", "mastered_skills"),
        ):
            items = memory.get(key) if isinstance(memory.get(key), list) else []
            rendered = []
            for item in items[:4]:
                if not isinstance(item, dict):
                    continue
                skill = str(item.get("skill_id") or item.get("gap") or "").strip()
                action = _sanitize_memory_text(item.get("recommended_next_action") or "")
                evidence = _sanitize_memory_text(item.get("latest_evidence") or "")
                missing = [
                    _sanitize_memory_text(v)
                    for v in item.get("missing_criteria", [])
                    if _sanitize_memory_text(v)
                ][:3]
                blockers = [
                    _sanitize_memory_text(v)
                    for v in item.get("blockers", [])
                    if _sanitize_memory_text(v)
                ][:3]
                bits = [skill]
                if action:
                    bits.append(f"next: {action}")
                if missing:
                    bits.append(f"missing: {', '.join(missing)}")
                if blockers:
                    bits.append(f"blockers: {', '.join(blockers)}")
                if evidence:
                    bits.append(f"evidence: {evidence[:120]}")
                rendered.append(" | ".join(bit for bit in bits if bit))
            if rendered:
                lines.append(f"  - {label}: " + " ; ".join(rendered))
        repeats = memory.get("repeated_issue_counts")
        if isinstance(repeats, dict) and repeats:
            pairs = [
                f"{_sanitize_memory_text(key)[:120]} x{int(value)}"
                for key, value in list(repeats.items())[:6]
                if _sanitize_memory_text(key)
            ]
            if pairs:
                lines.append("  - repeated issue counts: " + ", ".join(pairs))
        reports = memory.get("recent_reports") if isinstance(memory.get("recent_reports"), list) else []
        summaries = [
            _sanitize_memory_text(report.get("summary") or "")[:160]
            for report in reports[:3]
            if isinstance(report, dict) and _sanitize_memory_text(report.get("summary") or "")
        ]
        if summaries:
            lines.append("  - recent report summaries: " + " ; ".join(summaries))
    lines.append(
        "Use this for examples, follow-ups, bridge exercises, and challenge "
        "constraints. Never invent projects, employers, metrics, or history."
    )
    lines.append(
        "Do not under-score or steer away from a concrete answer just because it "
        "uses role-specific details from this context. If you model an example, "
        "keep it in the learner's role family or the same recent project thread; "
        "avoid unrelated domains such as generic customer churn, sales, marketing, "
        "or client-deliverable stories unless those are in the learner profile."
    )
    return "\n".join(lines) + "\n\n"


def _gd_topic_guard(career_context: dict | None) -> str:
    """Lock GD prep follow-ups to the learner's selected topics.

    The career context may include both role and GD preferences. Role examples
    are allowed to vary, but GD practice loses trust when a follow-up quietly
    changes the motion. Keep this separate from the general career block so the
    rule is explicit near every generation instruction.
    """
    topics = [
        str(v).strip()
        for v in (career_context or {}).get("gd_topics", [])
        if str(v).strip()
    ][:5]
    if not topics:
        return ""
    topic_list = "; ".join(f'"{topic}"' for topic in topics)
    return (
        "GD topic lock (private): the learner selected these GD topic(s): "
        f"{topic_list}.\n"
        "- Do not switch to an unrelated GD topic.\n"
        "- When showing examples, do not switch the selected GD topic; vary only "
        "the stakeholder, evidence type, constraint, or angle inside that same topic.\n"
        "- If you need a close variant, harder challenge, bridge, example, or "
        "follow-up, keep it on the same selected GD topic.\n"
        "- Only change topics if the learner explicitly asks to practise a "
        "different GD topic.\n\n"
    )


def _simulation_context_block(
    task_type,
    scenario_config: dict | None,
    career_context: dict | None,
    *,
    topic: str = "",
) -> str:
    """Render mode-safe context for scored simulations.

    Prep can use broad career personalization. TEST mode cannot: GD tests must
    stay locked to the active motion, and interview tests must not inherit GD
    topic preferences. This keeps role/profile context from bleeding across the
    two assessment modes.
    """
    scenario = scenario_config or {}
    task_value = getattr(task_type, "value", str(task_type or ""))
    inferred_gd = bool(scenario.get("topic") or scenario.get("resolved_topic"))
    is_gd = task_value == TaskType.GD_TEST.value or (
        inferred_gd and not scenario.get("target_role")
    )
    if is_gd:
        active_topic = (
            str(scenario.get("topic") or scenario.get("resolved_topic") or topic or "").strip()
            or "the active GD motion"
        )
        environment = str(scenario.get("environment") or scenario.get("setting") or "").strip()
        lines = [
            "Scored GD assessment context (private; do not read aloud):",
            f"- active GD motion: {active_topic}",
        ]
        if environment:
            lines.append(f"- environment: {environment}")
        lines.extend([
            "- Use only the active motion above. Do not switch to profile GD preferences, resume projects, interview goals, or unrelated examples.",
            "- The learner is being assessed on GD contribution quality, not coached mid-test.",
        ])
        return "\n".join(lines) + "\n\n" + _scenario_block(scenario_config)

    active_role = (
        str(scenario.get("target_role") or "").strip()
        or str((career_context or {}).get("primary_role") or "").strip()
        or "the target role"
    )
    slim_context = dict(career_context or {})
    slim_context.pop("gd_topics", None)
    slim_context.pop("custom_gd_topics", None)
    if active_role:
        slim_context["primary_role"] = active_role
        slim_context["target_roles"] = [active_role]
    lines = [
        "Scored interview assessment context (private; selected scenario role wins over profile defaults):\n",
        f"- AUTHORITATIVE active interview role: {active_role}\n",
        "- Use this exact role in the visible opening, prompts, scoring context, and report focus.\n",
        "- If career profile roles differ, treat them only as background history, never as the interview target.\n\n",
        _career_context_block(slim_context),
        _scenario_block(scenario_config),
        (
            "Use role/resume facts only to ask realistic interview probes. Do not mention or use GD "
            "topic preferences in interview mode.\n\n"
        ),
    ]
    return "".join(lines)


def _interview_prep_context_guard(node: "Concept", career_context: dict | None) -> str:
    """Keep interview-prep follow-ups inside the learner's role and recent thread."""
    if not getattr(node, "id", "").startswith("int_"):
        return ""
    ctx = career_context or {}
    role = (ctx.get("primary_role") or "").strip()
    target_roles = [
        str(v).strip() for v in ctx.get("target_roles", []) if str(v).strip()
    ][:3]
    role_family = (ctx.get("role_family") or "").strip()
    if not any([role, target_roles, role_family]):
        return ""
    role_focus = role or ", ".join(target_roles) or role_family
    lines = [
        "Interview prep context lock (private):",
        f"- AUTHORITATIVE active role: {role_focus}.",
        "- Use that exact active role in visible tasks. Secondary profile roles are background only; do not substitute one into the current exercise.",
        "- Preserve the recent scenario thread shown in the transcript when it is specific; do not jump to a new domain just to vary the exercise.",
        "- Do not introduce unrelated domains such as remote work culture, generic customer churn, sales, marketing, or broad business growth unless the learner introduced them.",
    ]
    if getattr(node, "id", "") == "int_05_why_this_role":
        lines.extend([
            "- A company may appear only if it is configured in context or the learner named it in the current conversation.",
            "- If no company has been named, ask the learner to choose a real company and provide a verified fact; never invent a company, company type, or startup context.",
            "- Preserve the learner's named company across feedback and pressure tasks unless the backend tutor plan explicitly requests a fresh independent company example.",
        ])
    if role_family == "software_technical" or any(
        term in " ".join([role, role_family, *target_roles]).lower()
        for term in ("backend", "software", "platform", "engineer", "developer")
    ):
        lines.append(
            "- For software/backend profiles, use backend/API/reliability/payment/platform/project-ownership/trade-off contexts."
        )
    return "\n".join(lines) + "\n\n"


def _scenario_block(scenario_config: dict | None) -> str:
    if not scenario_config:
        return ""
    pieces = []
    topic = scenario_config.get("resolved_topic") or scenario_config.get("topic")
    if topic:
        pieces.append(f"- resolved topic/focus: {topic}")
    if scenario_config.get("environment"):
        pieces.append(f"- GD environment: {scenario_config.get('environment')}")
    if scenario_config.get("interview_type"):
        pieces.append(f"- interview type: {scenario_config.get('interview_type')}")
    if scenario_config.get("pressure_level"):
        pieces.append(f"- pressure level: {scenario_config.get('pressure_level')}")
    if scenario_config.get("target_role"):
        pieces.append(f"- target role: {scenario_config.get('target_role')}")
    if not pieces:
        return ""
    return (
        "Simulation setup (private; keep the session consistent):\n"
        + "\n".join(pieces)
        + "\n\n"
    )


def _diagnosis_block(diagnosis: dict | None) -> str:
    """Render the latest diagnosis as a few clean, labelled lines for a coaching
    move.

    The coaching builders used to f-string the raw dict (`{diagnosis}`), emitting
    a Python repr — braces, quotes, booleans, and fields a teach/bridge move does
    not need (score, goodbye, on_task, english). A local model parses labelled
    plain lines far better than dict syntax, so surface only what shapes the next
    move: what they grasped, their errors, what they did well, the next focus, and
    a non-neutral emotional tone."""
    if not diagnosis:
        return "Your read of their last answer: (no prior read yet)\n\n"
    understanding = (diagnosis.get("understanding") or "").strip()
    errors = [str(e).strip() for e in (diagnosis.get("errors") or []) if str(e).strip()]
    strengths = [str(s).strip() for s in (diagnosis.get("strengths") or []) if str(s).strip()]
    next_focus = (diagnosis.get("next_focus") or "").strip()
    affect = (diagnosis.get("affect") or "").strip()
    lines = ["Your read of their last answer:"]
    if understanding:
        lines.append(f"- what they grasped: {understanding}")
    if errors:
        lines.append(f"- main error(s): {'; '.join(errors[:3])}")
    if strengths:
        lines.append(f"- did well: {'; '.join(strengths[:3])}")
    if next_focus:
        lines.append(f"- most useful next focus: {next_focus}")
    if affect and affect != "neutral":
        lines.append(f"- emotional tone: {affect}")
    if len(lines) == 1:
        lines.append("- (no detail captured this turn)")
    return "\n".join(lines) + "\n\n"


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


def _exemplar_block(node: "Concept") -> str:
    """Render the node's authored model answers as a calibration anchor.

    The curriculum hand-authors 1-2 exemplars per node (Concept.exemplars) —
    situated, target-context model answers that say far more than the abstract
    success_criteria about what "mastered" actually looks like. They were dead
    weight (no prompt consumed them); this surfaces them. Returns "" when a node
    has no exemplars (e.g. school_english) so the caller degrades silently."""
    exemplars = getattr(node, "exemplars", None) or []
    if not exemplars:
        return ""
    lines = "\n".join(f"  - {ex}" for ex in exemplars)
    return (
        "Model answers at the target quality bar for THIS skill (use them to "
        "calibrate what 'mastered' means and to recast toward — do NOT copy them "
        "verbatim or read them aloud):\n"
        f"{lines}\n\n"
    )


# ---------- evaluate (structured) ----------

def build_eval_prompt(
    node: Concept,
    messages: list[dict],
    user_input: str,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
    career_context: dict | None = None,
) -> str:
    scoped_context = _career_context_for_node(node, career_context)
    return (
        f"{_persona(behavior)}\n"
        f"{_strictness_gate(behavior)}\n"
        f"{_career_context_block(scoped_context)}"
        f"Skill being assessed: {node.skill}\n"
        f"What a mastered answer looks like: {node.success_criteria}\n\n"
        f"{_exemplar_block(node)}"
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


def build_prep_eval_prompt(packet: dict, career_context: dict | None = None) -> str:
    """Structured career-prep rubric prompt."""
    context = career_context or {}
    private_context = ""
    if context:
        facts = context.get("resume_facts") or []
        role = context.get("primary_role") or context.get("target_role") or ""
        private_context = (
            "\nPRIVATE CAREER CONTEXT (use only to interpret relevance; do not quote "
            "personal data):\n"
            f"- target role: {role or 'unspecified'}\n"
            f"- learner-owned facts: {', '.join(facts[:5]) if facts else 'none'}\n"
        )
    stage_contract = ""
    if packet.get("core_qualified") and packet.get("attempt_type") in {"transfer", "pressure"}:
        stage_contract = (
            "\nHARDER-STAGE CONTRACT:\n"
            f"- attempt_type: {packet.get('attempt_type')}\n"
            f"- validated parent turn: {packet.get('core_qualification_turn_id') or 'missing'}\n"
            "- The parent turn only authorizes this harder stage. Judge EVERY criterion "
            "present in this packet against the latest learner answer; some skill-specific "
            "stages intentionally require the learner to demonstrate the base skill again. "
            "Copy evidence only from the latest learner answer. If the parent turn is missing, mark "
            "pass_eligible false.\n"
        )
    return (
        f"{TUTOR_PERSONA}\n\n"
        "You are grading ONE career-prep answer against an explicit rubric. "
        "Judge semantic quality only. Do not invent evidence. For every required "
        "criterion marked met, copy a short evidence_quote from the learner answer. "
        "If the learner implies the skill but provides no quoteable proof, mark "
        "the criterion not met. For GD evidence, distinguish learner-owned experience, "
        "a named external source, an explicit analogy, and a labelled hypothetical. An "
        "external factual or numerical claim without a named source is unsupported: mark "
        "the evidence criterion not met and include source_missing in the reason. Treat the "
        "task_contract as the authoritative assigned role, topic, participants, claims, and "
        "transfer context; do not infer a different assignment from older transcript text.\n"
        f"{private_context}{stage_contract}\n"
        "EVALUATION PACKET JSON:\n"
        f"{json.dumps(packet, ensure_ascii=False)}\n\n"
        "Return JSON with:\n"
        "- raw_score: raw semantic score 0.0-1.0\n"
        "- effective_score: same as raw_score; backend may cap it\n"
        "- understanding: one-line read\n"
        "- errors: concrete misses\n"
        "- strengths: concrete strengths\n"
        "- next_focus: single next gap\n"
        "- criteria: one item for each criterion id with id, met, evidence_quote, reason, quality\n"
        "- required_missing: ids of required criteria that are not met\n"
        "- pass_eligible: true only if the answer independently meets all required criteria\n"
        "- mastery_eligible: true only for strong, transferable, non-borderline evidence\n"
        "- on_task, english, affect, goodbye\n"
        "Return only the JSON object."
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
    scenario_config: dict | None = None,
    career_context: dict | None = None,
    task_type=None,
) -> str:
    """Score a whole TEST-mode simulation transcript at the end.

    Unlike build_eval_prompt (one answer), this judges the learner's WHOLE
    contribution across the session — their stance, evidence, and handling of
    pressure — and returns the deferred feedback that was withheld mid-stream.
    """
    return (
        f"{_persona(behavior)}\n"
        f"{_strictness_gate(behavior)}\n"
        f"{_simulation_context_block(task_type, scenario_config, career_context, topic=topic)}"
        f"Topic of the session: {topic}\n\n"
        f"Full transcript (assistant lines are the simulated participants / "
        f"interviewer; user lines are the learner being assessed):\n"
        f"{_history_block(messages, limit=40, max_chars=_HISTORY_CHAR_BUDGET)}\n\n"
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
        "three to 0.0 for interview sessions. Judge these as DEBATE MOVES, not "
        "mere talk-time:\n"
        "- participation_score: initiative and floor moves — did the learner "
        "stake a clear position, claim the floor, and interject at the right "
        "moments rather than waiting to be invited? 0.7+ means they DROVE the "
        "discussion, not just reacted to it.\n"
        "- relevance_score: argumentative moves — did they REBUT specific points "
        "with reasoning, bring concrete evidence, and BUILD ON or synthesise "
        "others' contributions (not just restate their own view)? 0.7+ means "
        "moves that genuinely advanced the argument.\n"
        "- language_score: fluency, grammar, and CONCISION under live pressure — "
        "tight, well-formed contributions score high; rambling, padded, or "
        "hard-to-follow turns score lower even when the underlying idea is sound. "
        "0.7+ means fluent and economical with only minor slips.\n"
        "For interview sessions also rate two sub-dimensions (0.0-1.0 each); set "
        "both to 0.0 for GD sessions:\n"
        "- clarity_score: how clearly and concisely the learner answered — "
        "structured response, no waffle, concrete examples. 0.7+ means clear.\n"
        "- confidence_score: composure under pressure — steady delivery, no "
        "excessive hedging, handles follow-ups without deflecting. 0.7+ means "
        "composed.\n"
        "Return JSON with:\n"
        "- score: 0.0-1.0 on the scale above\n"
        "- summary: one short paragraph the learner can read. It must explain what evidence was actually shown and what coverage/validity limits remain. Do not use generic praise such as 'Great job', 'Strong answer', 'Strong interview', or 'Strong discussion'. Do not claim the learner is ready or has mastered the skill. Do not provide copyable sample answers.\n"
        "- strengths: list of what genuinely landed (empty list if none)\n"
        "- improvements: list of the few most useful things to work on next\n"
        "- participation_score: 0.0-1.0\n"
        "- relevance_score: 0.0-1.0\n"
        "- language_score: 0.0-1.0\n"
        "- clarity_score: 0.0-1.0\n"
        "- confidence_score: 0.0-1.0\n"
        "- scenario_label: short label for the tested role/topic\n"
        "- role_focus: target role if this was an interview, otherwise empty\n"
        "- topic: GD topic if this was a GD, otherwise the interview focus\n"
        "- observed_skill_gaps: list of concrete weak skills observed\n"
        "- recommended_next_nodes: list of short next practice labels\n"
        "- assessment_caveats: learner-evidence caveats only, such as insufficient answered turns, narrow competency coverage, or an unanswered final prompt. Do not include simulator repair/internal validity notes here; the backend adds those separately."
    )


# ---------- writers'-room simulation (director decides, persona speaks) ----------

def _probe_block(probe_items: list | None) -> str:
    """Render the weakness-probe bank for the director (P0-5).

    These are the prep-weakness-targeted items generated up front. The director
    was never shown them, so the candidate's stated weaknesses were never pressed
    (live: weaknesses:[] every turn). Surfacing them here lets the director set an
    intent that drives the panel onto exactly those weak spots."""
    items = probe_items or []
    if not items:
        return ""
    lines = [
        "\nProbe bank — the learner's known weak spots from prep. Work through "
        "the ones NOT yet pressed: set the next speaker's intent to press one "
        "directly (do not read this list aloud):"
    ]
    for it in items[:6]:
        prompt = (it.get("prompt") or "").strip()
        aim = (it.get("aim") or "").strip()
        if prompt:
            tail = f" — a strong answer {aim}" if aim else ""
            lines.append(f"- {prompt}{tail}")
    return "\n".join(lines) + "\n"


def build_director_prompt(
    bb: dict,
    personas: list[dict],
    task_type,
    transcript: str,
    probe_items: list | None = None,
    scenario_config: dict | None = None,
    career_context: dict | None = None,
) -> str:
    """The Director's brief for one writers'-room round.

    The director reads the live blackboard + transcript and decides the next
    move: which roster persona speaks, with what intent, at what tension, how
    well the learner's last contribution landed, and whether to close. This is a
    live ASSESSMENT (not coaching) — the behavior pack supplies the strict
    assessor voice. All instruction lives in the prompt text (council rule);
    the schema field descriptions carry none.
    """
    behavior = behavior_for(task_type)
    covered = ", ".join(bb.get("covered") or []) or "(nothing yet)"
    open_threads = ", ".join(bb.get("open_threads") or []) or "(none open)"
    roster_lines = []
    for p in personas:
        stance = p.get("stance") or p.get("role") or "participant"
        roster_lines.append(
            f"- speaker_id={p['speaker_id']}: {p['name']} — {stance}"
        )
    roster = "\n".join(roster_lines)
    last_id = bb.get("last_speaker", "")
    last_name = next(
        (p["name"] for p in personas if p["speaker_id"] == last_id), ""
    )
    last_speaker_line = (
        f"Last voice to speak: {last_name} (speaker_id={last_id}). Do NOT hand "
        "the floor back to the same speaker two turns running unless it is "
        "genuinely essential — rotate so different voices press the learner.\n"
        if last_id
        else "No one has spoken yet — open with whichever voice best frames the topic.\n"
    )
    return (
        f"{behavior.persona}\n"
        f"You are the DIRECTOR of a live writers'-room assessment. You do not "
        "speak to the learner yourself: you read the room, then choose which "
        "voice speaks next and exactly what it should do. This is a live "
        "assessment, not coaching — never soften, never teach.\n"
        f"How this assessment runs: {behavior.pedagogy}\n\n"
        f"{_simulation_context_block(task_type, scenario_config, career_context, topic=bb['topic'])}"
        f"Topic under discussion: {bb['topic']}\n"
        f"Current phase: {bb['phase']} | current tension: {bb['tension']}\n"
        f"Already covered: {covered}\n"
        f"Open threads still unresolved: {open_threads}\n"
        f"{_probe_block(probe_items)}\n"
        f"The roster of voices you may call on (you MUST pick one of these, by "
        f"its speaker_id):\n{roster}\n"
        f"{last_speaker_line}\n"
        f"Transcript so far:\n{transcript}\n\n"
        "Think like a director: take a beat, read what just happened, then make "
        "ONE deliberate decision for the next turn. Decide all of the following:\n"
        "1. WHO speaks next — choose exactly one voice from the roster above and "
        "name it by its speaker_id. It MUST be one of the listed speaker_ids; do "
        "not invent a speaker.\n"
        "2. That voice's INTENT for the upcoming turn — one concrete "
        "conversational goal grounded in the transcript (e.g. press a specific "
        "claim, surface a contradiction, open a new angle). Make it a single, "
        "actionable instruction the persona can act on.\n"
        "3. The TENSION the discussion should carry now, 0.0-1.0 — how much heat "
        "to bring next. Raise it to press a coasting learner, ease it only to let "
        "a genuinely strong point breathe.\n"
        "4. The ANSWER_QUALITY of the learner's MOST RECENT contribution, "
        "0.0-1.0 — your honest read of how well they just did. Hold a high bar; "
        "do not reward effort alone.\n"
        "5. Whether to CLOSE the session (should_close): true only when the topic "
        "is genuinely exhausted or the learner has clearly finished.\n"
        "Also pick the single action that best fits your move "
        "(probe_deeper, pivot_topic, escalate_pressure, or wind_down).\n"
        "Return your decision as the structured fields requested."
    )


def build_assessment_turn_prompt(
    *,
    plan: dict,
    visible_ledger: list[dict],
    transcript: str,
    learner_turn: str,
    turn_context: dict | None = None,
) -> str:
    """Prompt for the one-call assessment turn engine.

    The model both evaluates the learner's latest turn and drafts the next
    visible simulator response, but the backend still validates the returned
    speaker/action/text against the immutable plan and visible event ledger.
    """
    mode = str(plan.get("mode") or plan.get("task_type") or "")
    roster = plan.get("active_personas") or plan.get("roster") or []
    roster_lines = []
    for persona in roster:
        if not isinstance(persona, dict):
            continue
        role = persona.get("role_type") or persona.get("role") or persona.get("stance") or "participant"
        roster_lines.append(
            f"- {persona.get('speaker_id')}: {persona.get('name')} ({role})"
        )
    ledger_lines = []
    for event in visible_ledger[-12:]:
        if not isinstance(event, dict):
            continue
        speaker = event.get("speaker_name") or event.get("speaker_id") or "Assistant"
        content = " ".join(str(event.get("content") or "").split())[:360]
        event_id = event.get("event_id") or "unknown"
        ledger_lines.append(f"- {event_id} [{speaker}]: {content}")
    if mode == TaskType.GD_TEST.value:
        analysis_contract = (
            "analysis must be GDAnalysis with mode='gd_test'. "
            "routing_case is reply_only, reply_and_request, point_only, "
            "request_only, clarification_request, or move_on. Only set "
            "requested_next_speaker when the learner explicitly asks a roster "
            "voice to respond. A phrase like 'senior expert can review' is an "
            "argument, not a request for Quiet Expert unless the learner names "
            "Quiet Expert or an exact roster voice. addressed_event_ids must "
            "come only from the visible event ledger below. If the immutable plan "
            "contains focus_plan items and this answer demonstrates or misses one, "
            "set analysis.focus_id to that exact focus_id; otherwise leave it blank."
        )
        visible_response_contract = (
            "- GD panelist text must first contribute to the discussion: take a stance, "
            "challenge a claim, add evidence, synthesize positions, build consensus, "
            "or directly answer the learner's requested question.\n"
            "- GD panelist text must not turn into learner-facing evidence demands "
            "such as 'Can you provide metrics?' or 'What study proves that?'. "
            "If proof is weak, the panelist should state the missing proof as a "
            "discussion objection or counterpoint, not interview the learner.\n"
            "- GD panelists must not ask direct follow-up questions, cross-examine "
            "the learner, or hand the floor to another panelist. Convert questions "
            "into spoken claims: name the risk, condition, metric, or synthesis "
            "as the panelist's own contribution.\n"
            "- Moderator text may steer, summarize, repair an unavailable speaker request, "
            "or pivot the angle, but must keep the active topic visible.\n"
            "- If the learner explicitly requested a panelist, that panelist must answer "
            "the extracted question instead of echoing it back.\n"
        )
    else:
        active_probe = (turn_context or {}).get("answered_probe") or {}
        next_probe = (turn_context or {}).get("next_probe") or {}
        active_criteria = [
            str(value)
            for value in active_probe.get("criteria") or []
            if str(value).strip()
        ]
        analysis_contract = (
            "analysis must be InterviewAnalysis with mode='interview_test'. "
            "Use answer_kind='clarification_request' only when the learner asks "
            "what the question means; use 'move_on_request' only when they ask "
            "to switch topics. A substantive answer that begins with 'yes' is still "
            "answer_kind='answer', not a clarification. Do not score clarification or move-on controls. "
            f"For normal answers, evaluate answered_probe.prompt_id='{active_probe.get('prompt_id', '')}' "
            f"and set analysis.active_probe_id to that exact prompt_id. Use criteria from answered_probe only. "
            f"criteria_met and missing_criteria must be a complete, disjoint partition of exactly {json.dumps(active_criteria)}; "
            "do not omit a criterion and do not invent another criterion id. "
            "Name missing criteria that are actually missing from the learner's latest answer. "
            "Read the learner's entire latest answer, including its final sentences. "
            "If it contains an explicit changed outcome or metric, do not mark result missing. "
            "For a scorable answer, quality_score must be between 0.1 and 1.0; use 0 only for a non-scorable control. "
            f"The next visible interviewer question must ask next_probe.prompt_id='{next_probe.get('prompt_id', '')}' "
            "unless the learner asked for clarification or move-on. Do not repeat recent prompts."
        )
        visible_response_contract = (
            "- Interviewer text must ask or clarify one question. It must not answer "
            "the question for the learner.\n"
            "- Interviewer text must not re-ask a recent or already-covered prompt. "
            "Use the backend-authorized next_probe for normal answers.\n"
        )
    assessment_persona = (
        "You are Zidd's scored assessment operator. Evaluate the learner's latest "
        "turn semantically, keep the active assessment contract, and write only "
        "the next in-simulation response for the authorized speaker."
    )
    return (
        f"{assessment_persona}\n"
        "You are running a scored assessment turn. Make exactly one structured "
        "decision for the learner's latest turn. This is not coaching: do not "
        "give model answers, rubric explanations, or private scoring text to "
        "the learner.\n\n"
        "Immutable assessment plan JSON:\n"
        f"{json.dumps(plan, ensure_ascii=False)}\n\n"
        "Active roster (you may choose only these speaker_id values):\n"
        f"{chr(10).join(roster_lines) or '(no roster)'}\n\n"
        "Visible event ledger (only these prior assistant turns are visible):\n"
        f"{chr(10).join(ledger_lines) or '(none yet)'}\n\n"
        "Backend-authorized turn context JSON:\n"
        f"{json.dumps(turn_context or {}, ensure_ascii=False)}\n\n"
        f"Transcript tail:\n{transcript}\n\n"
        f"Learner latest turn:\n\"{learner_turn}\"\n\n"
        f"{analysis_contract}\n\n"
        "Return JSON with exactly:\n"
        "- analysis: the semantic read described above\n"
        "- next_action: speaker_id, action_type, intent, should_close\n"
        "- visible_response: speaker_id and learner-visible text\n\n"
        "Rules for visible_response:\n"
        "- speaker_id must match next_action.speaker_id.\n"
        "- Use only active topic/role/personas from the plan.\n"
        "- Never self-label inside the text; the UI already labels the speaker.\n"
        "- Never say another speaker made a prior point unless that speaker has "
        "a visible ledger event above.\n"
        f"{visible_response_contract}"
        "- Keep the response concise enough for a live simulator turn."
    )


# ---------- Spec B content selector (Stage 2: pick the next node) ----------

def build_selector_prompt(snapshot: dict, candidates: list[dict]) -> str:
    """The selector's brief: pick exactly ONE next-content candidate.

    Called only when the deterministic stage produced more than one valid
    candidate. The model reads a compact learner snapshot and the explicit
    candidate list, then picks one candidate (by its next_ref) and a difficulty
    band. All instruction lives here (council rule); the schema carries none.
    """
    weaknesses = ", ".join(str(w) for w in snapshot.get("weaknesses") or []) or "(none)"
    cand_lines = []
    for c in candidates:
        cand_lines.append(
            f"- action={c['action']} next_ref={c['next_ref']} "
            f"band={c.get('band', 'standard')}"
        )
    candidate_block = "\n".join(cand_lines)
    return (
        "You are the content SELECTOR for an adaptive English-coaching engine. "
        "The learner just cleared their current skill node. Your one job: choose "
        "exactly which node they move to next, from a fixed list of valid "
        "candidates.\n\n"
        "Learner snapshot:\n"
        f"- current node: {snapshot.get('current_node')}\n"
        f"- mastery on current node (0.0-1.0): {snapshot.get('mastery')}\n"
        f"- clean-pass streak: {snapshot.get('clean_streak')}\n"
        f"- attempts on current node: {snapshot.get('attempts')}\n"
        f"- recent weaknesses: {weaknesses}\n\n"
        "Valid candidates (you MUST pick exactly one of these, by its "
        f"next_ref):\n{candidate_block}\n\n"
        "Decide all of the following:\n"
        "1. next_ref — the next_ref of the ONE candidate you pick. It MUST be one "
        "of the next_ref values listed above; never invent a ref outside the "
        "list.\n"
        "2. action — copy the action of the candidate you picked (ADVANCE, "
        "REMEDIATE, REPEAT, or SKIP).\n"
        "3. band — the difficulty band to deliver the next node at: "
        "\"foundational\" for a shakier learner (low mastery, many attempts, "
        "recent weaknesses), \"standard\" for a solid clean pass, or \"stretch\" "
        "for a strong, fast, weakness-free pass.\n"
        "4. rationale — one sentence explaining your pick, grounded in the "
        "snapshot.\n"
        "Return your decision as the structured fields requested."
    )


def _is_moderator_persona(persona: dict) -> bool:
    role_type = str(persona.get("role_type") or "").lower()
    speaker_id = str(persona.get("speaker_id") or "").lower()
    name = str(persona.get("name") or "").lower()
    role = str(persona.get("role") or "").lower()
    return (
        role_type == "moderator"
        or "moderator" in speaker_id
        or "moderator" in name
        or "facilitator" in role
    )


def _other_voices_block(persona: dict, roster: list[dict] | None, *, is_moderator: bool = False) -> str:
    """Render the OTHER participants so a persona can engage them by name.

    Without this, each persona spoke into a vacuum — it knew only the topic and
    the transcript, never who else was in the room or their stances, so the
    panel read as parallel monologues at the learner instead of a group that
    argues with itself (the GD cross-talk gap). We list everyone EXCEPT this
    persona (matched by speaker_id, falling back to name) and the learner, and
    tell the persona to pick up and push on a named participant's point. Empty
    for a one-voice roster (the interview panel), so interview turns are
    unchanged."""
    if not roster:
        return ""
    sid = persona.get("speaker_id")
    name = persona.get("name")
    others = [
        p for p in roster
        if (p.get("speaker_id") or p.get("name")) != (sid or name)
    ]
    if not others:
        return ""
    lines = []
    for p in others:
        trait = p.get("stance") or p.get("role") or "participant"
        lines.append(f"- {p['name']} ({trait})")
    if is_moderator:
        return (
            "The active panelists are:\n" + "\n".join(lines) + "\n"
            "Use their names to manage the floor, invite quieter voices, clarify "
            "who can speak, and summarize the split in the room. Do not argue a "
            "side, do not take a debater stance, and do not speak on behalf of "
            "any panelist.\n\n"
        )
    return (
        "Also in the room are these other participants (this is NOT you, and "
        "NONE of them is the learner):\n" + "\n".join(lines) + "\n"
        "Engage them by name where it's natural: pick up something one of them "
        "actually said in the transcript and push back on it or build on it, so "
        "the discussion feels like a real group arguing, not separate speeches "
        "aimed at the learner. Only react to what they have ALREADY said — never "
        "put words in their mouth or speak on their behalf.\n\n"
    )


def build_persona_prompt(
    persona: dict,
    intent: str,
    transcript: str,
    bb: dict,
    roster: list[dict] | None = None,
    scenario_config: dict | None = None,
    career_context: dict | None = None,
    task_type=None,
) -> str:
    """One persona's turn: speak in-character, pursuing the director's intent.

    The model speaks ONLY as this persona, in its stance/role, pursuing the
    given intent against the transcript. It is a live assessment — the persona
    engages and presses the learner; it never coaches, grades, or breaks
    character. `roster` (the full panel) lets the persona address the OTHER
    voices by name so the group cross-talks instead of monologuing. All
    instruction lives in the prompt text (council rule).
    """
    character = (
        persona.get("prompt_role")
        or persona.get("stance")
        or persona.get("role")
        or "a participant"
    )
    # Optional per-session manner (interview tonal variants). Empty for personas
    # without a style (the GD panel), so their prompt is byte-for-byte unchanged.
    style = persona.get("style")
    style_line = f"Your manner this session is {style}.\n" if style else ""
    role_markers = " ".join(
        str(persona.get(key) or "")
        for key in ("speaker_id", "role_type", "role", "prompt_role")
    ).lower()
    context_task_type = task_type
    if context_task_type is None:
        if "moderator" in role_markers or "debater" in role_markers:
            context_task_type = TaskType.GD_TEST
        elif "interviewer" in role_markers:
            context_task_type = TaskType.INTERVIEW_TEST
    is_moderator = _is_moderator_persona(persona)
    is_gd_context = context_task_type == TaskType.GD_TEST
    interview_guard = ""
    if "interviewer" in role_markers:
        interview_guard = (
            "Interviewer discipline: ask the candidate one focused question or "
            "follow-up. Do not provide a model answer, sample answer, or coaching "
            "script. Do not say \"I would\" as if you were the candidate; the "
            "candidate must produce the answer.\n"
        )
    if is_moderator:
        if is_gd_context:
            turn_discipline = (
                "Stay fully in facilitator character. This is a live group "
                "discussion assessment, not a lesson or interview: keep the group "
                "clear, manage the floor, summarize shifts, and set one concrete "
                "discussion task. Do not promise an immediate second speaker; name "
                "the angle or kind of panel response needed instead. Do NOT argue a "
                "side, do NOT coach, do NOT grade, do NOT give feedback, and do "
                "NOT break character.\n"
            )
        else:
            turn_discipline = (
                "Stay fully in facilitator character. This is a live assessment, "
                "not a lesson: keep the exchange clear, manage the floor, "
                "summarize shifts, and set one concrete next step. Do NOT argue a "
                "side, do NOT coach, do NOT grade, do NOT give feedback, and do "
                "NOT break character.\n"
            )
    elif is_gd_context:
        turn_discipline = (
            "Stay fully in GD participant character. This is a live group "
            "discussion, not an interview: contribute a stance, challenge, "
            "evidence point, trade-off, synthesis move, or direct answer to a "
            "panelist request. Do not ask follow-up questions or hand the floor "
            "to another panelist; turn questions into clear claims or conditions. "
            "Do NOT coach, do NOT grade, do NOT give feedback, and do NOT break "
            "character.\n"
        )
    else:
        turn_discipline = (
            "Stay fully in character. This is a live assessment, not a lesson: engage "
            "the learner, push back, probe, and hold your stance. Do NOT coach, do "
            "NOT grade, do NOT give feedback, and do NOT break character.\n"
        )
    return (
        f"You are {persona['name']}, {character}, taking part in a live "
        f"discussion about: {bb['topic']}.\n"
        f"The discussion is at phase '{bb['phase']}' with tension {bb['tension']} "
        "(0.0 = calm, 1.0 = heated) — let that set how hard you push right now.\n"
        f"{style_line}"
        f"{interview_guard}"
        f"{_simulation_context_block(context_task_type, scenario_config, career_context, topic=bb['topic'])}"
        f"\nTranscript so far:\n{transcript}\n\n"
        f"{_other_voices_block(persona, roster, is_moderator=is_moderator)}"
        f"Your goal for THIS turn: {intent}\n\n"
        f"{turn_discipline}"
        "CRITICAL OUTPUT RULE: reply with ONLY your own spoken words, as plain "
        "prose. Do NOT prefix your reply with your name, a "
        f"\"{persona['name']}:\" tag, or any speaker label — your identity is "
        "attached separately, so a self-tag would double up. Do NOT speak for the "
        "learner or for any other participant; write only your single "
        "contribution."
    )


def build_test_gen_prompt(
    behavior: BehaviorPack | None,
    weaknesses: list | None,
    n_items: int = 4,
    career_context: dict | None = None,
    scenario_config: dict | None = None,
    task_type: TaskType | str | None = None,
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
        f"{_simulation_context_block(task_type, scenario_config, career_context)}"
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

# The single most damaging tutor failure: writing the exact answer the learner is
# meant to produce, so the task collapses to copying ("say 'Hello, I am Ryuk'").
# Every production prompt carries this so the learner always has real work to do.
_NO_GIVEAWAY = (
    "Never write out the exact answer the learner should produce. Set the task and "
    "the frame; if you show an example, use DIFFERENT details than what they should "
    "say so they still have to compose their own. For GD practice, keep the selected "
    "motion/topic and vary only the stakeholder, evidence type, constraint, or angle. "
    "For interview practice, never add ownership, metrics, employers, impact, or "
    "achievement verbs that the learner did not supply. Their job is to fill the "
    "frame; yours is to set it, not to fill it."
)


def build_opening_prompt(
    node: Concept,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
    sim_topic: str = "",
    interview_test: bool = False,
    review_skills: list | None = None,
    career_context: dict | None = None,
    scenario_config: dict | None = None,
    allow_weakness_warmup: bool = False,
) -> str:
    if sim_topic:
        context_block = _simulation_context_block(
            TaskType.GD_TEST,
            scenario_config,
            career_context,
            topic=sim_topic,
        )
    elif interview_test:
        context_block = _simulation_context_block(
            TaskType.INTERVIEW_TEST,
            scenario_config,
            career_context,
            topic=node.title,
        )
    else:
        scoped_context = _career_context_for_node(node, career_context)
        context_block = (
            f"{_career_context_block(scoped_context)}"
            f"{_interview_prep_context_guard(node, scoped_context)}"
            f"{_gd_topic_guard(scoped_context)}"
            f"{_scenario_block(scenario_config)}"
        )
    base = (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{context_block}"
        f"{_stance_block(behavior)}"
        f"Today's skill: {node.title} — {node.skill}\n"
        f"Teaching focus: {node.teach_focus}\n\n"
    )
    # GD assessment opening (P0-4): brief the EXACT concrete motion the panel will
    # debate, so the learner argues the same motion. Without this the opening
    # invented its own motion from the vague teach_focus while the panel debated
    # another — briefed topic A, panel topic B on every run.
    if sim_topic:
        return base + (
            "This is a live group-discussion assessment, not a lesson. The motion "
            f"under discussion is:\n\"{sim_topic}\"\n"
            "Brief the learner on THIS exact motion in one or two sentences (use it "
            "verbatim — never invent a different topic), then ask them to state "
            "their opening position on it. End with that ask."
        )
    # Interview assessment opening (P0): the examiner must NOT invent the
    # candidate's history. Live, it opened by fabricating "your previous
    # experience where you mentioned improving team efficiency" and then anchored
    # the whole assessment on that phantom backstory. Force it to elicit a real
    # example from the candidate instead of assuming one.
    if interview_test:
        active_role = str((scenario_config or {}).get("target_role") or "").strip()
        role_line = (
            f"Open with {active_role} as the focus. "
            if active_role
            else "Open with the selected target role as the focus. "
        )
        return base + (
            "This is a live interview assessment, not a lesson. You are the "
            "interviewer and you have NOT heard the candidate yet. Do NOT invent "
            "or assume any of their history, employer, projects, or metrics. "
            f"{role_line}"
            "Open in 1-2 sentences: name the focus of this round, then ask the "
            "candidate to give you a concrete example FROM THEIR OWN EXPERIENCE "
            "for you to probe. End with that ask."
        )
    # Spaced retention check: skills the learner mastered a while ago but hasn't
    # practised recently. Re-checking ONE in the warm-up fights forgetting — the
    # longitudinal half of tracking. Renders only when present, so a normal
    # opening (and every existing prompt snapshot) is unchanged.
    review_line = ""
    if review_skills:
        skills = ", ".join(str(s) for s in review_skills[:2])
        review_line = (
            "The learner did well on these a while back; if it fits, slip a quick "
            f"one-line refresher on ONE of them into the warm-up to check it stuck: {skills}.\n"
        )
    gd_opening_line = ""
    if node.id.startswith("gd_"):
        gd_opening_line = (
            "GD prep opening contract: create a concrete mini group-discussion, not "
            "an interview question or generic coaching instruction. Name one exact "
            "motion (prefer a selected GD topic above; otherwise use a realistic "
            "public or workplace policy motion), briefly state what one or two "
            "participants have contributed, and ask the learner to perform today's "
            "specific discussion move. The learner must contribute substance, not "
            "only answer a question. Do not use role-specific interview, coding, or "
            "technical-meeting scenarios unless that is the selected motion itself. "
            "Every participant contribution must be logically usable for today's move: "
            "for a derailment task, make the tangent unmistakably unrelated to the motion; "
            "for a synthesis task, quote the two actual positions the learner must summarize. "
            "Never label a legitimate issue inside the motion as off-topic.\n"
        )
    warmup_contract = (
        "If your remembered notes name a weak spot or a 'next focus' from last "
        "time, open with a 10-second warm-up that re-tests THAT first, then move "
        "into today's skill. Otherwise open directly.\n"
        if allow_weakness_warmup
        else (
            "Use remembered weak spots only to tailor examples and emphasis. Do "
            "not open with a separate weak-spot warm-up, review drill, or prior "
            "topic. The first learner task must practise today's skill above.\n"
        )
    )
    return base + (
        warmup_contract +
        review_line +
        gd_opening_line +
        "Open the lesson in 2-3 sentences: briefly say what you'll work on, then "
        "give the learner ONE clear, small task that makes them produce language "
        "right now. Do not over-explain. End with the task.\n" + _NO_GIVEAWAY
    )


def build_teach_prompt(
    node: Concept,
    messages: list[dict],
    diagnosis: dict,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
    career_context: dict | None = None,
) -> str:
    is_career_context = bool(
        (career_context or {}).get("primary_role")
        or (career_context or {}).get("target_roles")
        or (career_context or {}).get("role_family")
        or (career_context or {}).get("gd_topics")
    )
    scoped_context = _career_context_for_node(node, career_context)
    tutor_plan = (
        (coach or {}).get("tutor_turn_plan")
        if isinstance((coach or {}).get("tutor_turn_plan"), dict)
        else {}
    )
    plan_verdict = str(tutor_plan.get("verdict") or "")
    if is_career_context and plan_verdict == "independent_pass":
        feedback_contract = (
            "Give short, targeted career-coaching feedback (2-4 sentences). The required "
            "criteria are already covered: anchor to the learner's actual evidence, do not "
            "invent a missing gap, and do not request another rewrite of the same answer. "
            "Set ONE new pressure or transfer task based on the enforced tutor-plan focus. "
            "Do not introduce a different domain, unrelated sample story, unrelated company "
            "example, or generic model answer. End with the new task.\n"
        )
    elif is_career_context:
        feedback_contract = (
            "Give short, targeted career-coaching feedback (2-4 sentences). Required shape: "
            "anchor to the learner's actual answer, name the exact missing gap, then set ONE "
            "targeted revision task. Rewrite or pressure-test their own answer; Do not introduce "
            "a different domain, unrelated sample story, unrelated company example, or generic "
            "model answer. For GD prep, stay on the active GD topic. For interview prep, stay "
            "inside the learner's own story/role context. End with the revision task.\n"
        )
    else:
        feedback_contract = (
            "Give a short, targeted teaching move (2-4 sentences) as a recast "
            "sandwich: first acknowledge what genuinely worked, then gently recast "
            "the single most important error by modelling the correct form ON A "
            "DIFFERENT EXAMPLE (do not scold or just label it wrong), then set the "
            "next small production task. End with the task.\n"
        )
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_career_context_block(scoped_context)}"
        f"{_interview_prep_context_guard(node, scoped_context)}"
        f"{_gd_topic_guard(scoped_context)}"
        f"{_stance_block(behavior)}"
        f"Skill: {node.skill}\nTeaching focus: {node.teach_focus}\n\n"
        f"{_exemplar_block(node)}"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"{_diagnosis_block(diagnosis)}"
        f"{feedback_contract}" + _NO_GIVEAWAY
    )


def build_teach_game_prompt(
    node: "Concept",
    diagnosis: dict,
    coach: dict | None = None,
    career_context: dict | None = None,
) -> str:
    """Prompt for the gamified teach path (scaffold >= 1).

    Asks qwen to return a single JSON object conforming to FillBlankGame.
    The prompt is intentionally minimal — no conversation history, no persona
    preamble — so qwen spends its token budget on the structured output, not
    prose framing. Instructions live here (not in schema field descriptions)
    to comply with the Flash-Lite council rule."""
    scoped_context = _career_context_for_node(node, career_context)
    coach_text = _coach_block(coach)
    career_text = _career_context_block(scoped_context)
    interview_context_guard = _interview_prep_context_guard(node, scoped_context)
    gd_topic_guard = _gd_topic_guard(scoped_context)
    focus = diagnosis.get("next_focus") or node.teach_focus
    errors = diagnosis.get("errors", [])
    error_line = (
        f"\nTop mistake to fix: {errors[0]}" if errors else ""
    )
    is_career_context = bool(
        (career_context or {}).get("primary_role")
        or (career_context or {}).get("target_roles")
        or (career_context or {}).get("role_family")
    )
    if is_career_context:
        hint_line = (
            '  "hint": short interview move / GD move label (e.g. '
            '"specific corrective habit", "evidence of impact") — do NOT put '
            "the answer here\n"
        )
        career_rules = (
            "- This is career communication practice, not a grammar or vocab drill.\n"
            "- The gap must practice an interview move or GD move: structure, "
            "evidence, specificity, ownership, trade-off clarity, or outcome.\n"
            "- Do NOT target verb tense, verb base form, articles, spelling, or "
            "grammar categories unless the listed top mistake is explicitly about "
            "language accuracy.\n"
        )
    else:
        hint_line = (
            '  "hint": short grammar or vocab category label (e.g. "past simple verb") '
            "— do NOT put the answer here\n"
        )
        career_rules = ""
    return (
        f"{coach_text}"
        f"{career_text}"
        f"{interview_context_guard}"
        f"{gd_topic_guard}"
        f"Skill: {node.skill}\n"
        f"Teaching focus: {focus}{error_line}\n\n"
        "Return a single JSON object for a fill-in-the-blank practice item.\n"
        "Fields (all required):\n"
        '  "sentence": one complete, natural sentence with exactly one ___ gap\n'
        f"{hint_line}"
        '  "answer_key": the word or phrase that correctly fills the gap\n'
        '  "context": one line explaining why this gap targets the teaching focus\n\n'
        "Rules:\n"
        "- The gap must target ONLY the top mistake or teaching focus listed above.\n"
        f"{career_rules}"
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
    career_context: dict | None = None,
) -> str:
    scoped_context = _career_context_for_node(node, career_context)
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_career_context_block(scoped_context)}"
        f"{_interview_prep_context_guard(node, scoped_context)}"
        f"{_gd_topic_guard(scoped_context)}"
        f"{_stance_block(behavior)}"
        f"Skill: {node.skill}\n"
        f"Easier sub-step to scaffold down to: {node.bridge_focus}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"{_diagnosis_block(diagnosis)}"
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
    career_context: dict | None = None,
) -> str:
    scoped_context = _career_context_for_node(node, career_context)
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_career_context_block(scoped_context)}"
        f"{_interview_prep_context_guard(node, scoped_context)}"
        f"{_gd_topic_guard(scoped_context)}"
        f"{_stance_block(behavior)}"
        f"Skill: {node.skill}\nSuccess looks like: {node.success_criteria}\n\n"
        f"{_exemplar_block(node)}"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"{_diagnosis_block(diagnosis)}"
        "The skill is shaky but present. Reinforce it as a recast sandwich: name "
        "what worked, gently model the one weak spot correctly ON A DIFFERENT "
        "EXAMPLE, give a quick tip, then ask them to try a close variant of the "
        "same task. End with the task.\n" + _NO_GIVEAWAY
    )


def build_challenge_prompt(
    node: Concept,
    messages: list[dict],
    diagnosis: dict,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
    career_context: dict | None = None,
    attempt_type: str = "transfer",
) -> str:
    scoped_context = _career_context_for_node(node, career_context)
    if attempt_type == "pressure":
        challenge_contract = (
            "Ask one concrete interviewer or panel pushback tied to their latest answer. "
            "Require a concise defense using their own evidence; do not ask for a generic rewrite."
        )
        stage_label = "Skill (ready for a focused pressure check)"
        stage_intro = "The learner is ready for a focused pressure check, not durable mastery. "
    elif attempt_type == "independent":
        challenge_contract = (
            "Ask for one fresh independent demonstration using a different learner-owned example. "
            "Do not rewrite or polish the accepted answer, and do not invent the new example for them."
        )
        stage_label = "Skill (ready for another independent check)"
        stage_intro = "The learner passed once and now needs a fresh independent check, not a transfer task. "
    else:
        challenge_contract = (
            "Ask for one complete harder variant in a different realistic context. "
            "It must still demonstrate the full skill, not merely polish the same wording."
        )
        stage_label = "Skill (ready for a harder transfer check)"
        stage_intro = "The learner is ready for a harder transfer check, not durable mastery. "
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_career_context_block(scoped_context)}"
        f"{_interview_prep_context_guard(node, scoped_context)}"
        f"{_gd_topic_guard(scoped_context)}"
        f"{_stance_block(behavior)}"
        f"{stage_label}: {node.skill}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"{_diagnosis_block(diagnosis)}"
        f"{stage_intro}"
        "Acknowledge briefly, then push them: give a harder, more realistic "
        "variant of the task that stretches the same skill. "
        f"{challenge_contract} Keep it to 2-3 sentences. End with the harder task."
    )


def build_redirect_prompt(
    node: Concept,
    messages: list[dict],
    diagnosis: dict,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
    model_answer: bool = False,
    career_context: dict | None = None,
) -> str:
    scoped_context = _career_context_for_node(node, career_context)
    # After repeated steer-backs (model_answer), stop merely re-asking — the
    # learner is stuck in a loop. Model a correct answer so they see exactly what
    # is wanted, then give a fresh small task (Wave 1.2b stall-loop break).
    tail = (
        "The learner has answered a different question two turns running — just "
        "re-steering is looping. Stop re-asking: MODEL one short, correct answer "
        "to the ACTUAL task yourself (a concrete example they can copy the shape "
        "of), then invite them to give their own version of THAT. End with the ask."
        if model_answer else
        "The learner wrote fluent English but answered a DIFFERENT question — "
        "they did not attempt this skill. Do NOT scold and do NOT scaffold down "
        "(they are clearly capable). Warmly acknowledge what they said in one "
        "line, then steer them back: restate the actual task in one clear "
        "sentence and ask them to try THAT now. End with the task."
    )
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_career_context_block(scoped_context)}"
        f"{_interview_prep_context_guard(node, scoped_context)}"
        f"{_gd_topic_guard(scoped_context)}"
        f"{_stance_block(behavior)}"
        f"Skill being practised: {node.skill}\n"
        f"The task / success criteria: {node.success_criteria}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"{_diagnosis_block(diagnosis)}"
        + tail
    )


def build_clarify_prompt(
    node: Concept,
    messages: list[dict],
    diagnosis: dict,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
    model_answer: bool = False,
    career_context: dict | None = None,
) -> str:
    scoped_context = _career_context_for_node(node, career_context)
    # After two stuck turns (model_answer), a young/low-fluency learner re-asked
    # the same way just stalls (live: 9 turns on the same letter 'B'). Give them a
    # complete example to copy instead of asking them to self-produce again
    # (Wave 1.2b stall-loop break).
    tail = (
        "The learner has now been stuck for two turns and still has not produced "
        "the answer. Do NOT just ask again. MODEL it for them: say one short, "
        "complete, correct example answer for THIS task yourself, in simple "
        "English, tell them it is now their turn to say one just like it, then ask. "
        "Keep it tiny and encouraging. End with the ask."
        if model_answer else
        "The learner's last message was not in clear English (it may be another "
        "language, empty, or unreadable). Do NOT scold, do NOT scaffold the skill "
        "down, and do NOT guess what they meant. Assume good faith. In one warm "
        "sentence say you want to make sure you understand them, then ask them to "
        "say it again in English. Briefly restate the task in one simple sentence "
        "so they know what to answer. End with that ask."
    )
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_career_context_block(scoped_context)}"
        f"{_interview_prep_context_guard(node, scoped_context)}"
        f"{_gd_topic_guard(scoped_context)}"
        f"{_stance_block(behavior)}"
        f"Skill being practised: {node.skill}\n"
        f"The task / success criteria: {node.success_criteria}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"{_diagnosis_block(diagnosis)}"
        + tail
    )


def build_ease_prompt(
    node: Concept,
    messages: list[dict],
    diagnosis: dict,
    memory_context: "list[dict] | str",
    coach: dict | None = None,
    behavior: BehaviorPack | None = None,
    weaknesses: list | None = None,
    career_context: dict | None = None,
) -> str:
    scoped_context = _career_context_for_node(node, career_context)
    return (
        f"{_persona(behavior)}\n"
        f"{_memory_block(memory_context, weaknesses)}\n"
        f"{_coach_block(coach)}"
        f"{_career_context_block(scoped_context)}"
        f"{_interview_prep_context_guard(node, scoped_context)}"
        f"{_gd_topic_guard(scoped_context)}"
        f"{_stance_block(behavior)}"
        f"Skill: {node.skill}\n"
        f"Easiest sub-step: {node.bridge_focus}\n\n"
        f"Recent conversation:\n{_history_block(messages)}\n\n"
        f"{_diagnosis_block(diagnosis)}"
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
        "Write a short, measured end-of-session note for the learner in <=180 "
        "tokens. It doubles as a memory note for the next session, so name "
        "things precisely. Write in the second person (\"you\"). Do not use generic praise. "
        "Do not claim readiness. Do not claim mastery. Avoid phrases like "
        "\"Great job\", \"Great session\", \"Strong answer\", \"mastered\", or "
        "\"ready for the next level\" unless the transcript explicitly proves sustained "
        "independent performance; if evidence is mixed, name the gap plainly. Output EXACTLY "
        "three labelled lines and nothing else:\n"
        "Strengths: <1-2 things they did well>\n"
        "Watch: <1-2 recurring errors to keep an eye on>\n"
        "Next focus: <the single concept to revisit first next time, named "
        "precisely so it can be re-tested in a warm-up>\n\n"
        f"Skill worked on: {node.skill}\n\n"
        f"Conversation:\n{_history_block(messages, limit=40, max_chars=_HISTORY_CHAR_BUDGET)}"
    )

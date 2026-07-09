"""bridge node — learner struggling: scaffold DOWN to a smaller sub-step.

Increments bridge_attempts. route_node enforces the 3-attempt cap (council fix
for the infinite-bridge loop): after BRIDGE_ATTEMPT_CAP failed bridges it routes
to teach instead, so this node never runs a 4th consecutive time.

Pre-authored exercises are selected by SEVERITY, not at random (P0-3c): the first
bridge serves a `standard` step, each repeat steps DOWN toward `foundational`, a
very weak answer starts at foundational immediately, and already-served ids are
skipped so the learner never gets the same exercise twice. For closed items
(fill_blank / MCQ) the answer key is stashed so the next turn grades the fill
deterministically (P0-3b) instead of through the key-blind LLM rubric.
"""
from app.ai.calls import GEMINI_FLASH, GenSpec
from app.ai.behaviors import behavior_for_value
from app.ai.prompts import build_bridge_prompt, coach_view
from app.content.registry import get_node, module_of
from app.content.schema import BridgeExercise
from app.services.content_personalization import render_gd_bridge_exercise

_BAND_ORDER = ["foundational", "standard", "stretch"]  # easiest -> hardest
_UNRELATED_ROLE_EXAMPLES = (
    "data analyst",
    "marketing manager",
    "sales associate",
    "hr manager",
    "project manager",
    "project coordinator",
    "customer success manager",
    "backend developer",
    "backend engineer",
    "frontend engineer",
    "software engineer",
    "software developer",
)

_SOFTWARE_ROLE_TERMS = (
    "software",
    "backend",
    "frontend",
    "full stack",
    "developer",
    "engineer",
    "api",
    "devops",
    "platform",
)

_SOFTWARE_PHRASE_REWRITES = (
    (
        "I used to struggle with delegating, so now I ___ at the start of every project.",
        "I used to over-explain technical trade-offs, so now I ___ before stakeholder updates.",
    ),
    (
        "assign clear owners to each task",
        "lead with the recommendation and one risk",
    ),
    (
        "a concrete corrective habit",
        "a concrete communication habit",
    ),
    (
        "Drills the weakness->mitigation stem by pairing a real weakness with a specific fix.",
        "Drills the weakness->mitigation stem with a software-relevant communication habit and a specific fix.",
    ),
    (
        "turns messy spreadsheets into dashboards leadership actually uses",
        "builds reliable APIs and production systems teams can trust",
    ),
    (
        "turning messy spreadsheets into dashboards leadership actually uses",
        "building reliable APIs and production systems teams can trust",
    ),
    (
        "keeps cross-team launches on schedule",
        "keeps production releases reliable and observable",
    ),
    (
        "shipped four product releases without a single missed deadline",
        "shipped backend releases without regressions by tightening reviews and rollout checks",
    ),
    (
        "move into a program lead role where I own delivery end to end",
        "grow into a role where I own backend reliability and product trade-offs end to end",
    ),
    (
        "In the end, we shipped the release two days early because I ___.",
        "The checkout reliability issue became easier to diagnose because I ___.",
    ),
    (
        "reorganized the testing schedule and unblocked the team",
        "built an observability dashboard and explained the retry trade-offs",
    ),
    (
        "Anchors the Result beat first, then forces the learner to name the Action that caused it.",
        "Anchors the Result beat with a backend example, then forces the learner to name the Action that caused it.",
    ),
    (
        "Our team was three weeks behind on a major client deliverable.",
        "The checkout flow had payment failures that support and engineering could not trace quickly.",
    ),
    (
        "I split the project into milestones and ran a daily ten-minute standup to catch blockers early.",
        "I built a reliability dashboard, added retry and error signals, and explained the trade-offs to support.",
    ),
    (
        "We delivered on time and the client renewed their contract.",
        "Support identified failed-payment patterns faster and engineering reduced repeat incidents.",
    ),
    (
        "When you ask how I'd handle a difficult client — do you mean a client who's unhappy with the work, or ___?",
        "When you ask how I'd handle a production incident - do you mean an API latency spike, or ___?",
    ),
    (
        "one who keeps changing the requirements",
        "a payment retry failure affecting checkouts",
    ),
    (
        "Practices the 'do you mean A or B' clarifier stem to narrow a vague prompt before answering.",
        "Practices the 'do you mean A or B' clarifier stem with a backend reliability scenario before answering.",
    ),
    (
        "The interviewer asks a vague 'How would you improve our product?' Which response is the sharpest first move?",
        "The interviewer asks a vague 'How would you improve our checkout reliability?' Which response is the sharpest first move?",
    ),
    (
        "Happy to — are you more interested in onboarding for new users, or retention for existing ones?",
        "Happy to - are you more interested in API latency during checkout, or failed payment retries?",
    ),
    (
        "I'll ask a deliberately vague question: 'Tell me how you'd grow this business.' Ask one sharp clarifying question to narrow it, then give a focused answer to the version you chose.",
        "I'll ask a deliberately vague question: 'Tell me how you'd improve this payment platform.' Ask one sharp clarifying question to narrow it, then give a focused answer to the version you chose.",
    ),
    (
        "By grow, do you mean new revenue from new customers, or more revenue from the ones we already have? If it's existing customers, I'd start with the accounts using only one feature, because that's usually the fastest upsell.",
        "By improve, do you mean checkout API reliability or payment-retry visibility? If it is reliability, I would start with latency/error dashboards and rollback-safe release checks.",
    ),
    (
        "I cut report time by ___% by automating the weekly export.",
        "I cut incident triage time by ___% by automating checkout reliability signals.",
    ),
    (
        "any number (e.g. 40)",
        "any reliability number (e.g. 40)",
    ),
    (
        "Forces a measurable result into a vague achievement.",
        "Forces a measurable backend reliability result into a vague achievement.",
    ),
    (
        "I grew sign-ups 30% in two quarters, adding ~1,200 users.",
        "I reduced checkout incident triage time 40% by joining payment errors, retries, and database latency in one dashboard.",
    ),
    (
        "I worked really hard on growth.",
        "I worked really hard on reliability.",
    ),
    (
        "Growth went up a lot under me.",
        "Reliability got a lot better after my changes.",
    ),
    (
        "Instead of saying I improved support, I'd say I rewrote our help docs and first-response time dropped from about a day to under two hours, which cut repeat tickets by roughly a quarter.",
        "Instead of saying I improved reliability, I'd say I added checkout error signals and reduced incident triage from about 40 minutes to under 10 minutes.",
    ),
)

_ROLE_FAMILY_DOMAIN_COPY = {
    "hr_people": {
        "pitch_action": "strengthens hiring, onboarding, and employee trust",
        "system": "people processes across growing teams",
        "outage": "a hiring workflow stalled during a critical ramp",
        "billing_error": "a payroll or policy error that would have affected employee trust",
        "metering": "people analytics and HR process design",
        "checkout": "employee onboarding",
        "payment_code": "employee-data workflows",
        "release": "people-program rollout",
    },
    "business_management": {
        "pitch_action": "turns messy execution into clear operating plans",
        "system": "operating plans across cross-functional teams",
        "outage": "a launch plan hit a serious delivery risk",
        "billing_error": "a reporting error that would have misled leadership planning",
        "metering": "operating metrics and delivery systems",
        "checkout": "customer onboarding",
        "payment_code": "critical process decisions",
        "release": "business rollout",
    },
    "sales_customer": {
        "pitch_action": "turns customer conversations into repeatable revenue motion",
        "system": "customer pipelines and renewal processes",
        "outage": "a key customer escalation happened before renewal",
        "billing_error": "a contract-pricing issue that would have confused customers",
        "metering": "customer usage and account-growth systems",
        "checkout": "customer conversion",
        "payment_code": "customer-facing workflows",
        "release": "customer rollout",
    },
    "operations_other": {
        "pitch_action": "makes daily operations more reliable and measurable",
        "system": "operating processes teams can trust",
        "outage": "an operations process broke during peak demand",
        "billing_error": "a process error that would have delayed service for customers",
        "metering": "operational metrics and reliability systems",
        "checkout": "service delivery",
        "payment_code": "critical operating workflows",
        "release": "operations rollout",
    },
}


def _band_index(band: str | None) -> int:
    """Map a band label to its difficulty rank; None/unknown reads as standard."""
    try:
        return _BAND_ORDER.index(band)
    except (ValueError, TypeError):
        return 1


def select_bridge_exercise(
    exercises: list[BridgeExercise],
    bridge_attempts: int,
    served_ids: list[str],
    score: float,
) -> BridgeExercise:
    """Pick the next bridge exercise by severity (pure, testable).

    Targets a difficulty band that starts at `standard` and steps DOWN one band
    per prior bridge attempt (so a repeatedly-stuck learner is scaffolded harder),
    and clamps to `foundational` immediately for a very weak (<0.2) answer.
    Already-served ids are skipped; once every exercise has been served, repeats
    are allowed (still preferring the target band)."""
    served = set(served_ids or [])
    target = 1 - bridge_attempts          # 0 attempts -> standard, then step down
    if score < 0.2:
        target = min(target, 0)           # very weak -> foundational now
    target = max(0, min(len(_BAND_ORDER) - 1, target))

    unserved = [e for e in exercises if e.id not in served]
    pool = unserved or list(exercises)    # all served -> allow repeats

    def sort_key(e: BridgeExercise):
        bi = _band_index(e.band)
        # exact target band first, then bands at/under target (easier), then by
        # absolute distance — never overshoot to a harder band when an easier fits.
        return (abs(bi - target), bi > target, bi)

    return sorted(pool, key=sort_key)[0]


def _career_label(career_context: dict | None) -> str:
    if not career_context:
        return ""
    primary = str(career_context.get("primary_role") or "").strip()
    if primary:
        return primary
    roles = [
        str(role).strip()
        for role in career_context.get("target_roles", [])
        if str(role).strip()
    ]
    return roles[0] if roles else ""


def _is_software_context(career_context: dict | None, role: str) -> bool:
    if not career_context and not role:
        return False
    family = str((career_context or {}).get("role_family") or "").lower()
    haystack = " ".join(
        [
            family,
            role,
            *[
                str(item)
                for item in (career_context or {}).get("target_roles", [])
            ],
        ]
    ).lower()
    return family == "software_technical" or any(term in haystack for term in _SOFTWARE_ROLE_TERMS)


def _article_for_role(role: str) -> str:
    clean = role.strip().lower()
    if clean.startswith(("a", "e", "i", "o", "u", "hr ", "mba ")):
        return "an"
    return "a"


def _role_family_domain_rewrites(career_context: dict | None, role: str) -> tuple[tuple[str, str], ...]:
    family = str((career_context or {}).get("role_family") or "").lower()
    if family == "software_technical":
        return ()
    copy = _ROLE_FAMILY_DOMAIN_COPY.get(family)
    if not copy:
        return ()
    display_role = role or {
        "hr_people": "people professional",
        "business_management": "business manager",
        "sales_customer": "customer-facing professional",
        "operations_other": "operations professional",
    }.get(family, "career professional")
    article = _article_for_role(display_role)
    return (
        (
            "I'm a backend developer who builds payment systems for high-traffic apps.",
            f"I'm {article} {display_role} who {copy['pitch_action']}.",
        ),
        (
            "I'm a backend developer who ___ payment systems for high-traffic apps.",
            f"I'm {article} {display_role} who ___ {copy['system']}.",
        ),
        (
            "payment systems for high-traffic apps",
            copy["system"],
        ),
        (
            "payment systems",
            copy["system"],
        ),
        (
            "our server went down during a launch",
            copy["outage"],
        ),
        (
            "server went down during a launch",
            copy["outage"],
        ),
        (
            "billing error that would have overcharged 200 customers",
            copy["billing_error"],
        ),
        (
            "billing platforms end to end",
            f"{copy['metering']} end to end",
        ),
        (
            "metering systems",
            copy["metering"],
        ),
        (
            "checkout",
            copy["checkout"],
        ),
        (
            "payment code",
            copy["payment_code"],
        ),
        (
            "backend releases",
            f"{copy['release']}s",
        ),
        (
            "production releases",
            f"{copy['release']}s",
        ),
        (
            "backend reliability and product trade-offs",
            f"{copy['system']} and stakeholder trade-offs",
        ),
    )


def _gd_topic_phrase(topic: str) -> str:
    """Turn a question-style GD topic into a sentence-safe noun phrase."""
    clean = topic.strip().strip("\"'").strip()
    clean = clean[:-1].strip() if clean.endswith("?") else clean
    lower = clean.lower()
    if not lower.startswith("should "):
        return clean

    rest = clean[len("Should "):].strip()
    words = rest.split()
    if "be" in [word.lower() for word in words]:
        be_index = next(i for i, word in enumerate(words) if word.lower() == "be")
        if be_index > 0:
            subject = " ".join(words[:be_index])
            remainder = " ".join(words[be_index + 1:])
            return " ".join(part for part in (subject, "being", remainder) if part).strip()
    if len(words) < 2:
        return rest
    subject, verb, remainder = words[0], words[1], " ".join(words[2:])
    ing = {
        "abolish": "abolishing",
        "allow": "allowing",
        "ban": "banning",
        "be": "being",
        "do": "doing",
        "get": "getting",
        "have": "having",
        "make": "making",
        "replace": "replacing",
        "require": "requiring",
        "teach": "teaching",
        "use": "using",
    }.get(verb.lower())
    if not ing:
        return rest
    return " ".join(part for part in (subject, ing, remainder) if part).strip()


def personalize_bridge_exercise(
    exercise: BridgeExercise,
    career_context: dict | None,
    module_id: str,
) -> BridgeExercise:
    """Rewrite career scaffold surface examples without touching grading fields."""
    role = _career_label(career_context)
    topics = [
        str(topic).strip()
        for topic in (career_context or {}).get("gd_topics", [])
        if str(topic).strip()
    ]
    if not role and not topics:
        return exercise
    if module_id == "group_discussion" and topics:
        rendered = render_gd_bridge_exercise(exercise, exercise.id.rsplit("_bx", 1)[0], career_context)
        if rendered.model_dump() != exercise.model_dump():
            return rendered
    is_software = _is_software_context(career_context, role)

    def rewrite(text: str, *, sentence_field: bool = False) -> str:
        out = text
        for source, target in _role_family_domain_rewrites(career_context, role):
            out = out.replace(source, target)
            out = out.replace(source.title(), target)
        if role:
            role_lower = role.lower()
            for sample in _UNRELATED_ROLE_EXAMPLES:
                if sample.lower() in role_lower:
                    continue
                out = out.replace(sample, role)
                out = out.replace(sample.title(), role.title())
        if is_software:
            for source, target in _SOFTWARE_PHRASE_REWRITES:
                out = out.replace(source, target)
                out = out.replace(source.title(), target)
        if module_id == "group_discussion" and topics:
            topic_label = topics[0]
            topic_phrase = _gd_topic_phrase(topic_label) if sentence_field else topic_label
            out = out.replace(
                "that remote work helps companies more than it hurts them",
                f"{topic_phrase} would help more than it hurts",
            )
            out = out.replace(
                "remote work helps companies more than it hurts them",
                f"{topic_phrase} would help more than it hurts",
            )
            out = out.replace("remote work", topic_phrase)
            out = out.replace("Remote work", topic_phrase)
            out = out.replace(
                "the cost angle matters just as much as the time saved",
                f"one trade-off in {topic_phrase} matters just as much as the benefit people mentioned",
            )
            out = out.replace(
                "quick point about cost",
                f"quick point about {topic_phrase}",
            )
            out = out.replace(
                "whether exams should be scrapped",
                topic_phrase,
            )
            out = out.replace(
                "you're right that exams cause stress, and I'd add that they also reward memorising over real understanding",
                f"you're right that {topic_phrase} has benefits, and I'd add one trade-off we should weigh",
            )
            out = out.replace(
                "whether the budget should grow at all",
                topic_phrase,
            )
            out = out.replace(
                "the real question is whether the budget should grow at all",
                f"the real question is {topic_phrase}",
            )
        return out

    return exercise.model_copy(
        update={
            "sentence": rewrite(exercise.sentence, sentence_field=True),
            "hint": rewrite(exercise.hint),
            "context": rewrite(exercise.context),
            "answer_key": rewrite(exercise.answer_key, sentence_field=True),
            "accept": [rewrite(item, sentence_field=True) for item in exercise.accept] if exercise.accept else None,
            "options": [rewrite(item, sentence_field=True) for item in exercise.options] if exercise.options else None,
        }
    )


async def bridge_node(state: dict) -> dict:
    node = get_node(state["competency_node"])

    # Pre-authored scaffolding: if the curriculum defines bridge exercises, serve
    # one (severity-selected, de-duplicated) and skip the LLM generation.
    if node.bridge_exercises:
        served = state.get("served_bridge_ids", [])
        exercise = select_bridge_exercise(
            node.bridge_exercises,
            state.get("bridge_attempts", 0),
            served,
            state.get("last_eval_score", 0.0),
        )
        exercise = personalize_bridge_exercise(
            exercise,
            state.get("career_context") or {},
            module_of(state["competency_node"]),
        )
        out = {
            "pending_game": exercise.model_dump(),
            "served_bridge_ids": list(served) + [exercise.id],
            "last_route": "bridge",
            "bridge_attempts": state.get("bridge_attempts", 0) + 1,
            "active_prompt_attempt_type": "scaffolded",
        }
        # Stash the key so the NEXT turn grades the fill against it — but ONLY for
        # closed items. A `spoken` bridge is an open production task with no single
        # correct string, so it must fall through to the LLM evaluator as before.
        if exercise.type in ("fill_blank", "multiple_choice"):
            out["pending_answer_key"] = {
                "type": exercise.type,
                "answer_key": exercise.answer_key,
                "accept": exercise.accept,
                "options": exercise.options,
            }
        return out

    # Fallback: prompt the LLM to generate a bridge step on the fly.
    prompt = build_bridge_prompt(
        node,
        state.get("messages", []),
        state.get("last_diagnosis", {}),
        state.get("memory_context", ""),
        coach_view(state),
        behavior=behavior_for_value(state.get("task_type", "")),
        weaknesses=state.get("weakness_context", []),
        career_context=state.get("career_context") or {},
    )
    spec = GenSpec(
        provider="gemini", model=GEMINI_FLASH, prompt=prompt, kind="bridge"
    )
    return {
        "pending": spec,
        "last_route": "bridge",
        "bridge_attempts": state.get("bridge_attempts", 0) + 1,
        "active_prompt_attempt_type": "scaffolded",
    }

"""Topic-aware deterministic text for GD assessment repairs.

These fallbacks are visible to learners when model output is invalid, repeated,
or unavailable. They must still sound like group-discussion participants, not
generic interview prompts.
"""
from __future__ import annotations

import re


def _is_moderator(speaker_id: str, role_type: str) -> bool:
    speaker = speaker_id.lower()
    role = role_type.lower()
    return role == "moderator" or "moderator" in speaker


def _is_remote_work_topic(topic: str) -> bool:
    lower = topic.lower()
    return any(
        re.search(pattern, lower)
        for pattern in (
            r"\bremote[-\s]?first\b",
            r"\bremote\s+work\b",
            r"\bwork\s+from\s+home\b",
            r"\bhybrid\s+work\b",
            r"\bdistributed\s+(?:work|teams?|workforce)\b",
            r"\bremote\s+(?:default|teams?|jobs?|roles?|employees?|workers?)\b",
            r"\bdefault\s+remote\b",
        )
    )


def _is_ai_topic(topic: str) -> bool:
    lower = topic.lower()
    return any(marker in lower for marker in (" ai ", "artificial intelligence", "automation", "generative ai"))


def _is_ai_audit_topic(topic: str) -> bool:
    lower = topic.lower()
    return (
        any(marker in lower for marker in (" ai ", "artificial intelligence", "algorithmic", "automated system"))
        and any(marker in lower for marker in ("audit", "impact assessment", "regulat", "oversight"))
    )


def gd_topic_phrase(topic: str) -> str:
    """Normalize a GD motion into a phrase that fits inside a spoken sentence."""
    clean = (topic or "").strip().strip("\"'").strip()
    if clean.endswith("?"):
        clean = clean[:-1].strip()
    lower = clean.lower()
    if lower.startswith("should "):
        rest = clean[len("Should "):].strip()
        words = rest.split()
        if "be" in [word.lower() for word in words]:
            be_index = next(i for i, word in enumerate(words) if word.lower() == "be")
            if be_index > 0:
                subject = " ".join(words[:be_index])
                remainder = " ".join(words[be_index + 1:])
                return " ".join(part for part in (subject, "being", remainder) if part).strip()
        if len(words) >= 2:
            ing_map = {
                "abolish": "abolishing",
                "allow": "allowing",
                "ban": "banning",
                "do": "doing",
                "get": "getting",
                "have": "having",
                "make": "making",
                "regulate": "regulating",
                "replace": "replacing",
                "require": "requiring",
                "teach": "teaching",
                "use": "using",
            }
            for verb_index, verb in enumerate(words[1:], start=1):
                ing = ing_map.get(verb.lower())
                if not ing:
                    continue
                subject = " ".join(words[:verb_index])
                remainder = " ".join(words[verb_index + 1:])
                return " ".join(part for part in (subject, ing, remainder) if part).strip()
        return rest or clean
    return clean or "this topic"


def gd_persona_fallback_text(topic: str, speaker_id: str, role_type: str = "") -> str:
    """Return a natural GD contribution for a persona and topic."""
    topic = topic.strip() or "this topic"
    topic_phrase = gd_topic_phrase(topic)
    speaker_id = (speaker_id or "").strip()
    role_type = (role_type or "").strip()
    if _is_moderator(speaker_id, role_type):
        return (
            f"Stay with {topic}. One concrete example or risk is enough for the "
            "next contribution; keep the panel reacting to the motion itself."
        )

    if _is_remote_work_topic(topic):
        if speaker_id == "aggressive_challenger":
            return (
                f"I would push back on {topic_phrase}: making remote the default can make junior employees, "
                "new hires, and quieter contributors invisible unless mentoring, feedback, and "
                "escalation paths are deliberate."
            )
        if speaker_id == "data_driven_analyst":
            return (
                f"For {topic_phrase}, I would trust the argument only if hiring reach, "
                "time-to-productivity, decision latency, attrition, engagement, and delivery "
                "quality move in the same direction."
            )
        if speaker_id == "consensus_builder":
            return (
                f"I can support {topic_phrase} as remote-first, but only with planned onboarding, "
                "complex-decision rituals, documentation standards, and periodic trust resets."
            )
        if speaker_id == "quiet_expert":
            return (
                f"For me, {topic_phrase} succeeds or fails on operating discipline: decision records, "
                "mentorship cadence, async norms, and documentation quality decide whether remote stays fair."
            )
        if speaker_id == "devils_advocate":
            return (
                f"The counter-position on {topic_phrase} is that flexibility can weaken trust and informal "
                "learning if leaders do not protect onboarding, conflict surfacing, and cross-team ties."
            )
        return (
            f"The group should treat {topic_phrase} as conditional: prove access improves while mentoring, "
            "trust, decision latency, and delivery quality do not degrade."
        )

    if _is_ai_audit_topic(topic):
        if speaker_id == "aggressive_challenger":
            return (
                f"The strongest challenge to {topic_phrase} is checkbox compliance: a slow audit with weak "
                "technical expertise can delay useful systems without catching the failures that matter."
            )
        if speaker_id == "data_driven_analyst":
            return (
                f"For {topic_phrase}, the threshold should combine severity-weighted error rates, subgroup gaps, "
                "appeal reversals, and an independent re-test before deployment; publishing only an average is not enough."
            )
        if speaker_id == "consensus_builder":
            return (
                f"The hardest balance in {topic_phrase} is disclosure: publish the affected uses, headline risks, "
                "and remediation deadline, while giving an independent regulator protected access to technical details."
            )
        if speaker_id == "quiet_expert":
            return (
                f"For {topic_phrase}, audit scope and evaluator independence matter more than the label; require "
                "post-deployment monitoring because a one-time pre-release review will miss changing data and behavior."
            )
        if speaker_id == "devils_advocate":
            return (
                f"The counter-case against {topic_phrase} is that compliance cost can entrench large incumbents and "
                "push smaller deployers out unless audit depth scales with system risk and public exposure."
            )
        return (
            f"The workable middle ground on {topic_phrase} is risk-tiered review, independent access to evidence, "
            "a public findings summary, and a deadline for remediation before deployment."
        )

    if _is_ai_topic(topic):
        if speaker_id == "aggressive_challenger":
            return (
                f"I would challenge {topic_phrase} on accountability: speed is not progress if errors, bias, "
                "or unclear ownership reach users before review catches them."
            )
        if speaker_id == "data_driven_analyst":
            return (
                f"I would compare {topic_phrase} before and after adoption: quality, review time, "
                "error rates, escalations, and user outcomes all need to improve, not just speed."
            )
        if speaker_id == "consensus_builder":
            return (
                f"I can accept {topic_phrase} where it is human-supervised: use it for speed, but "
                "keep audit trails, escalation, and a rollback threshold visible."
            )
        if speaker_id == "quiet_expert":
            return (
                f"My concern on {topic_phrase} is review design: clear ownership, exception handling, "
                "and quality checks decide whether automation is trustworthy."
            )
        if speaker_id == "devils_advocate":
            return (
                f"The opposing case on {topic_phrase} is that efficiency can mask bad judgment unless people "
                "know when to override the system and who is accountable."
            )

    if speaker_id == "aggressive_challenger":
        return (
            f"I would push back on {topic_phrase} where rollout moves faster than safeguards; exclusion, "
            "trust failures, or weak accountability can appear only after harm is hard to reverse."
        )
    if speaker_id == "data_driven_analyst":
        return (
            f"I would judge {topic_phrase} by upside and failure together: adoption, complaint "
            "trends, inclusion, cost, reliability, and outcomes should move together."
        )
    if speaker_id == "consensus_builder":
        return (
            f"I can support {topic_phrase} conditionally: keep the benefit, but pair it with access "
            "safeguards, measurable thresholds, and named accountability."
        )
    if speaker_id == "quiet_expert":
        return (
            f"My vote on {topic_phrase} depends on implementation quality; clear rules, support paths, "
            "escalation, and safeguards decide whether the idea works in practice."
        )
    if speaker_id == "devils_advocate":
        return (
            f"The counter-position on {topic_phrase} is that convenience is not enough unless accountability, "
            "access, and trust are designed into the system from the start."
        )
    return (
        f"The next useful contribution on {topic_phrase} is to weigh the benefit against the strongest "
        "implementation risk, then name the condition under which the motion should stand."
    )


def gd_integrity_fallback_text(topic: str, *, is_moderator: bool = False) -> str:
    topic = topic.strip() or "this topic"
    if is_moderator:
        return (
            f"Let's keep the discussion grounded in {topic}. Put one concrete risk, "
            "example, or metric on the table before bringing in another panel voice."
        )
    if _is_remote_work_topic(topic):
        return (
            f"On {topic}, the defensible line is not remote by faith; mentoring quality, "
            "decision latency, trust, and time-to-productivity have to hold up before "
            "remote-first is treated as settled."
        )
    if _is_ai_audit_topic(topic):
        return (
            f"On {topic}, the defensible threshold combines severity-weighted failures, subgroup gaps, "
            "independent access to evidence, and a remediation deadline rather than a compliance label alone."
        )
    return (
        f"On {topic}, I would not treat the claim as settled until one visible example "
        "or metric shows the benefit without hiding the strongest implementation risk."
    )


def gd_repeat_fallbacks(topic: str, *, is_moderator: bool = False) -> tuple[str, ...]:
    topic = topic.strip() or "this topic"
    if is_moderator:
        return (
            "Hold the motion steady: {topic_sentence} Put the stakeholder carrying the biggest cost beside the stakeholder gaining the most, then continue from that tension.",
            "Keep the motion visible: {topic_sentence} Bring the implementation risk, the safeguard, and the failure signal into the same turn.",
            "Reset the room around the motion: {topic_sentence} Weigh the strongest argument on each side, then state the condition that would change the position.",
        )
    if _is_remote_work_topic(topic):
        return (
            "I'd split the remote-work debate into flexibility and weak ties: support holds only if mentoring, conflict surfacing, and trust are deliberately designed.",
            "If {topic} improves hiring reach but worsens time-to-productivity, decision latency, attrition, or delivery quality, the default is failing.",
            "My support for {topic} depends on documentation and manager cadence making quiet contributors visible; otherwise the default rewards people already fluent in async work.",
            "A workable compromise is remote-first with scheduled onboarding resets, complex-decision rituals, and a trigger for in-person collaboration when trust drops.",
        )
    if _is_ai_audit_topic(topic):
        return (
            "I'd split {topic} into audit depth and disclosure: the review must expose affected uses and severe risks without publishing attack-sensitive technical details.",
            "For {topic}, a credible pass threshold combines subgroup error gaps, severity-weighted failures, appeal reversals, and an independent re-test.",
            "The strongest implementation risk in {topic} is checkbox compliance, so evaluator independence, remediation deadlines, and liability must be visible.",
            "The synthesis on {topic} is risk-tiered oversight: public findings, protected regulator access, post-deployment monitoring, and a trigger for re-audit.",
        )
    return (
        "I'd split {topic} into promise and rollout risk: support only works when the group names who benefits, who is exposed, and when to pause.",
        "I would judge {topic} by adoption and harm together; if complaints, exclusion, cost, or reliability worsen, the proposal is losing legitimacy.",
        "My support for {topic} depends on a protected exception path; otherwise a default becomes compulsion for the people least able to absorb failure.",
        "The synthesis I hear on {topic} is conditional: keep the efficiency gain, but tie it to exception handling, named ownership, and a visible correction trigger.",
        "The overlooked risk in {topic} is power asymmetry; people closest to failure often have the least authority to object, so rollout has to start from their constraints.",
        "The benefit case for {topic} needs a hard success metric and a rollback condition, because otherwise the group is debating intentions instead of outcomes.",
        "A workable compromise would make {topic} reversible: adopt it where it works, but switch paths when reliability, access, or trust indicators drop.",
        "I would not treat convenience as proof of success; the group should judge {topic} by the users who are harmed when the easy path fails.",
        "The accountability gap in {topic} is the pressure point: the proposal is stronger only if someone owns intervention when convenience starts creating harm.",
        "I would rank trust and access before speed on {topic}; adoption numbers without legitimacy will not hold once edge cases start surfacing.",
    )

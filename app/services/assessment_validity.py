"""Validation helpers for assessment-turn model output."""
from __future__ import annotations

import re
from typing import Any


_MODEL_ANSWER_PATTERNS = (
    re.compile(r"\bi would\s+(?:start|begin|frame|approach|handle|explain|say|respond|structure)\b", re.I),
    re.compile(r"\bmy answer would\b", re.I),
    re.compile(r"\ba strong answer would\b", re.I),
)
_QUESTION_START_RE = re.compile(
    r"^\s*(?:what|how|why|when|where|which|can|could|would|should|do|does|did|is|are|will|please|tell|share|give|explain)\b",
    re.I,
)
_LEARNER_EVIDENCE_DEMAND_RE = re.compile(
    r"\b(?:can|could|would|will|please|tell|share|give|explain|what|which|how)\b"
    r"[^?]{0,120}\b(?:you|learner|metric|metrics|data|evidence|study|studies|report|reports|case|example|examples|prove|proves|show|showing)\b"
    r"[^?]{0,120}\?",
    re.I,
)
_GD_PERSONA_ADDRESS_RE = re.compile(
    r"^\s*(?:data[-\s]?driven\s+analyst|aggressive\s+challenger|consensus\s+builder|quiet\s+expert|devil'?s\s+advocate|moderator)\s*,",
    re.I,
)
_GD_LEARNER_FACING_QUESTION_RE = re.compile(
    r"\b(?:what\s+(?:is|are)\s+your|how\s+(?:do|would)\s+you|"
    r"(?:can|could|would|will|should|do)\s+you|your\s+(?:stance|view|answer|example|evidence|metric|safeguard))\b",
    re.I,
)
_GD_FORMULAIC_META_RE = re.compile(
    r"(?:"
    r"(?:a|the)\s+new\s+angle\s+is\b|"
    r"(?:i(?:'ll| will)|let\s+me)\s+shift\s+the\s+angle\b|"
    r"the\s+strongest\s+middle\s+ground\s+is\b|"
    r"the\s+key\s+trade[-\s]?off\s+(?:on|in|for)\b|"
    r"\bthe\s+real\s+issue\s+here\s+is\b|"
    r"\ba\s+balanced\s+way\s+to\s+see\s+this\s+is\b|"
    r"\bthe\s+practical\s+lens\s+is\b|"
    r"\bto\s+(?:summarize|synthesi[sz]e)\s+the\s+floor\b"
    r")",
    re.I,
)
_GD_PANELIST_FLOOR_CONTROL_RE = re.compile(
    r"(?:"
    r"\b(?:data[-\s]?driven\s+analyst|aggressive\s+challenger|consensus\s+builder|"
    r"quiet\s+expert|devil'?s\s+advocate|moderator)\s*,?\s+"
    r"(?:please\s+)?(?:respond|reply|challenge|take|weigh\s+in|jump\s+in|"
    r"come\s+in|share|explain|address|what\s+do\s+you\s+think|"
    r"how\s+would\s+you|can\s+you|could\s+you)\b|"
    r"\b(?:bring\s+in|hear\s+from|invite|ask|call\s+on|let'?s\s+hear\s+from)\s+"
    r"(?:data[-\s]?driven\s+analyst|aggressive\s+challenger|consensus\s+builder|"
    r"quiet\s+expert|devil'?s\s+advocate|moderator)\b|"
    r"\b(?:data[-\s]?driven\s+analyst|aggressive\s+challenger|consensus\s+builder|"
    r"quiet\s+expert|devil'?s\s+advocate|moderator)\s+should\s+"
    r"(?:respond|reply|challenge|take|weigh\s+in|jump\s+in|come\s+in|address)\b"
    r")",
    re.I,
)

_REQUEST_BEFORE_RE = re.compile(
    r"\b(?:ask|invite|hear\s+from|bring\s+in|call\s+on|let)\b",
    re.I,
)
_REQUEST_AFTER_FIRST_WORDS = {
    "what",
    "how",
    "why",
    "when",
    "where",
    "which",
    "can",
    "could",
    "would",
    "should",
    "do",
    "does",
    "did",
    "is",
    "are",
    "will",
    "please",
    "respond",
    "reply",
    "challenge",
    "tell",
    "share",
    "give",
    "explain",
}
_REQUEST_AFTER_PHRASES = {
    ("what", "do", "you", "think"),
    ("what", "is", "your", "view"),
    ("what", "is", "your", "opinion"),
    ("what", "is", "your", "take"),
    ("your", "view"),
    ("your", "opinion"),
    ("your", "take"),
}


def roster_by_id(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(persona.get("speaker_id") or ""): dict(persona)
        for persona in plan.get("active_personas") or []
        if isinstance(persona, dict) and persona.get("speaker_id")
    }


def moderator_persona(plan: dict[str, Any]) -> dict[str, Any]:
    roster = list(roster_by_id(plan).values())
    for persona in roster:
        role = str(persona.get("role_type") or "").lower()
        speaker_id = str(persona.get("speaker_id") or "").lower()
        name = str(persona.get("name") or "").lower()
        if role == "moderator" or "moderator" in speaker_id or "moderator" in name:
            return persona
    return roster[0] if roster else {"speaker_id": "moderator", "name": "Moderator", "role_type": "moderator"}


def first_debater(plan: dict[str, Any], *, avoid: str = "") -> dict[str, Any]:
    roster = list(roster_by_id(plan).values())
    for persona in roster:
        speaker_id = str(persona.get("speaker_id") or "")
        role = str(persona.get("role_type") or "").lower()
        if speaker_id == avoid:
            continue
        if role != "moderator" and "moderator" not in speaker_id.lower():
            return persona
    return moderator_persona(plan)


def speaker_is_active(plan: dict[str, Any], speaker_id: str) -> bool:
    return speaker_id in roster_by_id(plan)


def available_debater_names(plan: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for persona in roster_by_id(plan).values():
        role = str(persona.get("role_type") or "").lower()
        if role == "moderator":
            continue
        name = str(persona.get("name") or persona.get("speaker_id") or "").strip()
        if name:
            names.append(name)
    return names


def _normalized_words(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (value or "").lower()))


def _speaker_aliases_for_request(persona: dict[str, Any]) -> list[str]:
    values = [
        str(persona.get("name") or ""),
        str(persona.get("speaker_id") or "").replace("_", " "),
    ]
    aliases: list[str] = []
    for value in values:
        normalized = _normalized_words(value)
        if normalized and normalized not in aliases:
            aliases.append(normalized)
    return aliases


def _request_after_context(after: str) -> bool:
    words = after.split()
    if not words:
        return False
    # A possessive mention, e.g. "Aggressive Challenger's risk framing", is
    # argument content rather than an instruction for that persona to speak.
    if words[0] == "s":
        return False
    if words[0] in _REQUEST_AFTER_FIRST_WORDS:
        return True
    if "please" in words[:4]:
        return True
    for phrase in _REQUEST_AFTER_PHRASES:
        if tuple(words[:len(phrase)]) == phrase:
            return True
    return False


def explicit_requested_speaker_id(plan: dict[str, Any], learner_text: str) -> str:
    """Return the active roster speaker explicitly asked to respond, if any.

    This is intentionally narrower than semantic routing. It catches concrete
    UI/live phrasing like "Aggressive Challenger, what is the risk?" without
    treating ordinary mentions like "I agree with Data-Driven Analyst" as floor
    control.
    """
    segments = [
        segment
        for segment in re.split(r"(?<=[.!?])\s+|\n+", learner_text or "")
        if segment.strip()
    ]
    hits: list[str] = []
    for segment in segments:
        normalized = _normalized_words(segment)
        if not normalized:
            continue
        words = normalized.split()
        for speaker_id, persona in roster_by_id(plan).items():
            for alias in _speaker_aliases_for_request(persona):
                alias_words = alias.split()
                if not alias_words:
                    continue
                for index in range(0, len(words) - len(alias_words) + 1):
                    if words[index:index + len(alias_words)] != alias_words:
                        continue
                    before = " ".join(words[max(0, index - 8):index])
                    after = " ".join(words[index + len(alias_words):index + len(alias_words) + 14])
                    if _REQUEST_BEFORE_RE.search(before) or _request_after_context(after):
                        hits.append(speaker_id)
    unique_hits = []
    for speaker_id in hits:
        if speaker_id not in unique_hits:
            unique_hits.append(speaker_id)
    return unique_hits[-1] if len(unique_hits) == 1 else ""


def next_active_debater(plan: dict[str, Any], *, after: str = "", avoid: str = "") -> dict[str, Any]:
    debaters = [
        persona for persona in roster_by_id(plan).values()
        if str(persona.get("role_type") or "").lower() != "moderator"
        and "moderator" not in str(persona.get("speaker_id") or "").lower()
    ]
    if not debaters:
        return moderator_persona(plan)
    ids = [str(persona.get("speaker_id") or "") for persona in debaters]
    start = ids.index(after) + 1 if after in ids else 0
    for offset in range(len(debaters)):
        persona = debaters[(start + offset) % len(debaters)]
        if persona.get("speaker_id") != avoid:
            return persona
    return debaters[0]


def _speaker_tokens(persona: dict[str, Any]) -> list[str]:
    values = [
        str(persona.get("name") or ""),
        str(persona.get("speaker_id") or "").replace("_", " "),
    ]
    return [value.strip() for value in values if value.strip()]


def low_confidence_persona_request(analysis: dict[str, Any]) -> bool:
    routing = str(analysis.get("routing_case") or "")
    requested = str(analysis.get("requested_next_speaker") or "").strip()
    confidence = float(analysis.get("request_confidence") or 0.0)
    return bool(requested and routing in {"request_only", "reply_and_request"} and confidence < 0.7)


def self_label_or_meta_text(text: str, persona: dict[str, Any]) -> bool:
    lower = (text or "").strip().lower()
    if not lower:
        return False
    for token in _speaker_tokens(persona):
        token_lower = token.lower()
        if re.match(rf"^(?:as\s+)?{re.escape(token_lower)}\s*[:,\-]", lower):
            return True
        if re.match(rf"^as\s+(?:the\s+|a\s+|an\s+)?{re.escape(token_lower)}\b", lower):
            return True
        if re.match(rf"^{re.escape(token_lower)}\s*,\s*(?:please|can|could|respond|ask|take)\b", lower):
            return True
        if re.match(rf"^{re.escape(token_lower)}\s*,\s*(?:you|the learner|learner)\b", lower):
            return True
    return False


def gd_panelist_ask_only_text(text: str, persona: dict[str, Any]) -> bool:
    """True when a GD participant turn becomes an interview-style prompt.

    GD debaters contribute, challenge and synthesize. The moderator is allowed
    to steer the room; debaters should not demand learner proof, cross-examine,
    or hand the floor around as if this were an interview.
    """
    role_type = str(persona.get("role_type") or "").lower()
    speaker_id = str(persona.get("speaker_id") or "").lower()
    name = str(persona.get("name") or "").lower()
    if role_type == "moderator" or "moderator" in speaker_id or "moderator" in name:
        return False
    value = " ".join(str(text or "").split())
    if not value or "?" not in value:
        return bool(_GD_PANELIST_FLOOR_CONTROL_RE.search(value))
    if _GD_PANELIST_FLOOR_CONTROL_RE.search(value):
        return True
    sentence_chunks = [
        chunk.strip()
        for chunk in re.split(r"(?<=[.!?])\s+", value)
        if chunk.strip()
    ]
    if not sentence_chunks:
        return False
    question_indexes = [index for index, chunk in enumerate(sentence_chunks) if chunk.endswith("?")]
    if not question_indexes:
        return False
    if len(question_indexes) > 1:
        return True
    question_index = question_indexes[0]
    if question_index == 0:
        same_sentence_prefix = re.match(
            r"^(?P<prefix>.+?)(?:[,;:]\s*|\s+)"
            r"(?:but|however|yet)\s+"
            r"(?:what|why|which|how|who|where|when|can|could|should|would)\b",
            sentence_chunks[0],
            re.IGNORECASE,
        )
        if not same_sentence_prefix:
            return True
        prefix_words = re.findall(
            r"[A-Za-z0-9']+",
            same_sentence_prefix.group("prefix"),
        )
        return len(prefix_words) < 6
    substantive_before_question = any(
        len(re.findall(r"[A-Za-z0-9']+", chunk)) >= 6
        for chunk in sentence_chunks[:question_index]
    )
    return not substantive_before_question


def gd_panelist_formulaic_meta_text(text: str, persona: dict[str, Any]) -> bool:
    """True when a GD debater speaks in facilitator-template labels.

    Moderator pivots can explicitly label the next angle. Debaters should sound
    like participants in the discussion, not announce a coaching frame.
    """
    role_type = str(persona.get("role_type") or "").lower()
    speaker_id = str(persona.get("speaker_id") or "").lower()
    name = str(persona.get("name") or "").lower()
    if role_type == "moderator" or "moderator" in speaker_id or "moderator" in name:
        return False
    value = " ".join(str(text or "").split())
    return bool(_GD_FORMULAIC_META_RE.search(value))


def gd_moderator_interview_question_text(text: str, persona: dict[str, Any]) -> bool:
    """True when a moderator cross-examines the learner instead of steering."""
    role_type = str(persona.get("role_type") or "").lower()
    speaker_id = str(persona.get("speaker_id") or "").lower()
    name = str(persona.get("name") or "").lower()
    is_moderator = role_type == "moderator" or "moderator" in speaker_id or "moderator" in name
    if not is_moderator:
        return False
    questions = [
        chunk.strip()
        for chunk in re.split(r"(?<=[.!?])\s+", " ".join(str(text or "").split()))
        if chunk.strip().endswith("?")
    ]
    room_direction = re.compile(
        r"\b(?:the group|the room|the panel|participants|both sides|we|our|"
        r"the motion|this discussion|the discussion)\b",
        re.IGNORECASE,
    )
    for chunk in questions:
        if re.search(
            r"\b(?:can you|could you|would you|tell me|give me|what would you|how would you|you|your)\b",
            chunk,
            re.IGNORECASE,
        ):
            return True
        if room_direction.search(chunk):
            continue
        if re.match(r"^\s*(?:what|why|which|how)\b", chunk, re.IGNORECASE):
            return True
    return False


def interview_model_answer_leak(text: str) -> bool:
    lower = text or ""
    if not any(pattern.search(lower) for pattern in _MODEL_ANSWER_PATTERNS):
        return False
    return any(
        marker in lower.lower()
        for marker in ("for example", "how would you", "can you elaborate", "what would you")
    )

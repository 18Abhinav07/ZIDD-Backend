"""Simulation setup resolution for interview and GD tests."""
from __future__ import annotations

import hashlib
import json
import zlib
from dataclasses import dataclass, field
from typing import Any, Mapping

from app.content.motions import GD_MOTIONS, motion_for_node
from app.content.task_types import TaskType
from app.services.career_context import (
    CareerContext,
    ROLE_BUSINESS,
    ROLE_HR,
    ROLE_OPS,
    ROLE_SALES,
    ROLE_SOFTWARE,
    infer_role_family,
)


GD_ENVIRONMENTS: dict[str, str] = {
    "campus_placement": "Campus placement GD",
    "business_case": "Business case discussion",
    "workplace_debate": "Workplace debate",
    "high_pressure_panel": "High-pressure panel",
}

INTERVIEW_TYPES: dict[str, str] = {
    "hr": "HR interview",
    "behavioral": "Behavioral interview",
    "technical_project": "Technical/project interview",
    "management": "Management interview",
    "mixed": "Mixed interview",
}

PRESSURE_LEVELS: dict[str, str] = {
    "warm": "warm",
    "standard": "standard",
    "high": "high-pressure",
}

GD_PERSONA_LIBRARY: dict[str, dict[str, str]] = {
    "moderator_timekeeper": {
        "speaker_id": "moderator_timekeeper",
        "name": "Moderator",
        "role_type": "moderator",
        "role": (
            "neutral timekeeper and facilitator — frame the topic, pull in quiet "
            "voices, press vague claims for specifics, and summarize splits"
        ),
    },
    "aggressive_challenger": {
        "speaker_id": "aggressive_challenger",
        "name": "Aggressive Challenger",
        "role_type": "debater",
        "stance": (
            "forceful skeptic — attack weak assumptions, interrupt politely but "
            "firmly, and demand evidence before accepting claims"
        ),
    },
    "data_driven_analyst": {
        "speaker_id": "data_driven_analyst",
        "name": "Data-Driven Analyst",
        "role_type": "debater",
        "stance": (
            "evidence-first analyst — ask for numbers, trade-offs, and examples; "
            "reward specific reasoning and challenge vague opinions"
        ),
    },
    "quiet_expert": {
        "speaker_id": "quiet_expert",
        "name": "Quiet Expert",
        "role_type": "debater",
        "stance": (
            "reserved domain expert — speak less often but add precise, high-value "
            "points and invite the learner to build on them"
        ),
    },
    "consensus_builder": {
        "speaker_id": "consensus_builder",
        "name": "Consensus Builder",
        "role_type": "debater",
        "stance": (
            "collaborative synthesizer — connect opposing views, find common "
            "ground, and test whether the learner can build consensus"
        ),
    },
    "devils_advocate": {
        "speaker_id": "devils_advocate",
        "name": "Devil's Advocate",
        "role_type": "debater",
        "stance": (
            "counter-position specialist — take the uncomfortable opposite angle "
            "even when the room agrees too easily"
        ),
    },
}

DEFAULT_GD_PERSONAS = [
    "aggressive_challenger",
    "data_driven_analyst",
    "consensus_builder",
]


@dataclass(frozen=True)
class ResolvedSimulationConfig:
    task_type: str
    resolved_topic: str = ""
    environment: str = ""
    persona_roster: list[dict[str, Any]] = field(default_factory=list)
    interview_type: str = ""
    pressure_level: str = "standard"
    target_role: str = ""
    role_family: str = ""
    context_hash: str = ""

    def private_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "resolved_topic": self.resolved_topic,
            "environment": self.environment,
            "personas": [p.get("speaker_id") for p in self.persona_roster],
            "interview_type": self.interview_type,
            "pressure_level": self.pressure_level,
            "target_role": self.target_role,
            "role_family": self.role_family,
            "context_hash": self.context_hash,
        }

    def public_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "topic": self.resolved_topic,
            "environment": GD_ENVIRONMENTS.get(self.environment, self.environment),
            "personas": [
                p["name"]
                for p in self.persona_roster
                if p.get("role_type") != "moderator"
            ],
            "interview_type": INTERVIEW_TYPES.get(self.interview_type, self.interview_type),
            "pressure_level": PRESSURE_LEVELS.get(self.pressure_level, self.pressure_level),
            "target_role": self.target_role,
            "role_family": self.role_family,
        }


def _clean(value: Any, *, limit: int = 160) -> str:
    text = " ".join(str(value or "").split())
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "..."
    return text


def _stable_pick(options: list[str], seed: str) -> str:
    if not options:
        return ""
    idx = zlib.crc32(seed.encode("utf-8")) % len(options)
    return options[idx]


def _hash_context(ctx: CareerContext, config: Mapping[str, Any]) -> str:
    payload = {
        "role_family": ctx.role_family,
        "target_roles": ctx.target_roles[:4],
        "interview_goals": ctx.interview_goals[:4],
        "gd_topics": ctx.gd_topics[:6],
        "resume_facts": ctx.resume_facts[:4],
        "config": dict(config),
    }
    data = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]


def _gd_topic(node_id: str, raw: Mapping[str, Any], ctx: CareerContext) -> str:
    mode = _clean(raw.get("topic_mode") or raw.get("topicSource") or "profile", limit=40)
    explicit = _clean(raw.get("topic") or raw.get("resolved_topic"), limit=180)
    custom = _clean(raw.get("custom_topic") or raw.get("customTopic"), limit=180)
    if mode == "custom" and custom:
        return custom
    if explicit:
        return explicit
    if mode == "random":
        return _stable_pick(ctx.gd_topics or GD_MOTIONS, node_id + ctx.primary_role) or motion_for_node(node_id)
    if ctx.gd_topics:
        return _stable_pick(ctx.gd_topics, node_id + ctx.primary_role)
    return motion_for_node(node_id)


def _gd_roster(raw: Mapping[str, Any]) -> list[dict[str, Any]]:
    selected = raw.get("persona_ids") or raw.get("personas") or DEFAULT_GD_PERSONAS
    if not isinstance(selected, list):
        raise ValueError("persona_ids must be a list")
    clean_ids: list[str] = []
    for pid in selected:
        pid = _clean(pid, limit=60)
        if not pid or pid == "moderator_timekeeper":
            continue
        if pid not in GD_PERSONA_LIBRARY:
            raise ValueError(f"unknown GD persona: {pid}")
        if pid not in clean_ids:
            clean_ids.append(pid)
    if not clean_ids:
        clean_ids = list(DEFAULT_GD_PERSONAS)
    clean_ids = clean_ids[:4]
    return [dict(GD_PERSONA_LIBRARY["moderator_timekeeper"])] + [
        dict(GD_PERSONA_LIBRARY[pid]) for pid in clean_ids
    ]


def _environment(raw: Mapping[str, Any]) -> str:
    env = _clean(raw.get("environment") or "campus_placement", limit=60)
    if env not in GD_ENVIRONMENTS:
        raise ValueError(f"unknown GD environment: {env}")
    return env


def _interview_type(raw: Mapping[str, Any], ctx: CareerContext) -> str:
    requested = _clean(raw.get("interview_type") or raw.get("interviewType"), limit=60)
    if requested:
        if requested not in INTERVIEW_TYPES:
            raise ValueError(f"unknown interview type: {requested}")
        return requested
    if ctx.role_family == ROLE_SOFTWARE:
        return "technical_project"
    if ctx.role_family in (ROLE_BUSINESS, ROLE_HR, ROLE_SALES):
        return "behavioral"
    return "mixed"


def _pressure(raw: Mapping[str, Any]) -> str:
    pressure = _clean(raw.get("pressure_level") or raw.get("pressureLevel") or "standard", limit=40)
    if pressure not in PRESSURE_LEVELS:
        raise ValueError(f"unknown interview pressure level: {pressure}")
    return pressure


def _interviewer_style(pressure: str, interview_type: str) -> str:
    if pressure == "high":
        return "probing and high-tempo — short follow-ups, specific evidence, no vague claims"
    if pressure == "warm":
        return "warm and encouraging — make the candidate comfortable while still asking real follow-ups"
    if interview_type == "technical_project":
        return "technical but communication-focused — project depth, trade-offs, debugging, and ownership"
    return "neutral and professional — concise follow-ups that test structure and relevance"


def _interview_topic(target_role: str, interview_type: str, pressure: str, role_family: str) -> str:
    type_label = INTERVIEW_TYPES.get(interview_type, interview_type)
    pressure_label = PRESSURE_LEVELS.get(pressure, pressure)
    return f"{type_label} for {target_role} ({pressure_label}, {role_family})"


def resolve_simulation_config(
    task_type: TaskType,
    node_id: str,
    raw_config: Mapping[str, Any] | None,
    career_context: CareerContext,
) -> ResolvedSimulationConfig:
    """Validate and resolve learner-selected simulation setup."""
    raw = raw_config or {}
    if task_type == TaskType.GD_TEST:
        topic = _gd_topic(node_id, raw, career_context)
        env = _environment(raw)
        roster = _gd_roster(raw)
        private_config = {
            "task_type": task_type.value,
            "topic": topic,
            "environment": env,
            "personas": [p["speaker_id"] for p in roster],
        }
        return ResolvedSimulationConfig(
            task_type=task_type.value,
            resolved_topic=topic,
            environment=env,
            persona_roster=roster,
            role_family=career_context.role_family,
            context_hash=_hash_context(career_context, private_config),
        )

    if task_type == TaskType.INTERVIEW_TEST:
        requested_target_role = _clean(raw.get("target_role") or raw.get("targetRole"), limit=90)
        target_role = requested_target_role or career_context.primary_role
        role_family = career_context.role_family
        if requested_target_role:
            inferred = infer_role_family([target_role], career_context.interview_goals)
            if inferred != ROLE_OPS:
                role_family = inferred
        interview_type = _interview_type(raw, career_context)
        pressure = _pressure(raw)
        topic = _interview_topic(target_role, interview_type, pressure, role_family)
        roster = [
            {
                "speaker_id": "interviewer",
                "name": "Interviewer",
                "role_type": "interviewer",
                "role": f"{INTERVIEW_TYPES[interview_type]} interviewer for {target_role}",
                "prompt_role": (
                    f"{INTERVIEW_TYPES[interview_type]} interviewer for {target_role}. "
                    "The interview is communication-focused: probe examples, "
                    "ownership, trade-offs, clarity, and relevance."
                ),
                "style": _interviewer_style(pressure, interview_type),
            }
        ]
        private_config = {
            "task_type": task_type.value,
            "target_role": target_role,
            "interview_type": interview_type,
            "pressure": pressure,
            "role_family": role_family,
        }
        return ResolvedSimulationConfig(
            task_type=task_type.value,
            resolved_topic=topic,
            persona_roster=roster,
            interview_type=interview_type,
            pressure_level=pressure,
            target_role=target_role,
            role_family=role_family,
            context_hash=_hash_context(career_context, private_config),
        )

    return ResolvedSimulationConfig(
        task_type=task_type.value,
        role_family=career_context.role_family,
        target_role=career_context.primary_role,
        context_hash=_hash_context(career_context, {"task_type": task_type.value}),
    )

"""Career-profile personalization context.

This module converts the stored onboarding career profile into a compact,
sanitized context object. The private prompt block may include short resume
facts, but public/session snapshots must expose only non-sensitive labels.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping


RoleFamily = str

ROLE_SOFTWARE: RoleFamily = "software_technical"
ROLE_BUSINESS: RoleFamily = "business_management"
ROLE_HR: RoleFamily = "hr_people"
ROLE_SALES: RoleFamily = "sales_customer"
ROLE_OPS: RoleFamily = "operations_other"

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE_RE = re.compile(r"(?:\+?\d[\s().-]*){8,}")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_SPACE_RE = re.compile(r"\s+")

_ROLE_KEYWORDS: list[tuple[RoleFamily, tuple[str, ...]]] = [
    (
        ROLE_SOFTWARE,
        (
            "software",
            "developer",
            "engineer",
            "backend",
            "frontend",
            "full stack",
            "full-stack",
            "python",
            "react",
            "api",
            "data scientist",
            "machine learning",
            "ml engineer",
            "devops",
            "cloud",
            "qa",
            "sde",
        ),
    ),
    (
        ROLE_HR,
        (
            "human resources",
            "hr",
            "recruiter",
            "talent",
            "people operations",
            "people ops",
            "employee relations",
        ),
    ),
    (
        ROLE_SALES,
        (
            "sales",
            "business development",
            "customer success",
            "account executive",
            "support",
            "relationship manager",
            "client",
        ),
    ),
    (
        ROLE_BUSINESS,
        (
            "management",
            "manager",
            "consultant",
            "strategy",
            "business analyst",
            "product manager",
            "operations manager",
            "mba",
            "finance",
            "marketing",
        ),
    ),
]

GD_TOPIC_LABELS: dict[str, str] = {
    "ai-in-education": "AI in education",
    "social-media": "Social media and students",
    "startup-india": "Startups in India",
    "remote-work": "Remote work culture",
    "climate-action": "Climate responsibility",
    "digital-payments": "Digital payments",
}


@dataclass(frozen=True)
class CareerContext:
    role_family: RoleFamily = ROLE_OPS
    target_roles: list[str] = field(default_factory=list)
    interview_goals: list[str] = field(default_factory=list)
    gd_topics: list[str] = field(default_factory=list)
    resume_facts: list[str] = field(default_factory=list)

    @property
    def primary_role(self) -> str:
        return self.target_roles[0] if self.target_roles else _family_label(self.role_family)

    def public_dict(self) -> dict[str, Any]:
        """Public browser-safe labels. No resume text or extracted facts."""
        return {
            "role_family": self.role_family,
            "primary_role": self.primary_role,
            "target_roles": list(self.target_roles),
            "interview_goals": list(self.interview_goals),
            "gd_topics": list(self.gd_topics),
            "has_resume_facts": bool(self.resume_facts),
        }

    def private_dict(self) -> dict[str, Any]:
        """Private prompt/session context. Still sanitized and bounded."""
        return {
            **self.public_dict(),
            "resume_facts": list(self.resume_facts),
        }

    def private_prompt_block(self) -> str:
        parts: list[str] = [
            "Career personalization context (private; use it, never read it aloud):",
            f"- role family: {self.role_family}",
            f"- primary role focus: {self.primary_role}",
        ]
        if self.target_roles:
            parts.append(f"- target roles: {', '.join(self.target_roles[:5])}")
        if self.interview_goals:
            parts.append(f"- interview goals: {', '.join(self.interview_goals[:5])}")
        if self.gd_topics:
            parts.append(f"- preferred GD topics: {', '.join(self.gd_topics[:8])}")
        if self.resume_facts:
            parts.append("- safe resume/project facts to draw from:")
            parts.extend(f"  - {fact}" for fact in self.resume_facts[:8])
        parts.append(
            "Use this to choose examples, follow-ups, bridge exercises, and "
            "challenge constraints. Do not mention private notes, do not expose "
            "resume facts unless the learner already brought them into the chat, "
            "and never invent employers, projects, metrics, or history."
        )
        return "\n".join(parts) + "\n\n"


def _family_label(role_family: RoleFamily) -> str:
    return {
        ROLE_SOFTWARE: "software role",
        ROLE_BUSINESS: "business or management role",
        ROLE_HR: "HR or people role",
        ROLE_SALES: "sales or customer-facing role",
        ROLE_OPS: "career role",
    }.get(role_family, "career role")


def _clean_list(values: Any, *, limit: int = 8, item_limit: int = 80) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = _sanitize_text(str(value or ""), max_len=item_limit)
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            out.append(item)
        if len(out) >= limit:
            break
    return out


def _gd_topic_labels(values: Any, *, limit: int = 8) -> list[str]:
    topics = _clean_list(values, limit=limit, item_limit=80)
    return [GD_TOPIC_LABELS.get(topic, topic) for topic in topics]


def _sanitize_text(value: str, *, max_len: int = 180) -> str:
    text = _EMAIL_RE.sub("", value or "")
    text = _PHONE_RE.sub("", text)
    text = _URL_RE.sub("", text)
    text = _SPACE_RE.sub(" ", text).strip(" -•\t\r\n")
    if len(text) > max_len:
        text = text[: max_len - 1].rstrip() + "..."
    return text


def _resume_facts(resume_text: str) -> list[str]:
    if not resume_text or not resume_text.strip():
        return []
    raw_parts = re.split(r"[\n\r]+|(?<=[.!?])\s+", resume_text)
    facts: list[str] = []
    seen: set[str] = set()
    for raw in raw_parts:
        fact = _sanitize_text(raw, max_len=160)
        if len(fact) < 12:
            continue
        key = fact.lower()
        if key in seen:
            continue
        seen.add(key)
        facts.append(fact)
        if len(facts) >= 8:
            break
    return facts


def _infer_role_family(target_roles: list[str], goals: list[str], resume_text: str) -> RoleFamily:
    haystack = " ".join(target_roles + goals + [resume_text]).lower()
    for family, keywords in _ROLE_KEYWORDS:
        if any(keyword in haystack for keyword in keywords):
            return family
    return ROLE_OPS


def infer_role_family(
    target_roles: list[str] | None = None,
    goals: list[str] | None = None,
    resume_text: str = "",
) -> RoleFamily:
    return _infer_role_family(target_roles or [], goals or [], resume_text)


def build_career_context(profile_or_career_profile: Mapping[str, Any] | None) -> CareerContext:
    """Build a bounded personalization context from profile data.

    Accepts either a full learner profile containing `career_profile` or the
    `career_profile` object itself. Empty data returns a safe generic context.
    """
    source: Mapping[str, Any] = profile_or_career_profile or {}
    career = source.get("career_profile") if isinstance(source.get("career_profile"), Mapping) else source
    career = career if isinstance(career, Mapping) else {}

    target_roles = _clean_list(career.get("target_roles"), limit=5)
    interview_goals = _clean_list(career.get("interview_goals"), limit=6)
    gd_topic_ids = _gd_topic_labels(career.get("gd_topic_ids"), limit=6)
    custom_gd_topics = _clean_list(career.get("custom_gd_topics"), limit=8, item_limit=140)
    resume_text = str(career.get("resume_text") or "")
    role_family = _infer_role_family(target_roles, interview_goals, resume_text)

    return CareerContext(
        role_family=role_family,
        target_roles=target_roles,
        interview_goals=interview_goals,
        gd_topics=custom_gd_topics + [topic for topic in gd_topic_ids if topic not in custom_gd_topics],
        resume_facts=_resume_facts(resume_text),
    )

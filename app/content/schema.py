"""Data models for the agentic tutor curriculum.

These replace the hardcoded CommNode dataclasses and allow curricula to be
defined in structured JSON.
"""
from typing import Literal, Optional, List
from pydantic import BaseModel, Field


class BridgeExercise(BaseModel):
    """A pre-authored scaffolding exercise.
    
    Instead of relying on the LLM to generate a simpler prompt on the fly, 
    the engine can serve these structured exercises when a learner struggles.
    """
    id: str
    type: Literal["fill_blank", "multiple_choice", "spoken"]
    sentence: str
    hint: str
    context: str
    answer_key: str
    # Equally-correct alternative fills, graded the same as answer_key. Lets a
    # blank with interchangeable answers ("For example" / "For instance", "but" /
    # "however") accept any valid form instead of marking synonyms wrong (M3).
    accept: Optional[List[str]] = None
    options: Optional[List[str]] = None
    band: Optional[Literal["foundational", "standard", "stretch"]] = None


class Concept(BaseModel):
    """A single pedagogical node (formerly CommNode)."""
    id: str
    title: str
    level: int
    level_type: Literal["text", "voice"]
    skill: str
    teach_focus: str
    success_criteria: str
    bridge_focus: str
    cefr: str = ""
    prerequisites: List[str] = Field(default_factory=list)
    # Pre-authored scaffolding exercises mapped to this concept
    bridge_exercises: List[BridgeExercise] = Field(default_factory=list)
    role: str = "core"            # "core" | "remediation"
    exemplars: List[str] = []     # 1–2 model answers, optional


class Module(BaseModel):
    """A collection of Concepts forming a unified teaching sequence."""
    id: str
    title: str
    description: str
    nodes: List[Concept]

    @property
    def order(self) -> List[str]:
        return [n.id for n in self.nodes]


class ContentGroup(BaseModel):
    id: str
    title: str
    description: str = ""
    children: list["ContentGroup"] = Field(default_factory=list)  # recursive
    modules: list[str] = Field(default_factory=list)              # leaf-container refs
    locked: bool = False                                          # unlock-gate (D reuses for paywall)
    unlock_rule: Optional[str] = None                             # condition expression, None = open
    tests: list[str] = Field(default_factory=list)               # attached test/sim node ids

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
    options: Optional[List[str]] = None


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


class Module(BaseModel):
    """A collection of Concepts forming a unified teaching sequence."""
    id: str
    title: str
    description: str
    nodes: List[Concept]

    @property
    def order(self) -> List[str]:
        return [n.id for n in self.nodes]


class Track(BaseModel):
    """A higher-level grouping of modules (e.g. Communication Track)."""
    id: str
    title: str
    description: str
    modules: List[Module]

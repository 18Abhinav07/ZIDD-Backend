"""Data models for the agentic tutor curriculum.

These replace the hardcoded CommNode dataclasses and allow curricula to be
defined in structured JSON.
"""
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator


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

    @model_validator(mode="after")
    def _well_formed(self) -> "BridgeExercise":
        """Reject structurally broken exercises at load time (D4).

        pydantic's shape check alone let an empty prompt, a fill_blank with no
        gap, or a multiple_choice whose answer_key is not among its options pass
        validation and reach a learner as an ungradeable / unanswerable item."""
        for f in ("id", "sentence", "hint", "context"):
            if not str(getattr(self, f)).strip():
                raise ValueError(f"BridgeExercise {self.id!r}: '{f}' must be non-empty")
        if self.type == "fill_blank":
            if "_" not in self.sentence:
                raise ValueError(
                    f"BridgeExercise {self.id!r}: fill_blank sentence needs a '_' gap"
                )
            if not self.answer_key.strip():
                raise ValueError(
                    f"BridgeExercise {self.id!r}: fill_blank needs a non-empty answer_key"
                )
        elif self.type == "multiple_choice":
            opts = self.options or []
            if len(opts) < 2:
                raise ValueError(
                    f"BridgeExercise {self.id!r}: multiple_choice needs >= 2 options"
                )
            if not self.answer_key.strip() or self.answer_key not in opts:
                raise ValueError(
                    f"BridgeExercise {self.id!r}: multiple_choice answer_key must be one of options"
                )
        # 'spoken' has no single keyed answer to grade against — answer_key is
        # evaluator guidance, not a learner-visible model answer.
        return self


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

    @field_validator(
        "id", "title", "skill", "teach_focus", "success_criteria", "bridge_focus"
    )
    @classmethod
    def _non_empty(cls, v: str, info) -> str:
        """A required pedagogy string must carry real content (D4). An empty
        teach_focus / success_criteria / bridge_focus passed the shape check and
        silently degraded the coach prompt to a blank anchor."""
        if not str(v).strip():
            raise ValueError(f"Concept field '{info.field_name}' must be non-empty")
        return v


class AssessmentItem(BaseModel):
    """One deterministically-gradable assessment item (chapter / milestone / class
    test). Graded by the SAME answer_check engine as bridge exercises, so a school
    test never leans on the LLM rubric to mark a closed item. `skill` ties the item
    back to the level it assesses, so a report can say WHICH skill a child missed."""
    id: str
    type: Literal["fill_blank", "multiple_choice"]
    prompt: str
    answer_key: str
    options: Optional[List[str]] = None
    accept: Optional[List[str]] = None
    skill: str = ""

    @model_validator(mode="after")
    def _well_formed(self) -> "AssessmentItem":
        for f in ("id", "prompt", "answer_key"):
            if not str(getattr(self, f)).strip():
                raise ValueError(f"AssessmentItem {self.id!r}: '{f}' must be non-empty")
        if self.type == "fill_blank" and "_" not in self.prompt:
            raise ValueError(f"AssessmentItem {self.id!r}: fill_blank prompt needs a '_' gap")
        if self.type == "multiple_choice":
            opts = self.options or []
            if len(opts) < 2:
                raise ValueError(f"AssessmentItem {self.id!r}: multiple_choice needs >= 2 options")
            if self.answer_key not in opts:
                raise ValueError(f"AssessmentItem {self.id!r}: answer_key must be one of options")
        return self


class Assessment(BaseModel):
    """A school assessment: a bank of gradable items with a pass mark.

    `kind` distinguishes a per-chapter test, a class milestone (cumulative, fired
    at `at_percent` of the class's chapters), and the final class exam. A test is
    NOT a coaching node — it is scored as a whole and produces a report."""
    id: str
    title: str
    kind: Literal["chapter", "milestone", "class_final"]
    pass_mark: float = 0.6
    at_percent: Optional[int] = None   # milestone trigger (30/60/100); None for chapter
    items: List[AssessmentItem]

    @model_validator(mode="after")
    def _has_items(self) -> "Assessment":
        if not self.items:
            raise ValueError(f"Assessment {self.id!r}: must carry at least one item")
        if self.kind == "milestone" and self.at_percent not in (30, 60, 100):
            raise ValueError(f"Assessment {self.id!r}: milestone at_percent must be 30, 60, or 100")
        return self


class Module(BaseModel):
    """A collection of Concepts forming a unified teaching sequence.

    For NCERT primary English a Module IS a single chapter (the optional chapter
    metadata below): its `nodes` are the levels inside the chapter, and
    `chapter_test` is the short assessment that closes it. Non-school modules leave
    the chapter fields None and behave exactly as before."""
    id: str
    title: str
    description: str
    nodes: List[Concept]
    # ---- optional NCERT chapter metadata (a chapter is a module) ----
    class_no: Optional[int] = None       # 2-5; None for non-school modules
    chapter_no: Optional[int] = None     # ordinal within the class
    ncert_unit: Optional[str] = None     # the real Marigold chapter / poem title
    genre: Optional[Literal["story", "poem", "grammar"]] = None
    chapter_test: Optional[Assessment] = None  # closes the chapter

    @property
    def order(self) -> List[str]:
        return [n.id for n in self.nodes]


class SchoolClass(BaseModel):
    """A class (grade) manifest: ordered chapter modules + milestone tests at
    completion thresholds. Concretely wires the previously-dead ContentGroup idea
    for the NCERT primary-English ladder: class -> chapters -> levels (+ tests)."""
    class_no: int
    title: str
    description: str = ""
    chapters: List[str]                       # ordered chapter (module) ids
    milestones: List[Assessment] = Field(default_factory=list)  # at 30 / 60 / 100%

    @model_validator(mode="after")
    def _ordered_milestones(self) -> "SchoolClass":
        if not self.chapters:
            raise ValueError(f"SchoolClass {self.class_no}: must list chapters")
        pts = [m.at_percent for m in self.milestones]
        if pts != sorted(p for p in pts if p is not None):
            raise ValueError(f"SchoolClass {self.class_no}: milestones must ascend by at_percent")
        return self


class ContentGroup(BaseModel):
    id: str
    title: str
    description: str = ""
    children: list["ContentGroup"] = Field(default_factory=list)  # recursive
    modules: list[str] = Field(default_factory=list)              # leaf-container refs
    locked: bool = False                                          # unlock-gate (D reuses for paywall)
    unlock_rule: Optional[str] = None                             # condition expression, None = open
    tests: list[str] = Field(default_factory=list)               # attached test/sim node ids

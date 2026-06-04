"""Communication module — 10 competency nodes (architecture-v3 §601).

Text-first: 7 text levels (sentence-framing/construction) -> 3 voice levels
(apply the framing under speaking pressure). Content is derived/paraphrased
(NCERT/CEFR-aligned), never verbatim — IP-safe in a paid product.

These dataclasses are the curriculum source the engine prompts against. The
engine is content-agnostic: swap this list for another module's nodes and the
loop is unchanged.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CommNode:
    id: str
    title: str
    level: int
    level_type: str             # "text" | "voice"
    skill: str                  # the construction skill being built
    teach_focus: str            # what a teach turn should drill
    success_criteria: str       # what a mastered answer looks like
    bridge_focus: str           # the smaller sub-step when the learner struggles
    cefr: str = ""              # CEFR can-do alignment, if any
    prerequisites: list[str] = field(default_factory=list)


COMM_NODES: list[CommNode] = [
    CommNode(
        id="comm_01_self_intro",
        title="Introduce Yourself",
        level=1,
        level_type="text",
        skill="Frame a clear 2-sentence self-introduction (name, role, one detail).",
        teach_focus="Subject-verb basics in the present tense; one concrete detail.",
        success_criteria="Two grammatical sentences: who they are + one specific fact.",
        bridge_focus="Just one sentence: 'My name is ___ and I ___.'",
        cefr="A2",
    ),
    CommNode(
        id="comm_02_describe_routine",
        title="Describe Your Routine",
        level=2,
        level_type="text",
        skill="Use the present simple to describe habitual actions in sequence.",
        teach_focus="Present-simple conjugation; sequencing words (first, then, after).",
        success_criteria="3+ sequenced present-tense actions, correct verb forms.",
        bridge_focus="One present-tense sentence about a single daily action.",
        cefr="A2",
        prerequisites=["comm_01_self_intro"],
    ),
    CommNode(
        id="comm_03_past_event",
        title="Narrate a Past Event",
        level=3,
        level_type="text",
        skill="Narrate a completed event using the past tense.",
        teach_focus="Regular vs irregular past forms; time markers (yesterday, last week).",
        success_criteria="A short past-tense narration with correct verb forms.",
        bridge_focus="One past-tense sentence: 'Yesterday I ___.'",
        cefr="B1",
        prerequisites=["comm_02_describe_routine"],
    ),
    CommNode(
        id="comm_04_opinion",
        title="State an Opinion",
        level=4,
        level_type="text",
        skill="State an opinion with a supporting reason.",
        teach_focus="'I think/believe ... because ...' framing; one clear reason.",
        success_criteria="An opinion + at least one relevant supporting reason.",
        bridge_focus="Finish the stem: 'I think ___ because ___.'",
        cefr="B1",
        prerequisites=["comm_03_past_event"],
    ),
    CommNode(
        id="comm_05_compare",
        title="Compare Two Things",
        level=5,
        level_type="text",
        skill="Compare two options using comparative structures.",
        teach_focus="Comparatives (more/less, -er than); balanced contrast.",
        success_criteria="A clear comparison naming a difference and a preference.",
        bridge_focus="One comparative sentence: 'A is ___er than B.'",
        cefr="B1",
        prerequisites=["comm_04_opinion"],
    ),
    CommNode(
        id="comm_06_persuade",
        title="Make a Short Argument",
        level=6,
        level_type="text",
        skill="Build a 3-part argument: claim, reason, example.",
        teach_focus="Claim -> reason -> concrete example structure; linking words.",
        success_criteria="A claim backed by a reason and a concrete example.",
        bridge_focus="State only the claim in one sentence; reasons come later.",
        cefr="B2",
        prerequisites=["comm_05_compare"],
    ),
    CommNode(
        id="comm_07_handle_question",
        title="Handle a Follow-up Question",
        level=7,
        level_type="text",
        skill="Answer an unexpected follow-up directly and concisely.",
        teach_focus="Acknowledge -> answer -> stop; avoid rambling.",
        success_criteria="A direct, on-topic answer to the follow-up, no padding.",
        bridge_focus="Answer in a single sentence, then stop.",
        cefr="B2",
        prerequisites=["comm_06_persuade"],
    ),
    CommNode(
        id="comm_08_voice_intro",
        title="Speak Your Introduction",
        level=8,
        level_type="voice",
        skill="Deliver the self-introduction aloud with clear pacing.",
        teach_focus="Pace and pausing; apply the text framing under voice.",
        success_criteria="Spoken intro, intelligible, steady pace, no long freezes.",
        bridge_focus="Say only your name and role aloud.",
        cefr="A2",
        prerequisites=["comm_07_handle_question"],
    ),
    CommNode(
        id="comm_09_voice_convo",
        title="Hold a Short Exchange",
        level=9,
        level_type="voice",
        skill="Sustain a short back-and-forth aloud without freezing.",
        teach_focus="Turn-taking; quick formulation under live pressure.",
        success_criteria="3+ spoken turns staying on topic, recoverable hesitations.",
        bridge_focus="Answer one spoken question, then ask one back.",
        cefr="B1",
        prerequisites=["comm_08_voice_intro"],
    ),
    CommNode(
        id="comm_10_voice_pressure",
        title="Recover Under Interruption",
        level=10,
        level_type="voice",
        skill="Stay coherent when interrupted and regain the thread.",
        teach_focus="Reset phrases; finish the point after an interruption.",
        success_criteria="Handles an interruption and completes the original point.",
        bridge_focus="After an interruption, restate your last sentence.",
        cefr="B2",
        prerequisites=["comm_09_voice_convo"],
    ),
]

MODULE_ID = "communication"
MODULE_TITLE = "Communication Foundations"
MODULE_DESCRIPTION = (
    "Build core spoken/written English from the ground up: introduce yourself, "
    "narrate, give opinions, argue, and handle questions. A2 to B2."
)
MODULE_ORDER: list[str] = [n.id for n in COMM_NODES]
_BY_ID: dict[str, CommNode] = {n.id: n for n in COMM_NODES}


def get_node(node_id: str) -> CommNode:
    return _BY_ID[node_id]


def next_node(node_id: str) -> str | None:
    """Next node id in module order, or None if this was the last level."""
    idx = MODULE_ORDER.index(node_id)
    return MODULE_ORDER[idx + 1] if idx + 1 < len(MODULE_ORDER) else None

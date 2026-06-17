"""Concrete debate motions for group-discussion (GD) assessment sims.

P0-4 root cause: a GD TEST session seeded `sim_topic` from the node's
`teach_focus` — a TEACHING INSTRUCTION ("stake a clear position early"), not a
debatable motion. The opening brief and the persona/director prompts then each
invented a DIFFERENT concrete motion from that vague seed, so the learner was
briefed on one topic while the panel debated another (verified live: opening
"remote work", panel "social media").

The fix is a bank of CONCRETE motions. `motion_for_node` picks one
deterministically (stable across processes — Python's str hash is salted, so we
use sha1), which is stored once in `state["sim_topic"]` and read verbatim by the
opening, the director, and every persona. The node's GD micro-skill (staking a
position, rebutting, turn-taking) is assessed regardless of which motion carries
it, so a generic-but-coherent bank is exactly right; stable-per-node selection
gives variety across the ten GD nodes without ever desyncing within a session.
"""
import hashlib

# Campus / early-career GD motions: each is a single, clearly two-sided question
# a panel can argue and a learner can take a stance on.
GD_MOTIONS = [
    "Should remote work be the default option for most knowledge-economy companies?",
    "Is social media doing more harm than good to public discourse?",
    "Should college education be free for everyone?",
    "Do smartphones make young people more connected or more isolated?",
    "Should companies be allowed to monitor employees' productivity software?",
    "Is artificial intelligence a net positive for the future job market?",
    "Should public transport be made free in large cities?",
    "Is a four-day work week better for both employees and employers?",
    "Should standardized exams decide a student's place at university?",
    "Does working from a big city still matter for a successful career?",
    "Should governments regulate how much screen time children get?",
    "Is it better to be a specialist or a generalist in today's job market?",
    "Should businesses prioritise profit or social responsibility when the two conflict?",
    "Is online learning as effective as classroom learning?",
    "Should influencers be held to the same advertising rules as companies?",
]


def motion_for_node(node_id: str) -> str:
    """Pick a stable, concrete GD motion for a node.

    Deterministic across processes (sha1, not the salted builtin hash) so the same
    node always seeds the same motion — the value is stored once per session and
    shared verbatim by the opening, director, and personas."""
    digest = hashlib.sha1(node_id.encode("utf-8")).hexdigest()
    return GD_MOTIONS[int(digest, 16) % len(GD_MOTIONS)]

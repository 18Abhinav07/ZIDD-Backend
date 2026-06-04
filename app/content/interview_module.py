"""Interview-prep module — 10 competency nodes (B2 -> C1).

Medium-to-advanced track for learners who already have a working command of
English and want to perform in real job interviews. Skills escalate from a
crisp self-pitch to handling pushback and closing sharply. Content is
derived/paraphrased from standard CEFR can-do descriptors and common interview
coaching frameworks (STAR, etc.) — never verbatim, IP-safe in a paid product.

Same CommNode shape as the communication module; the engine is content-agnostic
and loops over this list unchanged.
"""
from app.content.comm_module import CommNode

INTERVIEW_NODES: list[CommNode] = [
    CommNode(
        id="int_01_elevator_pitch",
        title="Tell Me About Yourself",
        level=1,
        level_type="text",
        skill="Deliver a 30-second professional pitch: present role, signature strength, current goal.",
        teach_focus="Structure present->proof->direction; cut filler; lead with the most relevant fact.",
        success_criteria="A tight 3-4 sentence pitch that signals role, one concrete strength, and a forward goal — no rambling.",
        bridge_focus="One sentence: 'I'm a ___ who ___.' Just the role and one strength.",
        cefr="B2",
    ),
    CommNode(
        id="int_02_strength_with_evidence",
        title="Back a Strength With Evidence",
        level=2,
        level_type="text",
        skill="Assert a strength and immediately support it with a concrete, specific example.",
        teach_focus="Claim -> proof pairing; replace adjectives ('hardworking') with evidence (what you did).",
        success_criteria="A named strength followed by one specific situation that demonstrates it.",
        bridge_focus="State the strength, then finish: 'For example, once I ___.'",
        cefr="B2",
        prerequisites=["int_01_elevator_pitch"],
    ),
    CommNode(
        id="int_03_weakness_framing",
        title="Answer the Weakness Question",
        level=3,
        level_type="text",
        skill="Name a real weakness and pair it with the concrete action you take to manage it.",
        teach_focus="Honesty without self-sabotage; weakness -> mitigation -> evidence of progress.",
        success_criteria="A genuine, non-cliche weakness plus a specific corrective habit and a sign of improvement.",
        bridge_focus="Finish: 'I used to struggle with ___, so now I ___.'",
        cefr="B2",
        prerequisites=["int_02_strength_with_evidence"],
    ),
    CommNode(
        id="int_04_star_behavioral",
        title="Tell a STAR Story",
        level=4,
        level_type="text",
        skill="Answer a behavioral question using Situation, Task, Action, Result in order.",
        teach_focus="Keep S/T brief, expand A (your specific actions), end on a measurable R.",
        success_criteria="A coherent story with all four STAR beats, weighted toward the learner's own actions and a clear result.",
        bridge_focus="Just the Result first: 'In the end, ___ happened because of what I did.'",
        cefr="B2",
        prerequisites=["int_03_weakness_framing"],
    ),
    CommNode(
        id="int_05_why_this_role",
        title="Why This Company",
        level=5,
        level_type="text",
        skill="Give a tailored, researched reason for wanting this specific role — not a generic one.",
        teach_focus="Tie a company-specific fact to a personal motivation; avoid flattery and platitudes.",
        success_criteria="A motivation that references something concrete about the company and links it to the learner's goals.",
        bridge_focus="Name one specific thing about the company, then: 'That matters to me because ___.'",
        cefr="B2",
        prerequisites=["int_04_star_behavioral"],
    ),
    CommNode(
        id="int_06_own_a_failure",
        title="Own a Failure",
        level=6,
        level_type="text",
        skill="Describe a real failure or gap with full ownership and a credible lesson.",
        teach_focus="Take responsibility without blaming; show the change in behavior that followed.",
        success_criteria="A failure owned in the first person, no deflection, with a specific lesson applied later.",
        bridge_focus="One sentence of ownership: 'That was my call, and it didn't work because ___.'",
        cefr="C1",
        prerequisites=["int_05_why_this_role"],
    ),
    CommNode(
        id="int_07_clarify_before_answering",
        title="Clarify an Ambiguous Question",
        level=7,
        level_type="text",
        skill="Recognize a vague/loaded question and ask a sharp clarifying question before answering.",
        teach_focus="Buy thinking time professionally; narrow scope; confirm what's being asked.",
        success_criteria="A concise clarifying question that meaningfully narrows the prompt, followed by a focused answer.",
        bridge_focus="Just ask one clarifier: 'Do you mean ___ or ___?'",
        cefr="C1",
        prerequisites=["int_06_own_a_failure"],
    ),
    CommNode(
        id="int_08_quantify_impact",
        title="Quantify Your Impact",
        level=8,
        level_type="text",
        skill="Translate vague contributions into numbers, scale, or measurable outcomes.",
        teach_focus="Swap 'helped/improved' for metrics, percentages, scope, or before/after contrast.",
        success_criteria="At least one credible quantified outcome (number, %, scale, or timeframe) tied to the learner's action.",
        bridge_focus="Add one number: 'I ___, which changed ___ by ___.'",
        cefr="C1",
        prerequisites=["int_07_clarify_before_answering"],
    ),
    CommNode(
        id="int_09_diplomatic_pushback",
        title="Disagree With the Interviewer",
        level=9,
        level_type="text",
        skill="Push back on a premise or assertion diplomatically, holding your position with respect.",
        teach_focus="Acknowledge -> reframe -> assert; disagree with the idea, not the person; stay warm.",
        success_criteria="A respectful disagreement that concedes a point, states a clear counter-position, and keeps rapport.",
        bridge_focus="Use the stem: 'I see your point, though I'd argue ___.'",
        cefr="C1",
        prerequisites=["int_08_quantify_impact"],
    ),
    CommNode(
        id="int_10_close_strong",
        title="Close and Ask Sharp Questions",
        level=10,
        level_type="text",
        skill="End the interview by asking an insightful question and stating fit confidently.",
        teach_focus="Ask a question that signals research and ambition; reaffirm value without arrogance.",
        success_criteria="One substantive, non-generic question for the interviewer plus a confident, specific close.",
        bridge_focus="Ask one real question about the role or team, then stop.",
        cefr="C1",
        prerequisites=["int_09_diplomatic_pushback"],
    ),
]

MODULE_ID = "interview"
MODULE_TITLE = "Interview Mastery"
MODULE_DESCRIPTION = (
    "Perform under interview pressure: pitch yourself, structure answers, own "
    "failures, push back diplomatically, and close strong. B2 to C1."
)

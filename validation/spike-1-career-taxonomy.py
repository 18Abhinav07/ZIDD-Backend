"""Prove current report/event fields can drive stable skill IDs and history rows."""

from collections import defaultdict


TAXONOMY = {
    "gd_test": {
        "floor_management": ("floor", "claim", "dominant", "quiet"),
        "evidence_use": ("evidence", "source", "metric", "data"),
        "synthesis": ("synth", "consensus", "opposing"),
    },
    "interview_test": {
        "specificity": ("specific", "example", "evidence"),
        "impact": ("impact", "result", "metric"),
        "role_alignment": ("role", "fit", "company"),
    },
}


def skill_id(task_type: str, gap: str) -> str:
    lowered = gap.lower()
    for skill, markers in TAXONOMY[task_type].items():
        if any(marker in lowered for marker in markers):
            return f"{task_type}:{skill}"
    return f"{task_type}:other"


reports = [
    {"session_id": "s1", "task_type": "gd_test", "status": "final", "score": .72,
     "gaps_json": ["Claim the floor with evidence"]},
    {"session_id": "s2", "task_type": "gd_test", "status": "final", "score": .81,
     "gaps_json": ["Use evidence when claiming the floor"]},
]
history = defaultdict(list)
for report in reports:
    for gap in report["gaps_json"]:
        history[skill_id(report["task_type"], gap)].append(report["session_id"])

assert history == {"gd_test:floor_management": ["s1", "s2"]}
assert all({"session_id", "task_type", "status", "score"} <= report.keys() for report in reports)
print("PASS stable taxonomy and session history can use existing report fields")

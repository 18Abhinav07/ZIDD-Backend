"""Prove current memory rows contain enough metadata for safe mode/validity scoping."""

from app.services.learning_profile import build_career_memory_context


graph = {
    "profiles": [
        {"domain": "career", "skill_id": "int_02", "module_id": "interview",
         "task_type": "interview_prep", "readiness": .7, "mastery": 0, "confidence": .8},
        {"domain": "career", "skill_id": "gd_08", "module_id": "group_discussion",
         "task_type": "gd_prep", "readiness": .7, "mastery": 0, "confidence": .8},
    ],
    "reports": [
        {"report_id": "good", "task_type": "interview_test", "status": "final", "score": .8},
        {"report_id": "bad", "task_type": "gd_test", "status": "invalid_simulation", "score": .9},
    ],
    "events": [],
    "progression": [],
}
memory = build_career_memory_context(graph)
interview = {
    **memory,
    "improving_gaps": [row for row in memory["improving_gaps"] if row["task_type"].startswith("interview")],
    "recent_reports": [row for row in memory["recent_reports"]
                       if row["task_type"].startswith("interview") and row["status"] == "final"],
}
assert [row["skill_id"] for row in interview["improving_gaps"]] == ["int_02"]
assert [row["task_type"] for row in interview["recent_reports"]] == ["interview_test"]
print("PASS memory rows support mode and validity scoping")

"""Prove existing storage and API seams can serve history, reports, and resume links."""

import inspect

from app.api.routes import report
from app.services.learning_profile import CareerLearningProfileService
from app.storage.pg_store import PgStore


class FakeStore:
    async def get_learning_graph(self, user_id: str) -> dict:
        return {
            "profiles": [],
            "reports": [{"session_id": "ended-1", "task_type": "gd_test", "created_at": 123}],
            "events": [{"session_id": "prep-1", "task_type": "interview_prep", "occurred_at": 122}],
            "progression": [],
        }


assert inspect.iscoroutinefunction(report)
assert hasattr(PgStore, "get_latest_active_session_runtime_for_module")
assert inspect.iscoroutinefunction(CareerLearningProfileService.get_learning_graph)
graph = __import__("asyncio").run(CareerLearningProfileService(FakeStore()).get_learning_graph("u1"))
assert graph["reports"][0]["session_id"] == "ended-1"
assert graph["events"][0]["session_id"] == "prep-1"
print("PASS existing report, event, and active-runtime seams support continuity UI")

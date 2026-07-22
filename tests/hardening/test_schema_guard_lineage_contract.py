from __future__ import annotations

import copy

import pytest

from app.db import engine as db_engine
from app.db import schema_guard


SENSITIVE_SCHOOL_TABLES = {
    table
    for table in schema_guard.REQUIRED_RUNTIME_COLUMNS
    if table.startswith("school_")
}


class _FakeResult:
    def __init__(self, rows: list[dict[str, str]]) -> None:
        self._rows = rows

    def mappings(self) -> "_FakeResult":
        return self

    def all(self) -> list[dict[str, str]]:
        return self._rows


class _FakeSession:
    def __init__(self, result_sets: list[list[dict[str, str]]]) -> None:
        self._result_sets = iter(result_sets)

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def execute(self, _query) -> _FakeResult:
        return _FakeResult(next(self._result_sets))


def _legacy_retirement_guard_rows() -> list[dict[str, str]]:
    return [
        {
            "table_name": "sessions",
            "trigger_name": "sessions_reject_active_legacy_school",
            "function_schema": "public",
            "function_name": "reject_active_legacy_school_session_row",
            "tgenabled": "O",
            "trigger_definition": (
                "CREATE TRIGGER sessions_reject_active_legacy_school "
                "BEFORE INSERT OR UPDATE ON public.sessions FOR EACH ROW "
                "EXECUTE FUNCTION public.reject_active_legacy_school_session_row()"
            ),
            "function_definition": (
                "CREATE OR REPLACE FUNCTION public.reject_active_legacy_school_session_row() "
                "RETURNS trigger LANGUAGE plpgsql AS $function$ BEGIN "
                "IF NEW.status IS DISTINCT FROM 'ended' AND ("
                "NEW.module_id = 'school_english' OR NEW.task_type = 'school_english' "
                "OR EXISTS (SELECT 1 FROM public.session_runtime runtime "
                "WHERE runtime.session_id = NEW.session_id AND ("
                "runtime.module_id = 'school_english' "
                "OR runtime.task_type = 'school_english' "
                "OR runtime.state_snapshot ->> 'module_id' = 'school_english' "
                "OR runtime.state_snapshot ->> 'task_type' = 'school_english' "
                "OR runtime.state_snapshot ->> 'block_reason' "
                "= 'legacy_school_module_retired' "
                "OR runtime.last_error ->> 'code' "
                "= 'legacy_school_module_retired'))) "
                "THEN RAISE EXCEPTION 'legacy_school_module_retired:%', NEW.session_id; "
                "END IF; RETURN NEW; END; $function$"
            ),
        },
        {
            "table_name": "session_runtime",
            "trigger_name": "session_runtime_reject_active_legacy_school",
            "function_schema": "public",
            "function_name": "reject_active_legacy_school_runtime_row",
            "tgenabled": "O",
            "trigger_definition": (
                "CREATE TRIGGER session_runtime_reject_active_legacy_school "
                "BEFORE INSERT OR UPDATE ON public.session_runtime FOR EACH ROW "
                "EXECUTE FUNCTION public.reject_active_legacy_school_runtime_row()"
            ),
            "function_definition": (
                "CREATE OR REPLACE FUNCTION public.reject_active_legacy_school_runtime_row() "
                "RETURNS trigger LANGUAGE plpgsql AS $function$ BEGIN "
                "IF NEW.status IS DISTINCT FROM 'ended' AND ("
                "NEW.module_id = 'school_english' OR NEW.task_type = 'school_english' "
                "OR NEW.state_snapshot ->> 'module_id' = 'school_english' "
                "OR NEW.state_snapshot ->> 'task_type' = 'school_english' "
                "OR NEW.state_snapshot ->> 'block_reason' "
                "= 'legacy_school_module_retired' "
                "OR NEW.last_error ->> 'code' = 'legacy_school_module_retired' "
                "OR EXISTS (SELECT 1 FROM public.sessions parent "
                "WHERE parent.session_id = NEW.session_id AND ("
                "parent.module_id = 'school_english' "
                "OR parent.task_type = 'school_english'))) "
                "THEN RAISE EXCEPTION 'legacy_school_module_retired:%', NEW.session_id; "
                "END IF; RETURN NEW; END; $function$"
            ),
        },
    ]


def _valid_snapshot() -> dict[str, list[dict[str, str]]]:
    columns = [
        {
            "table_name": table,
            "column_name": column,
            "data_type": (
                "uuid"
                if (table, column) in schema_guard.REQUIRED_RUNTIME_COLUMN_TYPES
                else "text"
            ),
            "udt_name": (
                "uuid"
                if (table, column) in schema_guard.REQUIRED_RUNTIME_COLUMN_TYPES
                else "text"
            ),
            "is_nullable": (
                "YES"
                if (table, column)
                in {
                    ("school_placement_reports", "evaluated_class_no"),
                    ("school_placement_reports", "active_learning_class_no"),
                }
                else "NO"
            ),
        }
        for table, required_columns in schema_guard.REQUIRED_RUNTIME_COLUMNS.items()
        for column in required_columns
    ]
    indexes = []
    for name, tokens in schema_guard.REQUIRED_RUNTIME_INDEXES.items():
        indexdef = " ".join(tokens)
        if name == "idx_school_sessions_one_active_flow":
            indexdef = (
                "CREATE UNIQUE INDEX idx_school_sessions_one_active_flow "
                "ON public.school_sessions USING btree "
                "(user_id, flow_type, subject_id, class_no) "
                "WHERE status IN ('active', 'paused_for_masterclass')"
            )
        elif name == "idx_school_curriculum_releases_one_current":
            indexdef = (
                "CREATE UNIQUE INDEX idx_school_curriculum_releases_one_current "
                "ON public.school_curriculum_releases USING btree "
                "(board_id, subject_id, class_no, academic_year) "
                "WHERE status = 'current'"
            )
        elif name == "school_curriculum_releases_identity_digest_unique":
            indexdef = (
                "CREATE UNIQUE INDEX school_curriculum_releases_identity_digest_unique "
                "ON public.school_curriculum_releases USING btree "
                "(board_id, subject_id, class_no, academic_year, release_digest)"
            )
        indexes.append(
            {
                "indexname": name,
                "indexdef": indexdef,
                "indisvalid": True,
                "indisready": True,
            }
        )
    foreign_keys = [
        {
            "table_name": table,
            "constraint_name": f"{table}_{column}_fkey",
            "column_name": column,
            "foreign_table_name": foreign_table,
            "foreign_column_name": foreign_column,
            "column_position": 1,
            "convalidated": True,
            "confupdtype": "a",
            "confdeltype": "a",
        }
        for table, column, foreign_table, foreign_column in (
            schema_guard.REQUIRED_RUNTIME_FOREIGN_KEYS
        )
    ]
    for index, (
        table,
        source_columns,
        foreign_table,
        foreign_columns,
    ) in enumerate(schema_guard.REQUIRED_RUNTIME_COMPOSITE_FOREIGN_KEYS):
        requirement = (table, source_columns, foreign_table, foreign_columns)
        confupdtype, confdeltype = (
            schema_guard.REQUIRED_RUNTIME_COMPOSITE_FOREIGN_KEY_ACTIONS.get(
                requirement,
                ("a", "a"),
            )
        )
        constraint_name = f"composite_foreign_key_{index}"
        foreign_keys.extend(
            {
                "table_name": table,
                "constraint_name": constraint_name,
                "column_name": column,
                "foreign_table_name": foreign_table,
                "foreign_column_name": foreign_column,
                "column_position": position,
                "convalidated": True,
                "confupdtype": confupdtype,
                "confdeltype": confdeltype,
            }
            for position, (column, foreign_column) in enumerate(
                zip(source_columns, foreign_columns),
                start=1,
            )
        )
    checks = [
        {
            "table_name": "school_sessions",
            "constraint_name": "school_rebuild_active_profile_lineage",
            "constraint_definition": (
                "CHECK (((api_version <> 'rebuild'::text) OR "
                "(status <> ALL (ARRAY['active'::text, "
                "'paused_for_masterclass'::text])) OR "
                "(profile_version_id IS NOT NULL)))"
            ),
        },
        {
            "table_name": "school_profile_versions",
            "constraint_name": "school_profile_versions_complete_non_drafts",
            "constraint_definition": (
                "CHECK (((status <> 'active'::text) OR "
                "((display_name IS NOT NULL) AND (school_name IS NOT NULL) AND "
                "(board_id IN ('cbse'::text, 'ncert'::text)) AND "
                "(target_class_no BETWEEN 2 AND 5) AND "
                "(subject_ids IS NOT NULL) AND "
                "(jsonb_array_length(subject_ids) > 0) AND "
                "(subject_ids <@ '[\"english\"]'::jsonb) AND "
                "(preferred_teaching_language IN ('en'::text, 'hi'::text, 'hi_en'::text)) AND "
                "(english_comfort IN ('low'::text, 'medium'::text, 'high'::text)) AND "
                "(learner_goal IS NOT NULL) AND "
                "(parent_goal IS NOT NULL) AND "
                "((NULLIF(btrim(learner_goal), ''::text) IS NOT NULL) OR "
                "(NULLIF(btrim(parent_goal), ''::text) IS NOT NULL)) AND "
                "(prior_difficulty_signals IS NOT NULL) AND "
                "(prior_difficulty_signals <@ "
                "'[\"reading\", \"vocabulary\", \"grammar\", \"writing\", "
                "\"chapter_answers\"]'::jsonb))))"
            ),
        },
        {
            "table_name": "school_profile_versions",
            "constraint_name": "school_profile_versions_lifecycle",
            "constraint_definition": (
                "CHECK ((((status = 'draft'::text) AND (activated_at IS NULL) AND "
                "(archived_at IS NULL)) OR ((status = 'active'::text) AND "
                "(activated_at IS NOT NULL) AND (archived_at IS NULL)) OR "
                "((status = 'archived'::text) AND (archived_at IS NOT NULL))))"
            ),
        },
        {
            "table_name": "learning_events",
            "constraint_name": "learning_events_domain",
            "constraint_definition": "CHECK (domain IN ('career', 'school'))",
        },
        {
            "table_name": "learning_events",
            "constraint_name": "learning_events_domain_task",
            "constraint_definition": (
                "CHECK (((domain = 'school' AND task_type LIKE 'school\\_%') OR "
                "(domain = 'career' AND task_type NOT LIKE 'school\\_%')))"
            ),
        },
        {
            "table_name": "learner_skill_profiles",
            "constraint_name": "learner_skill_profiles_domain",
            "constraint_definition": "CHECK (domain IN ('career', 'school'))",
        },
        {
            "table_name": "learner_skill_profiles",
            "constraint_name": "learner_skill_profiles_domain_task",
            "constraint_definition": (
                "CHECK (((domain = 'school' AND task_type LIKE 'school\\_%') OR "
                "(domain = 'career' AND task_type NOT LIKE 'school\\_%')))"
            ),
        },
        {
            "table_name": "school_evaluation_jobs",
            "constraint_name": "school_evaluation_jobs_request_metadata_object",
            "constraint_definition": (
                "CHECK (jsonb_typeof(request_metadata_json) = 'object'::text)"
            ),
        },
    ]
    for check in checks:
        check["convalidated"] = True
    return {
        "columns": columns,
        "indexes": indexes,
        "foreign_keys": foreign_keys,
        "checks": checks,
        "rls": [
            {"table_name": table, "rls_enabled": True}
            for table in sorted(SENSITIVE_SCHOOL_TABLES)
        ],
        "privileges": [],
        "release_rows": [
            dict(row) for row in schema_guard.REQUIRED_SCHOOL_CURRICULUM_RELEASES
        ],
        "immutability": [
            {
                "table_name": "school_curriculum_releases",
                "trigger_name": "school_curriculum_releases_immutable",
                "function_schema": "public",
                "function_name": "reject_school_curriculum_release_identity_change",
                "tgenabled": "O",
                "trigger_definition": (
                    "CREATE TRIGGER school_curriculum_releases_immutable "
                    "BEFORE UPDATE OR DELETE "
                    "ON public.school_curriculum_releases FOR EACH ROW EXECUTE FUNCTION "
                    "reject_school_curriculum_release_identity_change()"
                ),
                "function_definition": (
                    "CREATE FUNCTION reject_school_curriculum_release_identity_change "
                    "RAISE EXCEPTION school_curriculum_release_immutable "
                    "RETURN OLD"
                ),
            },
            *_legacy_retirement_guard_rows(),
        ],
    }


def _install_fake_session(monkeypatch, snapshot: dict[str, list[dict[str, str]]]) -> None:
    result_sets = [
        snapshot["columns"],
        snapshot["indexes"],
        snapshot["foreign_keys"],
        snapshot["checks"],
        snapshot["rls"],
        snapshot["privileges"],
        snapshot["release_rows"],
        snapshot["immutability"],
    ]
    monkeypatch.setattr(
        db_engine,
        "get_sessionmaker",
        lambda: lambda: _FakeSession(result_sets),
    )


def _direct_connection(snapshot: dict[str, list[dict[str, str]]]) -> _FakeSession:
    return _FakeSession(
        [
            snapshot["columns"],
            snapshot["indexes"],
            snapshot["foreign_keys"],
            snapshot["checks"],
            snapshot["rls"],
            snapshot["privileges"],
            snapshot["release_rows"],
            snapshot["immutability"],
        ]
    )


def test_lineage_type_fk_and_check_points_are_required():
    points = set(schema_guard.required_schema_points())

    assert "public.school_migration_markers.migration_key" in points
    assert "public.school_migration_markers.claimed_at" in points
    assert "public.school_sessions.profile_version_id.type.uuid" in points
    assert "public.school_sessions.source_placement_report_id.type.uuid" in points
    assert (
        "public.foreign_key.school_sessions.profile_version_id"
        "->public.school_profile_versions.profile_version_id"
    ) in points
    assert (
        "public.foreign_key.school_sessions.source_placement_report_id"
        "->public.school_placement_reports.report_id"
    ) in points
    assert (
        "public.check.school_sessions.school_rebuild_active_profile_lineage"
    ) in points
    assert (
        "public.check.school_profile_versions.school_profile_versions_complete_non_drafts"
    ) in points
    assert (
        "public.composite_foreign_key.school_sessions.(user_id,linked_session_id)"
        "->public.school_sessions.(user_id,session_id)"
    ) in points
    assert "public.trigger.sessions_reject_active_legacy_school" in points
    assert "public.function.reject_active_legacy_school_session_row" in points
    assert "public.trigger.session_runtime_reject_active_legacy_school" in points
    assert "public.function.reject_active_legacy_school_runtime_row" in points
    for table in SENSITIVE_SCHOOL_TABLES:
        assert f"public.rls.{table}.enabled" in points
        assert f"public.privileges.{table}.api_roles_none" in points


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("drift", "expected_point"),
    [
        (
            "profile_type",
            "public.school_sessions.profile_version_id.type.uuid",
        ),
        (
            "source_report_type",
            "public.school_sessions.source_placement_report_id.type.uuid",
        ),
        (
            "profile_fk",
            "public.foreign_key.school_sessions.profile_version_id"
            "->public.school_profile_versions.profile_version_id",
        ),
        (
            "profile_fk_missing",
            "public.foreign_key.school_sessions.profile_version_id"
            "->public.school_profile_versions.profile_version_id",
        ),
        (
            "source_report_fk",
            "public.foreign_key.school_sessions.source_placement_report_id"
            "->public.school_placement_reports.report_id",
        ),
        (
            "active_check",
            "public.check.school_sessions.school_rebuild_active_profile_lineage",
        ),
        (
            "active_check_missing",
            "public.check.school_sessions.school_rebuild_active_profile_lineage",
        ),
        (
            "profile_completion_check_missing",
            "public.check.school_profile_versions.school_profile_versions_complete_non_drafts",
        ),
        (
            "request_metadata_check_missing",
            "public.check.school_evaluation_jobs.school_evaluation_jobs_request_metadata_object",
        ),
    ],
)
async def test_runtime_guard_rejects_lineage_schema_drift(
    monkeypatch,
    drift: str,
    expected_point: str,
):
    snapshot = copy.deepcopy(_valid_snapshot())
    if drift in {"profile_type", "source_report_type"}:
        column_name = (
            "profile_version_id"
            if drift == "profile_type"
            else "source_placement_report_id"
        )
        row = next(
            row
            for row in snapshot["columns"]
            if row["table_name"] == "school_sessions"
            and row["column_name"] == column_name
        )
        row.update(data_type="text", udt_name="text")
    elif drift in {"profile_fk", "source_report_fk", "profile_fk_missing"}:
        column_name = (
            "profile_version_id"
            if drift in {"profile_fk", "profile_fk_missing"}
            else "source_placement_report_id"
        )
        row = next(
            row
            for row in snapshot["foreign_keys"]
            if row["table_name"] == "school_sessions"
            and row["column_name"] == column_name
        )
        if drift == "profile_fk_missing":
            snapshot["foreign_keys"].remove(row)
        else:
            row["foreign_column_name"] = "user_id"
    elif drift == "active_check_missing":
        snapshot["checks"] = [
            row
            for row in snapshot["checks"]
            if row["constraint_name"] != "school_rebuild_active_profile_lineage"
        ]
    elif drift == "profile_completion_check_missing":
        snapshot["checks"] = [
            row
            for row in snapshot["checks"]
            if row["constraint_name"] != "school_profile_versions_complete_non_drafts"
        ]
    elif drift == "request_metadata_check_missing":
        snapshot["checks"] = [
            row
            for row in snapshot["checks"]
            if row["constraint_name"]
            != "school_evaluation_jobs_request_metadata_object"
        ]
    else:
        snapshot["checks"][0]["constraint_definition"] = (
            "CHECK (profile_version_id IS NOT NULL)"
        )

    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    assert expected_point in str(exc_info.value)


@pytest.mark.asyncio
async def test_runtime_guard_accepts_exact_lineage_constraints(monkeypatch):
    _install_fake_session(monkeypatch, _valid_snapshot())

    await schema_guard.validate_runtime_schema()


@pytest.mark.asyncio
async def test_runtime_guard_accepts_enabled_legacy_retirement_guards(monkeypatch):
    snapshot = _valid_snapshot()
    guard_names = {
        row["trigger_name"]
        for row in snapshot["immutability"]
        if "legacy_school" in row["trigger_name"]
    }
    assert guard_names == {
        "sessions_reject_active_legacy_school",
        "session_runtime_reject_active_legacy_school",
    }
    _install_fake_session(monkeypatch, snapshot)

    await schema_guard.validate_runtime_schema()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("trigger_name", "function_name"),
    (
        (
            "sessions_reject_active_legacy_school",
            "reject_active_legacy_school_session_row",
        ),
        (
            "session_runtime_reject_active_legacy_school",
            "reject_active_legacy_school_runtime_row",
        ),
    ),
)
async def test_runtime_guard_rejects_missing_legacy_retirement_guard(
    monkeypatch,
    trigger_name,
    function_name,
):
    snapshot = _valid_snapshot()
    snapshot["immutability"] = [
        row
        for row in snapshot["immutability"]
        if row["trigger_name"] != trigger_name
    ]
    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    error = str(exc_info.value)
    assert f"public.trigger.{trigger_name}" in error
    assert f"public.function.{function_name}" in error


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "trigger_name",
    (
        "sessions_reject_active_legacy_school",
        "session_runtime_reject_active_legacy_school",
    ),
)
async def test_runtime_guard_rejects_disabled_legacy_retirement_guard(
    monkeypatch,
    trigger_name,
):
    snapshot = _valid_snapshot()
    row = next(
        row
        for row in snapshot["immutability"]
        if row["trigger_name"] == trigger_name
    )
    row["tgenabled"] = "D"
    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    assert f"public.trigger.{trigger_name}" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("trigger_name", "function_name"),
    (
        (
            "sessions_reject_active_legacy_school",
            "reject_active_legacy_school_session_row",
        ),
        (
            "session_runtime_reject_active_legacy_school",
            "reject_active_legacy_school_runtime_row",
        ),
    ),
)
async def test_runtime_guard_rejects_legacy_trigger_bound_to_wrong_function(
    monkeypatch,
    trigger_name,
    function_name,
):
    snapshot = _valid_snapshot()
    row = next(
        row
        for row in snapshot["immutability"]
        if row["trigger_name"] == trigger_name
    )
    row["function_name"] = "wrong_legacy_school_guard"
    row["trigger_definition"] = row["trigger_definition"].replace(
        function_name,
        "wrong_legacy_school_guard",
    )
    row["function_definition"] = row["function_definition"].replace(
        function_name,
        "wrong_legacy_school_guard",
    )
    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    error = str(exc_info.value)
    assert f"public.trigger.{trigger_name}" in error
    assert f"public.function.{function_name}" in error


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "column_name",
    ("evaluated_class_no", "active_learning_class_no"),
)
async def test_runtime_guard_rejects_non_nullable_placement_report_classes(
    monkeypatch,
    column_name,
):
    snapshot = _valid_snapshot()
    row = next(
        row
        for row in snapshot["columns"]
        if row["table_name"] == "school_placement_reports"
        and row["column_name"] == column_name
    )
    row["is_nullable"] = "NO"
    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    assert (
        f"public.school_placement_reports.{column_name}.nullable"
        in str(exc_info.value)
    )


@pytest.mark.asyncio
async def test_validate_runtime_schema_accepts_direct_nullable_information_schema_rows():
    snapshot = _valid_snapshot()

    await schema_guard.validate_runtime_schema(_direct_connection(snapshot))


@pytest.mark.asyncio
async def test_validate_runtime_schema_rejects_direct_non_nullable_information_schema_rows():
    snapshot = _valid_snapshot()
    row = next(
        row
        for row in snapshot["columns"]
        if row["table_name"] == "school_placement_reports"
        and row["column_name"] == "evaluated_class_no"
    )
    row["is_nullable"] = "NO"

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema(_direct_connection(snapshot))

    assert (
        "public.school_placement_reports.evaluated_class_no.nullable"
        in str(exc_info.value)
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("drift", ["rls_disabled", "api_grant"])
async def test_runtime_guard_rejects_school_table_security_drift(monkeypatch, drift):
    snapshot = _valid_snapshot()
    table = "school_answer_requests"
    if drift == "rls_disabled":
        row = next(row for row in snapshot["rls"] if row["table_name"] == table)
        row["rls_enabled"] = False
        expected = f"public.rls.{table}.enabled"
    else:
        snapshot["privileges"].append(
            {
                "table_name": table,
                "grantee": "authenticated",
                "privilege_type": "SELECT",
            }
        )
        expected = f"public.privileges.{table}.api_roles_none"

    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    assert expected in str(exc_info.value)


@pytest.mark.asyncio
async def test_runtime_guard_rejects_profile_scoped_active_school_session_index(
    monkeypatch,
):
    snapshot = _valid_snapshot()
    active_index = next(
        row
        for row in snapshot["indexes"]
        if row["indexname"] == "idx_school_sessions_one_active_flow"
    )
    active_index["indexdef"] = (
        "CREATE UNIQUE INDEX idx_school_sessions_one_active_flow "
        "ON public.school_sessions USING btree "
        "(user_id, profile_version_id, flow_type, subject_id, class_no) "
        "WHERE status IN ('active', 'paused_for_masterclass')"
    )
    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    assert "public.index.idx_school_sessions_one_active_flow" in str(exc_info.value)


@pytest.mark.asyncio
async def test_runtime_guard_rejects_empty_canonical_release_authority(monkeypatch):
    snapshot = _valid_snapshot()
    snapshot["release_rows"] = []
    snapshot["immutability"] = [
        {
            "trigger_name": "school_curriculum_releases_immutable",
            "trigger_definition": (
                "CREATE TRIGGER school_curriculum_releases_immutable BEFORE UPDATE "
                "ON public.school_curriculum_releases FOR EACH ROW EXECUTE FUNCTION "
                "reject_school_curriculum_release_identity_change()"
            ),
            "function_definition": "school_curriculum_release_immutable manifest release_digest",
        }
    ]
    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    assert "public.data.school_curriculum_releases.canonical_rows" in str(exc_info.value)


@pytest.mark.asyncio
async def test_runtime_guard_rejects_missing_release_immutability_trigger(monkeypatch):
    snapshot = _valid_snapshot()
    snapshot["release_rows"] = [
        dict(row) for row in schema_guard.REQUIRED_SCHOOL_CURRICULUM_RELEASES
    ]
    snapshot["immutability"] = []
    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    assert "public.trigger.school_curriculum_releases_immutable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_runtime_guard_rejects_missing_release_uniqueness(monkeypatch):
    snapshot = _valid_snapshot()
    snapshot["release_rows"] = [
        dict(row) for row in schema_guard.REQUIRED_SCHOOL_CURRICULUM_RELEASES
    ]
    snapshot["immutability"] = [
        {
            "trigger_name": "school_curriculum_releases_immutable",
            "trigger_definition": (
                "CREATE TRIGGER school_curriculum_releases_immutable BEFORE UPDATE "
                "ON public.school_curriculum_releases FOR EACH ROW EXECUTE FUNCTION "
                "reject_school_curriculum_release_identity_change()"
            ),
            "function_definition": "school_curriculum_release_immutable manifest release_digest",
        }
    ]
    snapshot["indexes"] = [
        row
        for row in snapshot["indexes"]
        if row["indexname"] != "idx_school_curriculum_releases_one_current"
    ]
    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    assert "public.index.idx_school_curriculum_releases_one_current" in str(
        exc_info.value
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("flag", ["indisvalid", "indisready"])
async def test_runtime_guard_rejects_invalid_or_unready_required_index(
    monkeypatch,
    flag,
):
    snapshot = _valid_snapshot()
    row = next(
        row
        for row in snapshot["indexes"]
        if row["indexname"] == "idx_school_sessions_one_active_flow"
    )
    row[flag] = False
    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    assert "public.index.idx_school_sessions_one_active_flow" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value"),
    [("convalidated", False), ("confdeltype", "c"), ("confupdtype", "c")],
)
async def test_runtime_guard_rejects_unvalidated_or_cascading_lineage_fk(
    monkeypatch,
    field,
    value,
):
    snapshot = _valid_snapshot()
    row = next(
        row
        for row in snapshot["foreign_keys"]
        if row["table_name"] == "school_sessions"
        and row["column_name"] == "curriculum_release_id"
    )
    row[field] = value
    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    assert "public.foreign_key.school_sessions.curriculum_release_id" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_runtime_guard_requires_the_evaluation_job_request_cascade(
    monkeypatch,
):
    snapshot = _valid_snapshot()
    row = next(
        row
        for row in snapshot["foreign_keys"]
        if row["table_name"] == "school_evaluation_jobs"
        and row["column_name"] == "session_id"
    )
    row["confdeltype"] = "a"
    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    assert (
        "public.composite_foreign_key.school_evaluation_jobs."
        "(session_id,activity_id)->public.school_answer_requests."
        "(session_id,activity_id)"
    ) in str(exc_info.value)


@pytest.mark.asyncio
async def test_runtime_guard_skips_school_evaluation_job_drift_only_when_disabled(
    monkeypatch,
):
    snapshot = _valid_snapshot()
    snapshot["columns"] = [
        row
        for row in snapshot["columns"]
        if not (
            row["table_name"] == "school_evaluation_jobs"
            and row["column_name"]
            in {"request_metadata_json", "next_attempt_at"}
        )
    ]
    snapshot["foreign_keys"] = [
        row
        for row in snapshot["foreign_keys"]
        if row["table_name"] != "school_evaluation_jobs"
    ]

    career_points = set(
        schema_guard.required_schema_points(school_runtime_enabled=False)
    )
    assert "public.sessions.status" in career_points
    assert "public.school_evaluation_jobs.request_metadata_json" not in career_points
    assert (
        "public.composite_foreign_key.school_evaluation_jobs."
        "(session_id,activity_id)->public.school_answer_requests."
        "(session_id,activity_id)"
    ) not in career_points

    career_connection = _FakeSession(
        [
            snapshot["columns"],
            snapshot["indexes"],
            snapshot["foreign_keys"],
            snapshot["checks"],
        ]
    )
    await schema_guard.validate_runtime_schema(
        connection=career_connection,
        school_runtime_enabled=False,
    )

    _install_fake_session(monkeypatch, snapshot)
    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema(school_runtime_enabled=True)

    error = str(exc_info.value)
    assert "public.school_evaluation_jobs.request_metadata_json" in error
    assert (
        "public.composite_foreign_key.school_evaluation_jobs."
        "(session_id,activity_id)->public.school_answer_requests."
        "(session_id,activity_id)"
    ) in error


@pytest.mark.asyncio
async def test_runtime_guard_rejects_disabled_release_trigger(monkeypatch):
    snapshot = _valid_snapshot()
    snapshot["immutability"][0]["tgenabled"] = "D"
    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    assert "public.trigger.school_curriculum_releases_immutable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_runtime_guard_rejects_tampered_manifest_even_with_expected_digest(
    monkeypatch,
):
    snapshot = _valid_snapshot()
    snapshot["release_rows"][0]["manifest"] = {
        **snapshot["release_rows"][0]["manifest"],
        "book_title": "tampered",
    }
    _install_fake_session(monkeypatch, snapshot)

    with pytest.raises(schema_guard.SchemaDriftError) as exc_info:
        await schema_guard.validate_runtime_schema()

    assert "public.data.school_curriculum_releases.canonical_rows" in str(exc_info.value)

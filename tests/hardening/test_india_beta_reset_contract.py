from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts import reset_india_beta_database as reset


def _settings(**overrides):
    values = {
        "app_env": "dev",
        "data_region": "india",
        "supabase_direct_url_ind": (
            "postgresql://postgres:secret@db.india.example:5432/postgres"
        ),
        "supabase_transaction_pooler_url_ind": (
            "postgresql://postgres.project:secret@pool.india.example:6543/postgres"
        ),
        "supabase_db_password_ind": "secret",
        "migration_database_configured": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_india_beta_reset_target_requires_dev_india_and_exact_direct_host():
    settings = _settings()

    target = reset.validate_india_beta_reset_target(
        settings,
        expected_direct_host="db.india.example",
    )

    assert target.direct_host == "db.india.example"
    assert target.runtime_host == "pool.india.example"


@pytest.mark.parametrize(
    "overrides, expected_code",
    [
        ({"data_region": "default"}, "india_beta_reset_requires_data_region_india"),
        ({"app_env": "prod"}, "india_beta_reset_forbidden_in_production"),
        ({"supabase_direct_url_ind": ""}, "india_beta_reset_direct_database_missing"),
    ],
)
def test_india_beta_reset_fails_closed_for_wrong_environment(overrides, expected_code):
    with pytest.raises(reset.IndiaBetaResetRefused, match=expected_code):
        reset.validate_india_beta_reset_target(
            _settings(**overrides),
            expected_direct_host="db.india.example",
        )


def test_india_beta_reset_rejects_wrong_explicit_host_even_when_region_is_india():
    with pytest.raises(
        reset.IndiaBetaResetRefused,
        match="india_beta_reset_direct_host_mismatch",
    ):
        reset.validate_india_beta_reset_target(
            _settings(),
            expected_direct_host="wrong.india.example",
        )


def test_reset_plan_wipes_user_owned_runtime_data_but_preserves_migration_and_release_tables():
    plan = reset.india_beta_reset_plan()

    assert "learner_profiles" in plan.truncate_tables
    assert "school_sessions" in plan.truncate_tables
    assert "credit_transactions" in plan.truncate_tables
    assert "school_migration_markers" not in plan.truncate_tables
    assert "school_curriculum_releases" not in plan.truncate_tables
    assert plan.preserve_tables == (
        "school_migration_markers",
        "school_curriculum_releases",
    )


def test_reset_plan_statement_uses_only_the_explicit_public_table_allowlist():
    statement = reset.truncate_statement(reset.india_beta_reset_plan())

    assert statement.startswith("TRUNCATE TABLE public.")
    assert "CASCADE" in statement
    assert "school_migration_markers" not in statement
    assert "school_curriculum_releases" not in statement

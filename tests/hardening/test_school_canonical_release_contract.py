from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.content.school.release_loader import (
    ReleaseSourceVerificationError,
    load_current_release,
    load_release_manifest,
    release_manifest_digest,
    verify_release_sources,
)
from app.content.school.release_schema import CurriculumModule, CurriculumReleaseManifest


EXPECTED_BOOKS = {
    2: {
        "book_title": "Mridang",
        "book_code": "bemr1",
        "isbn": "978-93-5292-434-9",
        "source_sha256": "bd8b09e5eec4502a47bcaa5b46a0e4cb3cee9643fd5e20918a8b72a496ac22ca",
        "source_size_bytes": 2_812_044,
        "edition_history": [("first_edition", "May", 2023), ("reprint", "March", 2024), ("reprint", "March", 2025), ("reprint", "February", 2026)],
    },
    3: {
        "book_title": "Santoor",
        "book_code": "cesa1",
        "isbn": "978-93-5292-991-7",
        "source_sha256": "6b0ce2a24327c9fad6acd997b38a12ce4bff961e729856133c4474656b424816",
        "source_size_bytes": 1_956_951,
        "edition_history": [("first_edition", "April", 2024), ("reprint", "March", 2025), ("reprint", "January", 2026)],
    },
    4: {
        "book_title": "Santoor",
        "book_code": "desa1",
        "isbn": "978-93-5729-932-9",
        "source_sha256": "ab890381b64c55094ea0651adb3e2c68d32a8341665d587ef90873fb9ab35f9a",
        "source_size_bytes": 6_888_606,
        "edition_history": [("first_edition", "March", 2025), ("reprint", "January", 2026)],
    },
    5: {
        "book_title": "Santoor",
        "book_code": "eesa1",
        "isbn": "978-93-5729-062-3",
        "source_sha256": "7ecaefaa0ed0ada410282fa18ab5a944b8e818cbc897993404cc4924a2682e5d",
        "source_size_bytes": 4_469_179,
        "edition_history": [("first_edition", "June", 2025), ("reprint", "January", 2026)],
    },
}

EXPECTED_SECTIONS = {
    2: ["Sing", "Speak", "Read", "Draw", "Say", "Write"],
    3: ["Recite", "Think", "Speak", "Learn", "Listen", "Write", "Do", "Explore"],
    4: ["Read", "Recite", "Think", "Speak", "Learn", "Listen", "Write", "Do", "Explore"],
    5: ["Recite", "Think", "Speak", "Learn", "Listen", "Write", "Do", "Explore"],
}


def _manifest_payload() -> dict:
    path = (
        Path(__file__).parents[2]
        / "app/content/school/releases/english_cbse_2026_27.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _recalculate_digest(payload: dict) -> dict:
    unsigned = deepcopy(payload)
    unsigned.pop("manifest_sha256", None)
    canonical = json.dumps(
        unsigned,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    payload["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def test_manifest_loads_four_strict_current_class_releases():
    manifest = load_release_manifest("english_cbse_2026_27")

    assert manifest.manifest_id == "english_cbse_2026_27"
    assert manifest.academic_year == "2026-27"
    assert manifest.manifest_sha256 == release_manifest_digest(manifest)
    assert [release.class_no for release in manifest.releases] == [2, 3, 4, 5]
    assert len({release.curriculum_release_id for release in manifest.releases}) == 4

    for release in manifest.releases:
        expected = EXPECTED_BOOKS[release.class_no]
        assert release.board_id == "cbse"
        assert release.subject_id == "english"
        assert release.academic_year == "2026-27"
        assert release.release_status == "current"
        assert release.verification_status == "verified"
        assert release.retired_on is None
        assert release.release_label == "Reprint 2026-27"
        assert release.book_title == expected["book_title"]
        assert release.book_code == expected["book_code"]
        assert release.isbn == expected["isbn"]
        assert str(release.official_pdf_url) == (
            f"https://ncert.nic.in/textbook/pdf/{release.book_code}ps.pdf"
        )
        assert str(release.official_selector_url) == "https://ncert.nic.in/textbook.php"
        assert release.curriculum_release_id == (
            f"english_cbse_2026_27_c{release.class_no}_{release.book_code}"
        )
        assert release.source_sha256 == expected["source_sha256"]
        assert release.source_size_bytes == expected["source_size_bytes"]
        assert [
            (entry.kind, entry.month, entry.year)
            for entry in release.edition_history
        ] == expected["edition_history"]
        assert release.effective_from.isoformat() == "2026-04-01"
        assert release.effective_through.isoformat() == "2027-03-31"
        assert release.verification_evidence.verified_on.isoformat() == "2026-07-13"
        assert release.verification_evidence.hash_algorithm == "sha256"
        assert release.verification_evidence.provenance == "official_ncert_pdf"
        assert set(release.language_structures) >= {"listening", "speaking"}
        assert [section.label for section in release.pedagogical_sections] == (
            EXPECTED_SECTIONS[release.class_no]
        )
        assert [section.order for section in release.pedagogical_sections] == list(
            range(1, len(EXPECTED_SECTIONS[release.class_no]) + 1)
        )
        assert all(
            section.source_pdf_page == 6
            and section.source_evidence == "official_front_matter"
            for section in release.pedagogical_sections
        )


def test_current_release_loader_selects_exact_class_and_rejects_unsupported_scope():
    assert load_current_release("english", 2, as_of=date(2026, 4, 1)).book_code == "bemr1"
    assert load_current_release("english", 5, as_of=date(2027, 3, 31)).book_code == "eesa1"

    with pytest.raises(LookupError, match="unsupported_school_release"):
        load_current_release("english", 6)
    with pytest.raises(LookupError, match="unsupported_school_release"):
        load_current_release("math", 2)
    with pytest.raises(LookupError, match="school_release_not_effective"):
        load_current_release("english", 2, as_of=date(2026, 3, 31))
    with pytest.raises(LookupError, match="school_release_not_effective"):
        load_current_release("english", 2, as_of=date(2027, 4, 1))


def test_manifest_represents_units_special_modules_and_reference_structures():
    manifest = load_release_manifest("english_cbse_2026_27")
    releases = {release.class_no: release for release in manifest.releases}

    assert [[unit.title for unit in releases[class_no].units] for class_no in (2, 3, 4, 5)] == [
        ["Fun with Friends", "Welcome to My World", "Going Places", "Life Around Us", "Harmony"],
        ["Fun with Friends", "Toys and Games", "Good Food", "The Sky"],
        ["My Land", "My Beautiful World", "Fun with Games", "Up High"],
        ["Let's Have Fun", "My Colourful World", "Water", "Ups and Downs", "Work is Worship"],
    ]

    all_modules = [
        module
        for release in manifest.releases
        for unit in release.units
        for module in unit.modules
    ]
    assert len(all_modules) > 47
    assert {module.kind for module in all_modules} >= {
        "lesson",
        "picture_reading",
        "self_assessment",
    }
    assert sum(module.kind == "picture_reading" for module in all_modules) == 5
    assert sum(module.kind == "self_assessment" for module in all_modules) == 6
    papa_spectacles = next(
        module for module in all_modules if module.title == "Papa's Spectacles"
    )
    assert papa_spectacles.source_genre == "poem"

    assert [item.title for item in releases[3].reference_modules] == [
        "Our National Anthem"
    ]
    assert [item.title for item in releases[4].reference_modules] == [
        "Constitution of India"
    ]
    assert [item.title for item in releases[5].reference_modules] == [
        "Gandhiji's Talisman"
    ]
    assert all(item.kind == "reference" for release in manifest.releases for item in release.reference_modules)

    for release in manifest.releases:
        for unit in release.units:
            for module in unit.modules:
                assert module.module_id.startswith(f"{unit.unit_id}_m")
                if module.kind == "lesson":
                    assert module.source_genre in {
                        "poem",
                        "story",
                        "prose",
                        "play",
                        "informational",
                        "mixed",
                    }
                else:
                    assert module.source_genre == "none"
        assert all(
            module.source_genre == "reference"
            for module in release.reference_modules
        )


def test_phase_zero_public_display_title_is_format_only_and_phase_bounded():
    compatible = CurriculumModule(
        module_id="eng_c3_u03_m03",
        order=3,
        title="Thank God",
        phase_0_public_display_title="Thank God!",
        kind="lesson",
        source_genre="poem",
    )

    assert compatible.phase_0_public_display_title == "Thank God!"
    with pytest.raises(ValidationError, match="phase_0_public_display_title_mismatch"):
        CurriculumModule(
            module_id="eng_c3_u03_m03",
            order=3,
            title="Thank God",
            phase_0_public_display_title="A Different Lesson",
            kind="lesson",
            source_genre="poem",
        )


def test_release_manifest_contains_metadata_only_not_textbook_body():
    payload = _manifest_payload()
    serialized = json.dumps(payload).lower()

    forbidden_keys = {"body", "body_text", "passage", "chapter_text", "source_prose"}

    def walk(value: object) -> None:
        if isinstance(value, dict):
            assert forbidden_keys.isdisjoint(value)
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)

    walk(payload)
    assert "zidd-authored teaching content" not in serialized


def test_class_two_mixed_prose_play_module_is_not_mislabeled_as_poetry():
    release = load_current_release("english", 2, as_of=date(2026, 7, 13))
    module = next(
        module
        for unit in release.units
        for module in unit.modules
        if module.title == "We are all Indians"
    )

    assert module.source_genre == "mixed"


@pytest.mark.parametrize(
    ("mutate", "error"),
    [
        (lambda p: p.update({"unexpected": True}), "extra_forbidden"),
        (lambda p: p["releases"].append(deepcopy(p["releases"][0])), "duplicate_curriculum_release_id"),
        (lambda p: p["releases"][0].update({"class_no": 1}), "invalid_school_class"),
        (lambda p: p["releases"][0].update({"source_sha256": "bad"}), "string_pattern_mismatch"),
        (lambda p: p["releases"][0]["units"][1].update({"order": 1}), "duplicate_unit_order"),
        (lambda p: p["releases"][0]["units"][0]["modules"][1].update({"order": 1}), "duplicate_module_order"),
        (lambda p: p["releases"][0]["units"][0]["modules"][1].update({"module_id": p["releases"][0]["units"][0]["modules"][0]["module_id"]}), "duplicate_module_id"),
        (lambda p: p["releases"][0].update({"release_status": "current", "retired_on": "2026-07-01"}), "current_release_cannot_be_retired"),
        (lambda p: p["releases"][0].update({"curriculum_release_id": "english_cbse_2026_27_c2_fake1"}), "curriculum_release_id_mismatch"),
        (lambda p: p["releases"][0].update({"official_selector_url": "https://example.com/textbook.php"}), "official_selector_host_invalid"),
        (lambda p: p["releases"][0].update({"official_selector_url": "http://ncert.nic.in/textbook.php"}), "official_selector_scheme_invalid"),
        (lambda p: p["releases"][0].update({"official_selector_url": "https://ncert.nic.in:444/textbook.php"}), "official_selector_port_invalid"),
        (lambda p: p["releases"][0].update({"official_selector_url": "https://user@ncert.nic.in/textbook.php"}), "official_selector_userinfo_invalid"),
        (lambda p: p["releases"][0].update({"official_selector_url": "https://ncert.nic.in/textbook.php?redirect=1"}), "official_selector_query_invalid"),
        (lambda p: p["releases"][0].update({"official_selector_url": "https://ncert.nic.in/textbook.php#contents"}), "official_selector_fragment_invalid"),
        (lambda p: p["releases"][0].update({"official_pdf_url": "https://ncert.nic.in/textbook/pdf/bemr101.pdf"}), "official_pdf_path_invalid"),
        (lambda p: p["releases"][0].update({"official_pdf_url": "http://ncert.nic.in/textbook/pdf/bemr1ps.pdf"}), "official_pdf_scheme_invalid"),
        (lambda p: p["releases"][0].update({"official_pdf_url": "https://ncert.nic.in:444/textbook/pdf/bemr1ps.pdf"}), "official_pdf_port_invalid"),
        (lambda p: p["releases"][0].update({"official_pdf_url": "https://user@ncert.nic.in/textbook/pdf/bemr1ps.pdf"}), "official_pdf_userinfo_invalid"),
        (lambda p: p["releases"][0].update({"official_pdf_url": "https://ncert.nic.in/textbook/pdf/bemr1ps.pdf#page=1"}), "official_pdf_fragment_invalid"),
        (lambda p: p["releases"][0].update({"official_pdf_url": "https://ncert.nic.in/textbook/pdf/bemr1ps.pdf?redirect=1"}), "official_pdf_query_invalid"),
        (lambda p: p["releases"][0]["units"][0]["modules"][0].update({"module_id": "eng_c2_u02_m01"}), "module_unit_mismatch"),
        (lambda p: p["releases"][0].update({"edition_history": [p["releases"][0]["edition_history"][0], p["releases"][0]["edition_history"][2], p["releases"][0]["edition_history"][1], p["releases"][0]["edition_history"][3]]}), "edition_history_not_chronological"),
        (lambda p: p["releases"][0]["edition_history"].append(deepcopy(p["releases"][0]["edition_history"][-1])), "duplicate_edition_history"),
        (lambda p: p["releases"][0].update({"release_status": "retired", "retired_on": "2026-03-31"}), "retired_date_outside_effective_window"),
    ],
)
def test_schema_rejects_invalid_or_mutable_release_shapes(mutate, error):
    payload = _manifest_payload()
    mutate(payload)
    _recalculate_digest(payload)

    with pytest.raises(ValidationError) as exc_info:
        CurriculumReleaseManifest.model_validate_json(json.dumps(payload))

    assert error in str(exc_info.value)


def test_loader_rejects_tampered_manifest_digest(tmp_path: Path):
    payload = _manifest_payload()
    payload["releases"][0]["book_title"] = "Tampered"
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="school_release_manifest_digest_mismatch"):
        load_release_manifest(path)


def test_detached_trusted_lock_rejects_tampering_even_after_embedded_digest_recomputed(
    tmp_path: Path,
):
    payload = _manifest_payload()
    payload["releases"][0]["book_title"] = "Tampered"
    _recalculate_digest(payload)
    path = tmp_path / "tampered-and-resigned.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="school_release_trusted_digest_mismatch"):
        load_release_manifest(path)


def test_source_verification_is_offline_by_default_and_can_hash_local_pdf(tmp_path: Path):
    release = load_current_release("english", 2)
    manifest_only = verify_release_sources(release.curriculum_release_id)

    assert manifest_only.manifest_integrity_checked is True
    assert manifest_only.source_hash_verified is False
    assert manifest_only.source_path is None

    with pytest.raises(TypeError, match="curriculum_release_id_must_be_string"):
        verify_release_sources(release)  # type: ignore[arg-type]


def test_source_verification_fails_on_missing_size_or_hash(tmp_path: Path):
    release = load_current_release("english", 3)
    source = tmp_path / "cesa1ps.pdf"
    source.write_bytes(b"wrong-source")

    with pytest.raises(ReleaseSourceVerificationError, match="source_size_mismatch"):
        verify_release_sources(release.curriculum_release_id, source_dir=tmp_path)

    source.write_bytes(b"x" * release.source_size_bytes)
    with pytest.raises(ReleaseSourceVerificationError, match="source_sha256_mismatch"):
        verify_release_sources(release.curriculum_release_id, source_dir=tmp_path)


def test_verified_local_release_sources_match_trusted_manifest():
    source_dir = Path("/tmp/zidd-ncert-release-sources")
    if not source_dir.exists():
        pytest.skip("verified NCERT source directory not available")

    for release in load_release_manifest().releases:
        result = verify_release_sources(
            release.curriculum_release_id,
            source_dir=source_dir,
        )
        assert result.manifest_integrity_checked is True
        assert result.source_hash_verified is True
        assert result.actual_sha256 == release.source_sha256


def test_release_verifier_runs_from_backend_root():
    backend_root = Path(__file__).parents[2]
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/verify_school_release.py",
            "--release",
            "english_cbse_2026_27",
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "source verified" not in completed.stdout.lower()
    assert completed.stdout.count("manifest_integrity=checked") == 4
    assert completed.stdout.count("source_hash=not_checked") == 4
    assert "classes=4 errors=0" in completed.stdout
    assert "digest=" in completed.stdout


def test_release_verifier_reports_source_hash_only_when_local_bytes_match():
    backend_root = Path(__file__).parents[2]
    source_dir = Path("/tmp/zidd-ncert-release-sources")
    if not source_dir.exists():
        pytest.skip("verified NCERT source directory not available")
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/verify_school_release.py",
            "--release",
            "english_cbse_2026_27",
            "--source-dir",
            str(source_dir),
        ],
        cwd=backend_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.count("source_hash=verified") == 4
    assert "sources_verified=4" in completed.stdout

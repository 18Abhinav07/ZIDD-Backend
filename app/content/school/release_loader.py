"""Offline loader and source verifier for immutable School releases."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .release_schema import CurriculumRelease, CurriculumReleaseManifest


RELEASES_DIR = Path(__file__).resolve().parent / "releases"
_RELEASE_ID = re.compile(r"^[a-z0-9_]+$")
TRUSTED_MANIFEST_DIGESTS = {
    "english_cbse_2026_27": "9e493e73007d640762854b8d3adf5d72b2daf9601eb4833828051b0f29982a0b",
}


class ReleaseSourceVerificationError(ValueError):
    """Raised when a local official source does not match locked metadata."""


@dataclass(frozen=True)
class ReleaseSourceVerification:
    curriculum_release_id: str
    manifest_integrity_checked: bool
    source_hash_verified: bool
    source_path: Path | None
    expected_sha256: str
    actual_sha256: str | None
    expected_size_bytes: int
    actual_size_bytes: int | None


def _canonical_digest(payload: dict) -> str:
    unsigned = dict(payload)
    unsigned.pop("manifest_sha256", None)
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def release_manifest_digest(manifest: CurriculumReleaseManifest) -> str:
    return _canonical_digest(manifest.model_dump(mode="json"))


def _release_path(release: str | Path) -> Path:
    if isinstance(release, Path):
        return release
    if not _RELEASE_ID.fullmatch(release):
        raise ValueError("invalid_school_release_identifier")
    return RELEASES_DIR / f"{release}.json"


def load_release_manifest(
    release: str | Path = "english_cbse_2026_27",
) -> CurriculumReleaseManifest:
    path = _release_path(release)
    try:
        raw_manifest = path.read_text(encoding="utf-8")
        payload = json.loads(raw_manifest)
    except FileNotFoundError as exc:
        raise LookupError(f"school_release_manifest_not_found:{path.name}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid_school_release_manifest_json:{path.name}") from exc

    expected_digest = payload.get("manifest_sha256")
    actual_digest = _canonical_digest(payload)
    if expected_digest != actual_digest:
        raise ValueError("school_release_manifest_digest_mismatch")
    trusted_digest = TRUSTED_MANIFEST_DIGESTS.get(payload.get("manifest_id"))
    if trusted_digest is None or actual_digest != trusted_digest:
        raise ValueError("school_release_trusted_digest_mismatch")

    # Strict models intentionally use Pydantic's JSON boundary so JSON arrays
    # and ISO dates are decoded into their immutable Python counterparts.
    manifest = CurriculumReleaseManifest.model_validate_json(raw_manifest)
    if release_manifest_digest(manifest) != manifest.manifest_sha256:
        raise ValueError("school_release_manifest_digest_mismatch")
    return manifest


def load_current_release(
    subject_id: str = "english",
    class_no: int = 2,
    *,
    board_id: str = "cbse",
    as_of: date | None = None,
) -> CurriculumRelease:
    manifest = load_release_manifest()
    scope_matches = [
        release
        for release in manifest.releases
        if release.subject_id == subject_id
        and release.class_no == class_no
        and release.board_id == board_id
        and release.release_status == "current"
        and release.retired_on is None
    ]
    if len(scope_matches) != 1:
        raise LookupError(
            f"unsupported_school_release:{board_id}:{subject_id}:class_{class_no}"
        )
    selected_date = as_of or date.today()
    release = scope_matches[0]
    if not (release.effective_from <= selected_date <= release.effective_through):
        raise LookupError(
            "school_release_not_effective:"
            f"{release.curriculum_release_id}:{selected_date.isoformat()}"
        )
    if release.retired_on is not None and selected_date > release.retired_on:
        raise LookupError(
            "school_release_retired:"
            f"{release.curriculum_release_id}:{selected_date.isoformat()}"
        )
    return release


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_release_sources(
    curriculum_release_id: str,
    *,
    source_dir: str | Path | None = None,
) -> ReleaseSourceVerification:
    """Verify locked metadata and, optionally, a locally downloaded NCERT PDF.

    No network request is made. API boot can call this without ``source_dir``;
    the CLI can pass a controlled source directory for byte-level verification.
    """

    if not isinstance(curriculum_release_id, str):
        raise TypeError("curriculum_release_id_must_be_string")
    manifest = load_release_manifest()
    matches = [
        release
        for release in manifest.releases
        if release.curriculum_release_id == curriculum_release_id
    ]
    if len(matches) != 1:
        raise LookupError(
            f"school_release_id_not_found:{curriculum_release_id}"
        )
    release = matches[0]

    if source_dir is None:
        return ReleaseSourceVerification(
            curriculum_release_id=release.curriculum_release_id,
            manifest_integrity_checked=True,
            source_hash_verified=False,
            source_path=None,
            expected_sha256=release.source_sha256,
            actual_sha256=None,
            expected_size_bytes=release.source_size_bytes,
            actual_size_bytes=None,
        )

    source_path = Path(source_dir) / f"{release.book_code}ps.pdf"
    if not source_path.is_file():
        raise ReleaseSourceVerificationError(
            f"school_release_source_missing:{source_path}"
        )
    actual_size = source_path.stat().st_size
    if actual_size != release.source_size_bytes:
        raise ReleaseSourceVerificationError(
            "source_size_mismatch:"
            f"{release.book_code}:expected={release.source_size_bytes}:actual={actual_size}"
        )
    actual_sha256 = _sha256_file(source_path)
    if actual_sha256 != release.source_sha256:
        raise ReleaseSourceVerificationError(
            "source_sha256_mismatch:"
            f"{release.book_code}:expected={release.source_sha256}:actual={actual_sha256}"
        )
    return ReleaseSourceVerification(
        curriculum_release_id=release.curriculum_release_id,
        manifest_integrity_checked=True,
        source_hash_verified=True,
        source_path=source_path,
        expected_sha256=release.source_sha256,
        actual_sha256=actual_sha256,
        expected_size_bytes=release.source_size_bytes,
        actual_size_bytes=actual_size,
    )

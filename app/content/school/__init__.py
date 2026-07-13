"""Canonical School curriculum release contracts."""

from .release_loader import (
    load_current_release,
    load_release_manifest,
    release_manifest_digest,
    verify_release_sources,
)
from .release_schema import CurriculumRelease, CurriculumReleaseManifest

__all__ = [
    "CurriculumRelease",
    "CurriculumReleaseManifest",
    "load_current_release",
    "load_release_manifest",
    "release_manifest_digest",
    "verify_release_sources",
]

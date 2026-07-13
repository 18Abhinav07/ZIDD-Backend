"""Verify a canonical School release without network access."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.content.school.release_loader import (
    load_release_manifest,
    release_manifest_digest,
    verify_release_sources,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", default="english_cbse_2026_27")
    parser.add_argument(
        "--source-dir",
        type=Path,
        help="Optional directory containing {book_code}ps.pdf source files.",
    )
    args = parser.parse_args()

    manifest = load_release_manifest(args.release)
    sources_verified = 0
    for release in manifest.releases:
        result = verify_release_sources(
            release.curriculum_release_id,
            source_dir=args.source_dir,
        )
        source_hash_status = (
            "verified" if result.source_hash_verified else "not_checked"
        )
        sources_verified += int(result.source_hash_verified)
        print(
            f"checked class={release.class_no} book={release.book_code} "
            "manifest_integrity=checked "
            f"source_hash={source_hash_status} sha256={release.source_sha256}"
        )
    print(
        f"school_release_checked release={manifest.manifest_id} "
        f"classes={len(manifest.releases)} errors=0 "
        f"sources_verified={sources_verified} "
        f"digest={release_manifest_digest(manifest)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

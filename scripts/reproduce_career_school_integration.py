#!/usr/bin/env python3
"""Reproduce a frozen Career/School integration from its ownership manifest."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


RESTORE_FROM_CAREER = {"career_exact", "manual_union"}
RESTORE_FROM_SCHOOL = {"school_exact", "reference_only"}
REMOVE_BEFORE_PATCH = {"integration_new", "excluded_delete"}


def _run(
    repo: Path,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed ({result.returncode}):\n"
            f"{result.stdout}{result.stderr}"
        )
    return result


def _remove_path(repo: Path, path: str) -> None:
    _run(repo, "rm", "-f", "--ignore-unmatch", "--", path)
    target = repo / path
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)


def _restore(repo: Path, commit: str, path: str) -> None:
    _run(repo, "checkout", commit, "--", path)


def _load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        lines = (line for line in handle if not line.startswith("#"))
        rows = list(csv.DictReader(lines, delimiter="\t"))
    required = {
        "path",
        "disposition",
        "final_mode",
        "final_blob",
        "career_blob",
        "school_blob",
    }
    if not rows or not required.issubset(rows[0]):
        raise RuntimeError("integration_manifest_schema_invalid")
    return rows


def _resolve_rows(
    repo: Path,
    *,
    career: str,
    school: str,
    rows: list[dict[str, str]],
) -> None:
    for row in rows:
        path = row["path"]
        disposition = row["disposition"]
        if disposition in RESTORE_FROM_CAREER:
            if row["career_blob"]:
                _restore(repo, career, path)
            else:
                _remove_path(repo, path)
        elif disposition in RESTORE_FROM_SCHOOL:
            if not row["school_blob"]:
                raise RuntimeError(f"school_blob_missing:{path}")
            _restore(repo, school, path)
        elif disposition in REMOVE_BEFORE_PATCH:
            _remove_path(repo, path)
        else:
            raise RuntimeError(f"unknown_integration_disposition:{disposition}:{path}")


def _assert_manifest_blobs(
    repo: Path,
    rows: list[dict[str, str]],
) -> None:
    indexed = _run(repo, "ls-files", "-s", "-z").stdout.split("\0")
    actual: dict[str, tuple[str, str]] = {}
    for entry in indexed:
        if not entry:
            continue
        metadata, path = entry.split("\t", 1)
        mode, blob, stage = metadata.split()
        if stage == "0":
            actual[path] = (mode, blob)

    mismatches: list[str] = []
    for row in rows:
        expected_blob = row["final_blob"]
        expected_mode = row["final_mode"]
        current = actual.get(row["path"])
        if expected_blob:
            if current != (expected_mode, expected_blob):
                mismatches.append(
                    f"{row['path']}: expected {expected_mode} {expected_blob}, got {current}"
                )
        elif current is not None:
            mismatches.append(f"{row['path']}: expected deletion, got {current}")
    if mismatches:
        raise RuntimeError("integration_blob_mismatch:\n" + "\n".join(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--career", required=True)
    parser.add_argument("--school", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--worktree", type=Path)
    parser.add_argument("--keep-worktree", action="store_true")
    args = parser.parse_args()

    source_repo = Path.cwd().resolve()
    manifest = args.manifest.resolve()
    patch = args.patch.resolve()
    lock = json.loads(args.lock.resolve().read_text(encoding="utf-8"))
    rows = _load_manifest(manifest)

    temporary_root: Path | None = None
    if args.worktree:
        worktree = args.worktree.resolve()
        if worktree.exists():
            raise RuntimeError("reproduction_worktree_must_not_exist")
    else:
        temporary_root = Path(tempfile.mkdtemp(prefix="zidd-integration-repro-"))
        worktree = temporary_root / "worktree"

    _run(source_repo, "cat-file", "-e", f"{args.career}^{{commit}}")
    _run(source_repo, "cat-file", "-e", f"{args.school}^{{commit}}")
    _run(source_repo, "worktree", "add", "--detach", str(worktree), args.career)
    try:
        merge = _run(
            worktree,
            "merge",
            "--no-commit",
            "--no-ff",
            args.school,
            check=False,
        )
        if merge.returncode not in {0, 1}:
            raise RuntimeError(
                f"integration_parent_merge_failed:\n{merge.stdout}{merge.stderr}"
            )

        _resolve_rows(
            worktree,
            career=args.career,
            school=args.school,
            rows=rows,
        )
        _run(worktree, "add", "-A")
        _run(worktree, "apply", "--index", "--binary", str(patch))
        unresolved = _run(
            worktree,
            "diff",
            "--name-only",
            "--diff-filter=U",
        ).stdout.strip()
        if unresolved:
            raise RuntimeError(f"integration_unresolved_paths:\n{unresolved}")

        _assert_manifest_blobs(worktree, rows)
        actual_tree = _run(worktree, "write-tree").stdout.strip()
        expected_tree = str(lock.get("core_tree") or "")
        if actual_tree != expected_tree:
            raise RuntimeError(
                f"integration_tree_mismatch: expected {expected_tree}, got {actual_tree}"
            )
        print(json.dumps({"ok": True, "core_tree": actual_tree}, sort_keys=True))
        return 0
    finally:
        if args.keep_worktree:
            print(f"kept reproduction worktree: {worktree}")
        else:
            _run(source_repo, "worktree", "remove", "--force", str(worktree), check=False)
            if temporary_root is not None:
                shutil.rmtree(temporary_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

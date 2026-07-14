#!/usr/bin/env python3
"""Audit only import/resource paths reachable from active production entrypoints.

Archived V2/V3 modules are intentionally not scanned as production merely
because they remain importable. Active runtime closures have no exceptions.
"""

from __future__ import annotations

import ast
import re
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SCHOOL_ENTRY = "app.api.school_rebuild_routes"
_VERSIONED_SCHOOL_MODULE = re.compile(r"(?:^|\.)(school_v[23](?:_|$))")


@dataclass(frozen=True, order=True)
class RuntimeAuditFinding:
    source_module: str
    target: str
    kind: str


@dataclass(frozen=True)
class RuntimeAuditAllowlistEntry:
    source_module: str
    target: str
    kind: str
    reason: str

    def matches(self, finding: RuntimeAuditFinding) -> bool:
        return (
            self.source_module,
            self.target,
            self.kind,
        ) == (
            finding.source_module,
            finding.target,
            finding.kind,
        )


@dataclass(frozen=True)
class RuntimeAuditReport:
    violations: tuple[RuntimeAuditFinding, ...]
    allowlisted: tuple[RuntimeAuditFinding, ...]
    reachable_modules: tuple[str, ...]


DEFAULT_RUNTIME_ALLOWLIST: tuple[RuntimeAuditAllowlistEntry, ...] = ()


def _module_index(root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for top_level in ("app", "scripts"):
        base = root / top_level
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            relative = path.relative_to(root).with_suffix("")
            parts = list(relative.parts)
            if parts[-1] == "__init__":
                parts.pop()
            if parts:
                index[".".join(parts)] = path
    return index


def _resolve_from_module(
    source_module: str,
    node: ast.ImportFrom,
    *,
    source_is_package: bool,
) -> str:
    if node.level == 0:
        return node.module or ""
    package_parts = source_module.split(".")
    if not source_is_package:
        package_parts.pop()
    if node.level > 1:
        package_parts = package_parts[: -(node.level - 1)]
    if node.module:
        package_parts.extend(node.module.split("."))
    return ".".join(package_parts)


def _imports_for(
    source_module: str,
    path: Path,
    index: dict[str, Path],
) -> tuple[set[str], set[str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    raw_targets: set[str] = set()
    graph_targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                raw_targets.add(alias.name)
                if alias.name in index:
                    graph_targets.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            base = _resolve_from_module(
                source_module,
                node,
                source_is_package=path.name == "__init__.py",
            )
            if base:
                raw_targets.add(base)
                if base in index:
                    graph_targets.add(base)
            for alias in node.names:
                candidate = f"{base}.{alias.name}" if base else alias.name
                if candidate in index:
                    raw_targets.add(candidate)
                    graph_targets.add(candidate)
    return raw_targets, graph_targets


def _reachable_imports(
    root: Path,
    entry_modules: Iterable[str],
) -> tuple[set[str], dict[str, set[str]], dict[str, Path]]:
    index = _module_index(root)
    raw_imports: dict[str, set[str]] = {}
    graph: dict[str, set[str]] = {}
    queue = deque(entry_modules)
    reachable: set[str] = set()
    while queue:
        module = queue.popleft()
        if module in reachable:
            continue
        reachable.add(module)
        path = index.get(module)
        if path is None:
            continue
        raw_targets, graph_targets = _imports_for(module, path, index)
        raw_imports[module] = raw_targets
        graph[module] = graph_targets
        queue.extend(graph_targets - reachable)
    return reachable, raw_imports, index


def _is_forbidden_import(target: str) -> bool:
    return bool(
        _VERSIONED_SCHOOL_MODULE.search(target)
        or target.startswith("app.content.data.school")
        or "generate_school_v3_seed_content" in target
        or "generated_school_seed" in target
    )


def _findings_for_closure(
    root: Path,
    entry_modules: Iterable[str],
) -> tuple[set[str], set[RuntimeAuditFinding]]:
    reachable, raw_imports, _index = _reachable_imports(root, entry_modules)
    findings = {
        RuntimeAuditFinding(source, target, "import")
        for source, targets in raw_imports.items()
        for target in targets
        if _is_forbidden_import(target)
    }
    if "app.content.curriculum" in reachable:
        findings.add(
            RuntimeAuditFinding(
                "app.content.curriculum",
                "app.content.data.school",
                "resource",
            )
        )
    return reachable, findings


def audit_school_runtime_authority(
    root: str | Path = ROOT,
    *,
    entry_modules: tuple[str, ...] = ("app.main",),
    allowlist: tuple[RuntimeAuditAllowlistEntry, ...] = DEFAULT_RUNTIME_ALLOWLIST,
) -> RuntimeAuditReport:
    root = Path(root)
    reachable, findings = _findings_for_closure(root, entry_modules)

    # Audit the canonical router independently so an unmounted archive can
    # never hide a forbidden dependency.
    if (root / "app/api/school_rebuild_routes.py").exists():
        school_reachable, school_findings = _findings_for_closure(
            root,
            (CANONICAL_SCHOOL_ENTRY,),
        )
        reachable.update(school_reachable)
        findings.update(school_findings)

    allowlisted: set[RuntimeAuditFinding] = set()
    violations: set[RuntimeAuditFinding] = set()
    for finding in findings:
        if any(entry.matches(finding) for entry in allowlist):
            allowlisted.add(finding)
        else:
            violations.add(finding)
    return RuntimeAuditReport(
        violations=tuple(sorted(violations)),
        allowlisted=tuple(sorted(allowlisted)),
        reachable_modules=tuple(sorted(reachable)),
    )


def main() -> int:
    report = audit_school_runtime_authority(ROOT)
    for finding in report.violations:
        print(
            f"forbidden_school_runtime_{finding.kind}:"
            f"{finding.source_module}->{finding.target}"
        )
    if report.violations:
        print(
            "school_runtime_authority_failed "
            f"violations={len(report.violations)} "
            f"reachable={len(report.reachable_modules)}"
        )
        return 1
    print(
        "school_runtime_authority_ok "
        f"violations=0 allowlisted={len(report.allowlisted)} "
        f"reachable={len(report.reachable_modules)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

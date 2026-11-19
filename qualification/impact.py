"""Risk classification, case dependencies and deterministic case hashes.

This module is the single source for deciding which qualification cases are
affected by a source tree. Unknown inputs fail safe to the full gate.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import inspect
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.case_selection import CASE_BY_SLUG, CASE_SLUGS
from qualification.cases import (
    reference_implementations_for,
    supported_case_slugs,
)
from qualification.geometry_contracts import proof_contract
from qualification.native_cases import mutation_spec


TECHNICAL_CASE_SLUGS = supported_case_slugs()


RISK_ORDER = {
    "presentation": 0,
    "publication": 1,
    "derived": 2,
    "case": 3,
    "model-sensitive": 4,
    "foundational": 5,
    "toolchain": 6,
    "unknown": 7,
}

FOUNDATIONAL_MODULES = frozenset(
    {
        "scpf/scpf/compiler.py",
        "scpf/scpf/core.py",
        "scpf/scpf/headless.py",
        "scpf/scpf/model_objects.py",
        "scpf/scpf/replay.py",
        "scpf/scpf/runner.py",
    }
)

GLOBAL_CASE_INPUTS = frozenset(
    {
        "qualification/case_selection.py",
        "qualification/cases.py",
        "qualification/impact.py",
        "qualification/native_cases.py",
    }
)

PUBLICATION_PATHS = (
    "scripts/generated_output.py",
    "scripts/publish_generated.py",
    "scripts/reconcile_generated.py",
    "site/provenance.py",
    ".github/workflows/preview.yml",
    ".github/workflows/site.yml",
    ".github/workflows/preflight.yml",
)

FULL_WORKFLOW_PATHS = frozenset(
    {
        ".github/workflows/scpf.yml",
        ".github/workflows/scpf-affected.yml",
        ".github/workflows/release.yml",
    }
)

DERIVED_PATH_PREFIXES = (
    "qualification/report.py",
    "qualification/diagrams/",
    "qualification/templates/",
)

TOOLCHAIN_PATHS = frozenset(
    {
        "scpf/scpf/version.py",
        "qualification/toolchain.json",
        "scpf/pyproject.toml",
        "pyproject.toml",
    }
)


def _norm(path: str) -> str:
    value = path.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return str(PurePosixPath(value))


def _module_name(path: str) -> str:
    rel = PurePosixPath(path)
    if rel.parts[:2] != ("scpf", "scpf") or rel.suffix != ".py":
        raise ValueError(path)
    if rel.name == "__init__.py":
        return "scpf"
    return "scpf." + ".".join(rel.with_suffix("").parts[2:])


def _module_path(name: str) -> str | None:
    if name == "scpf":
        return "scpf/scpf/__init__.py"
    if not name.startswith("scpf."):
        return None
    return "scpf/scpf/" + name.removeprefix("scpf.").replace(".", "/") + ".py"


def _internal_module_graph(repo_root: Path = ROOT) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    root = repo_root / "scpf" / "scpf"
    for path in sorted(root.glob("*.py")):
        rel = str(path.relative_to(repo_root)).replace("\\", "/")
        name = _module_name(rel)
        deps: set[str] = set()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    candidate = _module_path(alias.name)
                    if candidate and (repo_root / candidate).is_file():
                        deps.add(candidate)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level:
                    base = name.split(".")[:-node.level]
                    module = ".".join(base + ([module] if module else []))
                candidate = _module_path(module)
                if candidate and (repo_root / candidate).is_file():
                    deps.add(candidate)
        graph[rel] = deps
    return graph


def _public_symbol_modules(source: Path) -> set[str]:
    if not source.is_file():
        return set()
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    modules: set[str] = set()
    scpf_module = importlib.import_module("scpf")
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == "scpf":
                for alias in node.names:
                    obj = getattr(scpf_module, alias.name, None)
                    module = inspect.getmodule(obj)
                    if module is not None:
                        candidate = _module_path(module.__name__)
                        if candidate:
                            modules.add(candidate)
            elif node.module and node.module.startswith("scpf."):
                candidate = _module_path(node.module)
                if candidate:
                    modules.add(candidate)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                candidate = _module_path(alias.name)
                if candidate:
                    modules.add(candidate)
    return modules


def case_dependencies(slug: str, repo_root: Path = ROOT) -> tuple[str, ...]:
    if slug not in CASE_BY_SLUG:
        raise KeyError(slug)
    seeds = set(FOUNDATIONAL_MODULES)
    source = repo_root / "examples" / slug / "scpf" / "model.py"
    seeds.update(_public_symbol_modules(source))
    tests = repo_root / "examples" / slug / "tests"
    if tests.is_dir():
        for test in sorted(tests.glob("test_*.py")):
            seeds.update(_public_symbol_modules(test))

    graph = _internal_module_graph(repo_root)
    stack = list(seeds)
    seen = set(seeds)
    while stack:
        current = stack.pop()
        for dep in graph.get(current, ()):
            if dep not in seen:
                seen.add(dep)
                stack.append(dep)
    return tuple(sorted(path for path in seen if (repo_root / path).is_file()))


def affected_cases(paths: tuple[str, ...] | list[str], repo_root: Path = ROOT) -> tuple[str, ...]:
    normalized = tuple(_norm(path) for path in paths)
    if any(path in GLOBAL_CASE_INPUTS for path in normalized):
        return TECHNICAL_CASE_SLUGS

    selected: set[str] = set()
    for raw in normalized:
        parts = PurePosixPath(raw).parts
        if len(parts) >= 2 and parts[0] == "examples" and parts[1] in CASE_BY_SLUG:
            selected.add(parts[1])

    changed_modules = {
        path
        for path in normalized
        if path.startswith("scpf/scpf/") and path.endswith(".py")
    }
    if changed_modules:
        dependency_map = {
            slug: set(case_dependencies(slug, repo_root))
            for slug in TECHNICAL_CASE_SLUGS
        }
        for slug, dependencies in dependency_map.items():
            if changed_modules & dependencies:
                selected.add(slug)
        unresolved = changed_modules - set().union(*dependency_map.values())
        if unresolved:
            return TECHNICAL_CASE_SLUGS

    return tuple(slug for slug in TECHNICAL_CASE_SLUGS if slug in selected)


def classify_path(path: str) -> str:
    path = _norm(path)
    if path in TOOLCHAIN_PATHS:
        return "toolchain"
    if path in FULL_WORKFLOW_PATHS:
        return "foundational"
    if path in FOUNDATIONAL_MODULES:
        return "foundational"
    if path.startswith("scpf/scpf/") and path.endswith(".py"):
        return "model-sensitive"
    if path in GLOBAL_CASE_INPUTS:
        return "foundational"
    if path.startswith("examples/"):
        parts = PurePosixPath(path).parts
        if len(parts) >= 3 and parts[2] == "scpf":
            return "model-sensitive"
        return "case"
    if path.startswith("qualification/"):
        if any(path.startswith(prefix) for prefix in DERIVED_PATH_PREFIXES):
            return "derived"
        if path.startswith("qualification/tests/"):
            return "case"
        return "model-sensitive"
    if path in PUBLICATION_PATHS or path.startswith("site/tests/"):
        return "publication"
    if path.startswith(".github/workflows/"):
        return "publication"
    if (
        path.startswith("site/")
        or path.startswith("docs/")
        or path in {"AGENTS.md", "README.md", "CHANGELOG.md"}
    ):
        return "presentation"
    return "unknown"


def classify(paths: tuple[str, ...] | list[str]) -> str:
    classes = [classify_path(path) for path in paths]
    if not classes:
        return "presentation"
    return max(classes, key=RISK_ORDER.__getitem__)


def target_stage(
    paths: tuple[str, ...] | list[str],
    cases: tuple[str, ...],
) -> str:
    """Return the highest explicit Forge stage required by changed paths."""

    risk = classify(paths)
    if risk in {"presentation", "publication", "derived"}:
        return "none"
    if risk == "case":
        return "tool_verify" if cases else "tool_qualification"
    if risk == "model-sensitive":
        return "model_verify" if cases else "tool_qualification"
    return "tool_qualification"


def _hash_file(hasher, path: Path, repo_root: Path) -> None:
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    hasher.update(rel.encode())
    hasher.update(b"\0")
    hasher.update(path.read_bytes())
    hasher.update(b"\0")


def _hash_json(hasher, label: str, value) -> None:
    hasher.update(label.encode())
    hasher.update(b"\0")
    hasher.update(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    )
    hasher.update(b"\0")


def case_input_hash(
    slug: str,
    implementation: str = "scpf",
    repo_root: Path = ROOT,
) -> str:
    if slug not in CASE_BY_SLUG:
        raise KeyError(slug)
    hasher = hashlib.sha256()

    source_dir = repo_root / "examples" / slug / implementation
    if source_dir.is_dir():
        for path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
            _hash_file(hasher, path, repo_root)

    _hash_json(hasher, "case", CASE_BY_SLUG[slug])
    _hash_json(hasher, "proof", proof_contract(slug))
    _hash_json(hasher, "mutation", mutation_spec(slug))
    _hash_json(
        hasher,
        "references",
        reference_implementations_for(CASE_BY_SLUG[slug]),
    )

    if implementation == "scpf":
        for path in case_dependencies(slug, repo_root):
            _hash_file(hasher, repo_root / path, repo_root)
        tests = repo_root / "examples" / slug / "tests"
        if tests.is_dir():
            for path in sorted(p for p in tests.rglob("*.py") if p.is_file()):
                _hash_file(hasher, path, repo_root)
    else:
        runner = repo_root / "qualification" / "reference_validation.py"
        if runner.is_file():
            _hash_file(hasher, runner, repo_root)

    toolchain = repo_root / "qualification" / "toolchain.json"
    if toolchain.is_file():
        _hash_file(hasher, toolchain, repo_root)

    return "sha256:" + hasher.hexdigest()


def changed_paths(base: str, head: str, repo_root: Path = ROOT) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", base, head, "--"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(line.strip() for line in completed.stdout.splitlines() if line.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    paths = changed_paths(args.base, args.head)
    cases = affected_cases(paths)
    risk = classify(paths)
    stage = target_stage(paths, cases)
    print("Changed paths:")
    for path in paths:
        print(f"  - {path}")
    print(f"Risk class: {risk}")
    print("Affected cases: " + (", ".join(cases) if cases else "none"))
    print(f"Target stage: {stage}")

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"risk={risk}\n")
            handle.write(f"cases={','.join(cases)}\n")
            handle.write(f"has_cases={'true' if cases else 'false'}\n")
            handle.write(f"stage={stage}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

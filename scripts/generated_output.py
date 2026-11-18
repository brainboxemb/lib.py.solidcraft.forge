#!/usr/bin/env python3
"""Build and maintain the generated-output branch layouts.

Workflows may create intermediate files in producer-oriented directories.
This module is the single place that maps those files to the persistent
item-oriented build branch and manages generated PR/stable scopes.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_BUILD_TOP_LEVEL = {"build.json", "examples", "qualification"}


def _copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _copy_tree(source: Path, target: Path) -> None:
    if not source.is_dir():
        return
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if ".git" in relative.parts:
            continue
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            _copy_file(path, destination)


def _known_case(repo_root: Path, slug: str) -> bool:
    return (repo_root / "examples" / slug).is_dir()


def _known_implementation(repo_root: Path, slug: str, implementation: str) -> bool:
    return (repo_root / "examples" / slug / implementation).is_dir()


def _copy_reference_root(
    repo_root: Path,
    reference_root: Path,
    destination: Path,
    summary_name: str,
) -> None:
    if not reference_root.is_dir():
        return

    for case_dir in sorted(reference_root.iterdir()):
        if not case_dir.is_dir() or not _known_case(repo_root, case_dir.name):
            continue
        for implementation_dir in sorted(case_dir.iterdir()):
            if not implementation_dir.is_dir():
                continue
            if not _known_implementation(
                repo_root,
                case_dir.name,
                implementation_dir.name,
            ):
                continue
            _copy_tree(
                implementation_dir,
                destination
                / "examples"
                / case_dir.name
                / implementation_dir.name,
            )

    summary = reference_root / "summary.json"
    if summary.is_file():
        _copy_file(
            summary,
            destination / "qualification" / summary_name,
        )


def assemble_build(
    output_root: Path,
    destination: Path,
    metadata: dict,
    *,
    repo_root: Path = ROOT,
) -> None:
    """Create one persistent build scope from workflow intermediate output."""
    output_root = Path(output_root)
    destination = Path(destination)
    repo_root = Path(repo_root)

    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    qualification = output_root / "qualification"
    _copy_tree(qualification, destination / "qualification")

    diagrams = output_root / "diagrams"
    _copy_tree(diagrams, destination / "qualification" / "diagrams")

    for compiled in sorted(output_root.glob("*.json")):
        slug = compiled.stem
        if not _known_case(repo_root, slug):
            continue
        _copy_file(
            compiled,
            destination / "examples" / slug / "scpf" / "solidcraft.json",
        )

    native_root = output_root / "native"
    if native_root.is_dir():
        for case_dir in sorted(native_root.iterdir()):
            if not case_dir.is_dir() or not _known_case(repo_root, case_dir.name):
                continue
            _copy_tree(
                case_dir,
                destination / "examples" / case_dir.name / "scpf",
            )

        verification = native_root / "verification.json"
        if verification.is_file():
            _copy_file(
                verification,
                destination / "qualification" / "native-verification.json",
            )

    _copy_reference_root(
        repo_root,
        output_root / "references",
        destination,
        "references-summary.json",
    )
    _copy_reference_root(
        repo_root,
        output_root / "reference-smoke",
        destination,
        "reference-smoke-summary.json",
    )

    payload = {
        "schema": 1,
        **metadata,
        "generated_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
    }
    (destination / "build.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify_build(root: Path, source_commit: str | None = None) -> dict:
    """Verify the persistent build-scope contract."""
    root = Path(root)
    metadata_file = root / "build.json"
    if not metadata_file.is_file():
        raise RuntimeError(f"missing build metadata: {metadata_file}")

    unexpected = sorted(
        path.name
        for path in root.iterdir()
        if path.name not in ALLOWED_BUILD_TOP_LEVEL
    )
    if unexpected:
        raise RuntimeError(
            "unexpected top-level build output: " + ", ".join(unexpected)
        )

    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    if metadata.get("schema") != 1:
        raise RuntimeError("unsupported build metadata schema")
    if metadata.get("scope") not in {"main", "pr"}:
        raise RuntimeError("build scope must be main or pr")
    if metadata.get("scope") == "pr" and not metadata.get("pull_request"):
        raise RuntimeError("PR build metadata must contain pull_request")
    if source_commit and metadata.get("source_commit") != source_commit:
        raise RuntimeError(
            f"build source commit {metadata.get('source_commit')} "
            f"does not match {source_commit}"
        )

    return metadata


def prepare_stable_pages(
    site: Path,
    current_pages: Path,
    destination: Path,
) -> None:
    """Replace the stable site while preserving all PR previews."""
    site = Path(site)
    current_pages = Path(current_pages)
    destination = Path(destination)

    if not (site / "provenance.json").is_file():
        raise RuntimeError("stable site is missing provenance.json")

    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    _copy_tree(site, destination)

    previews = current_pages / "previews"
    if previews.is_dir():
        preview_destination = destination / "previews"
        if preview_destination.exists():
            shutil.rmtree(preview_destination)
        _copy_tree(previews, preview_destination)


def remove_pr(root: Path, kind: str, pull_request: int) -> bool:
    """Remove only one generated PR scope."""
    root = Path(root)
    if pull_request < 1:
        raise ValueError("pull request number must be positive")

    if kind == "build":
        target = root / "pr" / str(pull_request)
    elif kind == "pages":
        target = root / "previews" / f"pr-{pull_request}"
    else:
        raise ValueError(f"unknown generated output kind: {kind}")

    if not target.exists():
        return False

    shutil.rmtree(target)
    parent = target.parent
    if parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()
    return True


def _metadata_from_args(args: argparse.Namespace) -> dict:
    if args.scope == "pr" and args.pull_request is None:
        raise SystemExit("--pull-request is required for --scope pr")
    if args.scope == "main" and args.pull_request is not None:
        raise SystemExit("--pull-request is not valid for --scope main")

    return {
        "scope": args.scope,
        "source_ref": args.source_ref,
        "source_commit": args.source_commit,
        "pull_request": args.pull_request,
        "forge_version": args.forge_version,
        "solidcraft_version": args.solidcraft_version,
        "workflow_run_id": args.workflow_run_id,
        "qualification": {
            "level": args.qualification_level,
            "status": args.qualification_status,
        },
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)

    assemble = commands.add_parser("assemble-build")
    assemble.add_argument("--output-root", type=Path, required=True)
    assemble.add_argument("--destination", type=Path, required=True)
    assemble.add_argument("--scope", choices=("main", "pr"), required=True)
    assemble.add_argument("--source-ref", required=True)
    assemble.add_argument("--source-commit", required=True)
    assemble.add_argument("--pull-request", type=int)
    assemble.add_argument("--forge-version", required=True)
    assemble.add_argument("--solidcraft-version")
    assemble.add_argument("--workflow-run-id", required=True)
    assemble.add_argument("--qualification-level", required=True)
    assemble.add_argument("--qualification-status", required=True)

    verify = commands.add_parser("verify-build")
    verify.add_argument("--root", type=Path, required=True)
    verify.add_argument("--source-commit")

    pages = commands.add_parser("prepare-stable-pages")
    pages.add_argument("--site", type=Path, required=True)
    pages.add_argument("--current-pages", type=Path, required=True)
    pages.add_argument("--destination", type=Path, required=True)

    remove = commands.add_parser("remove-pr")
    remove.add_argument("--root", type=Path, required=True)
    remove.add_argument("--kind", choices=("build", "pages"), required=True)
    remove.add_argument("--pull-request", type=int, required=True)

    return result


def main() -> int:
    args = parser().parse_args()

    if args.command == "assemble-build":
        assemble_build(
            args.output_root,
            args.destination,
            _metadata_from_args(args),
        )
        return 0
    if args.command == "verify-build":
        verify_build(args.root, args.source_commit)
        return 0
    if args.command == "prepare-stable-pages":
        prepare_stable_pages(
            args.site,
            args.current_pages,
            args.destination,
        )
        return 0
    if args.command == "remove-pr":
        remove_pr(args.root, args.kind, args.pull_request)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Assemble, validate and merge generated technical output.

Persistent build data uses schema v2 and per-case provenance. PR scopes are
sparse overlays; main is a complete baseline.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.case_selection import CASE_SLUGS
from qualification.cases import (
    reference_implementations_for,
    supported_case_slugs,
)
from qualification.case_selection import CASE_BY_SLUG
from qualification.impact import case_input_hash


SCHEMA_VERSION = 2
TECHNICAL_CASE_SLUGS = supported_case_slugs()
ALLOWED_BUILD_TOP_LEVEL = {"build.json", "examples", "qualification"}
LEVEL_RANK = {
    "preflight": 0,
    "derived": 0,
    "integration": 1,
    "native": 2,
    "full-native": 3,
    "reference": 1,
}


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


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
    return slug in CASE_SLUGS and (repo_root / "examples" / slug).is_dir()


def _selected_cases(value: str | None, output_root: Path, repo_root: Path) -> tuple[str, ...]:
    if value:
        requested = tuple(part.strip() for part in value.replace(" ", ",").split(",") if part.strip())
        unknown = sorted(set(requested) - set(TECHNICAL_CASE_SLUGS))
        if unknown:
            raise ValueError("unknown case(s): " + ", ".join(unknown))
        return tuple(slug for slug in TECHNICAL_CASE_SLUGS if slug in requested)

    detected = set()
    for path in output_root.glob("*.json"):
        if _known_case(repo_root, path.stem):
            detected.add(path.stem)
    for base in ("native", "references", "reference-smoke"):
        root = output_root / base
        if root.is_dir():
            detected.update(
                child.name
                for child in root.iterdir()
                if child.is_dir() and _known_case(repo_root, child.name)
            )
    return tuple(slug for slug in TECHNICAL_CASE_SLUGS if slug in detected)


def _copy_reference_case(
    reference_root: Path,
    destination: Path,
    slug: str,
    implementations: tuple[str, ...],
) -> None:
    for implementation in implementations:
        source = reference_root / slug / implementation
        if source.is_dir():
            _copy_tree(
                source,
                destination / "examples" / slug / implementation,
            )


def _implementation_record(
    slug: str,
    implementation: str,
    source_commit: str,
    level: str,
    generated_at: str,
    repo_root: Path,
    build_scope: str,
) -> dict:
    return {
        "source_commit": source_commit,
        "build_scope": build_scope,
        "input_hash": case_input_hash(slug, implementation, repo_root),
        "verification_level": level,
        "status": "pass",
        "generated_at": generated_at,
    }


def assemble_build(
    output_root: Path,
    destination: Path,
    metadata: dict,
    *,
    cases: tuple[str, ...] | None = None,
    repo_root: Path = ROOT,
) -> dict:
    output_root = Path(output_root)
    destination = Path(destination)
    repo_root = Path(repo_root)
    selected = cases or _selected_cases(None, output_root, repo_root)
    generated_at = _now()

    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    case_records = {}
    for slug in selected:
        implementations = {}

        compiled = output_root / f"{slug}.json"
        if compiled.is_file():
            _copy_file(
                compiled,
                destination / "examples" / slug / "scpf" / "solidcraft.json",
            )

        native = output_root / "native" / slug
        if native.is_dir():
            _copy_tree(native, destination / "examples" / slug / "scpf")

        scpf_target = destination / "examples" / slug / "scpf"
        if scpf_target.is_dir():
            implementations["scpf"] = _implementation_record(
                slug,
                "scpf",
                metadata["source_commit"],
                metadata["qualification"]["level"],
                generated_at,
                repo_root,
                (
                    "main"
                    if metadata["scope"] == "main"
                    else f"pr/{metadata['pull_request']}"
                ),
            )

        for reference_root_name in ("references", "reference-smoke"):
            reference_root = output_root / reference_root_name
            if not reference_root.is_dir():
                continue
            refs = reference_implementations_for(CASE_BY_SLUG[slug])
            _copy_reference_case(reference_root, destination, slug, refs)
            for implementation in refs:
                target = destination / "examples" / slug / implementation
                if target.is_dir():
                    implementations[implementation] = _implementation_record(
                        slug,
                        implementation,
                        metadata["source_commit"],
                        "reference",
                        generated_at,
                        repo_root,
                        (
                            "main"
                            if metadata["scope"] == "main"
                            else f"pr/{metadata['pull_request']}"
                        ),
                    )

        if implementations:
            case_records[slug] = {"implementations": implementations}

    qualification = output_root / "qualification"
    _copy_tree(qualification, destination / "qualification")

    diagrams = output_root / "diagrams"
    _copy_tree(diagrams, destination / "qualification" / "diagrams")

    native_verification = output_root / "native" / "verification.json"
    if native_verification.is_file():
        _copy_file(
            native_verification,
            destination / "qualification" / "native-verification.json",
        )

    for source_name, target_name in (
        ("references", "references-summary.json"),
        ("reference-smoke", "reference-smoke-summary.json"),
    ):
        source = output_root / source_name / "summary.json"
        if source.is_file():
            _copy_file(source, destination / "qualification" / target_name)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "scope": metadata["scope"],
        "source_ref": metadata["source_ref"],
        "source_commit": metadata["source_commit"],
        "base_commit": metadata.get("base_commit"),
        "pull_request": metadata.get("pull_request"),
        "workflow_run_id": metadata["workflow_run_id"],
        "toolchain": {
            "forge_version": metadata["forge_version"],
            "solidcraft_version": metadata.get("solidcraft_version"),
        },
        "verification": metadata["qualification"],
        "generated_at": generated_at,
        "cases": case_records,
    }
    (destination / "build.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_derived_index(destination)
    return payload


def load_manifest(root: Path) -> dict:
    path = Path(root) / "build.json"
    if not path.is_file():
        raise RuntimeError(f"missing build metadata: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeError(
            f"unsupported build metadata schema: {data.get('schema_version')}"
        )
    return data


def verify_build(
    root: Path,
    source_commit: str | None = None,
    *,
    require_complete: bool = False,
    repo_root: Path = ROOT,
) -> dict:
    root = Path(root)
    metadata = load_manifest(root)
    unexpected = sorted(
        path.name
        for path in root.iterdir()
        if path.name not in ALLOWED_BUILD_TOP_LEVEL
    )
    if unexpected:
        raise RuntimeError(
            "unexpected top-level build output: " + ", ".join(unexpected)
        )
    if metadata.get("scope") not in {"main", "pr"}:
        raise RuntimeError("build scope must be main or pr")
    if metadata["scope"] == "pr" and not metadata.get("pull_request"):
        raise RuntimeError("PR build metadata must contain pull_request")
    if source_commit and metadata.get("source_commit") != source_commit:
        raise RuntimeError(
            f"build source commit {metadata.get('source_commit')} "
            f"does not match {source_commit}"
        )

    for slug, case in metadata.get("cases", {}).items():
        if slug not in TECHNICAL_CASE_SLUGS:
            raise RuntimeError(f"unknown case in build manifest: {slug}")
        for implementation, record in case.get("implementations", {}).items():
            if not str(record.get("input_hash", "")).startswith("sha256:"):
                raise RuntimeError(
                    f"{slug}/{implementation}: missing input hash"
                )
            if record.get("status") != "pass":
                raise RuntimeError(
                    f"{slug}/{implementation}: non-passing persistent evidence"
                )
            build_scope = record.get("build_scope")
            if build_scope != "main" and not (
                isinstance(build_scope, str)
                and build_scope.startswith("pr/")
                and build_scope.removeprefix("pr/").isdigit()
            ):
                raise RuntimeError(
                    f"{slug}/{implementation}: invalid build_scope {build_scope!r}"
                )
            target = root / "examples" / slug / implementation
            if not target.is_dir():
                raise RuntimeError(
                    f"{slug}/{implementation}: manifest has no directory"
                )

    if require_complete:
        missing = sorted(set(TECHNICAL_CASE_SLUGS) - set(metadata.get("cases", {})))
        if missing:
            raise RuntimeError(
                "main build is missing registered cases: " + ", ".join(missing)
            )
    return metadata


def write_derived_index(root: Path) -> None:
    root = Path(root)
    manifest = json.loads((root / "build.json").read_text(encoding="utf-8"))
    rows = {}
    for slug, case in sorted(manifest.get("cases", {}).items()):
        levels = [
            record["verification_level"]
            for record in case.get("implementations", {}).values()
        ]
        rows[slug] = {
            "implementations": sorted(case.get("implementations", {})),
            "minimum_verification_rank": min(
                (LEVEL_RANK.get(level, -1) for level in levels),
                default=-1,
            ),
        }
    qualification = root / "qualification"
    qualification.mkdir(parents=True, exist_ok=True)
    (qualification / "evidence-index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_from_build_schema": SCHEMA_VERSION,
                "cases": rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def verify_current_hashes(root: Path, *, repo_root: Path = ROOT) -> dict:
    root = Path(root)
    manifest = verify_build(root, require_complete=True, repo_root=repo_root)
    mismatches = []
    for slug, case in manifest["cases"].items():
        for implementation, record in case.get("implementations", {}).items():
            current = case_input_hash(slug, implementation, repo_root)
            if record.get("input_hash") != current:
                mismatches.append(
                    f"{slug}/{implementation}: "
                    f"{record.get('input_hash')} != {current}"
                )
    if mismatches:
        raise RuntimeError(
            "build/main evidence no longer matches current technical inputs: "
            + "; ".join(mismatches)
        )
    return manifest


def _complete_overlay(manifest: dict) -> bool:
    return set(manifest.get("cases", {})) == set(TECHNICAL_CASE_SLUGS)


def _bootstrap_main_from_overlay(
    overlay_root: Path,
    destination: Path,
    *,
    source_commit: str,
    source_ref: str,
    workflow_run_id: str,
) -> dict:
    overlay = verify_build(overlay_root)
    if not _complete_overlay(overlay):
        raise RuntimeError(
            "legacy main can only be replaced from a complete verified overlay"
        )
    if destination.exists():
        shutil.rmtree(destination)
    _copy_tree(overlay_root, destination)
    merged = load_manifest(destination)
    merged["scope"] = "main"
    merged["source_ref"] = source_ref
    merged["source_commit"] = source_commit
    merged["pull_request"] = None
    merged["workflow_run_id"] = workflow_run_id
    merged["generated_at"] = _now()
    for case in merged["cases"].values():
        for record in case.get("implementations", {}).values():
            record["build_scope"] = "main"
    (destination / "build.json").write_text(
        json.dumps(merged, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_derived_index(destination)
    verify_build(destination, source_commit, require_complete=True)
    return merged


def promote_overlay(
    main_root: Path,
    overlay_root: Path,
    destination: Path,
    *,
    required_level: str,
    source_commit: str,
    source_ref: str = "main",
    workflow_run_id: str = "",
    repo_root: Path = ROOT,
) -> dict:
    main_root = Path(main_root)
    overlay_root = Path(overlay_root)
    destination = Path(destination)
    overlay_manifest = verify_build(overlay_root, repo_root=repo_root)
    try:
        main_manifest = verify_build(
            main_root,
            require_complete=True,
            repo_root=repo_root,
        )
    except RuntimeError:
        if (
            LEVEL_RANK.get(required_level, -1)
            >= LEVEL_RANK["full-native"]
            and _complete_overlay(overlay_manifest)
        ):
            return _bootstrap_main_from_overlay(
                overlay_root,
                destination,
                source_commit=source_commit,
                source_ref=source_ref,
                workflow_run_id=workflow_run_id,
            )
        raise
    if overlay_manifest["scope"] not in {"pr", "main"}:
        raise RuntimeError("promotion requires a PR or main candidate")
    if (
        overlay_manifest["scope"] == "main"
        and overlay_manifest.get("source_commit") != source_commit
    ):
        raise RuntimeError("main candidate source commit does not match promotion target")

    required_rank = LEVEL_RANK[required_level]
    for slug, case in overlay_manifest["cases"].items():
        for implementation, record in case["implementations"].items():
            if implementation == "scpf":
                level = record["verification_level"]
                if LEVEL_RANK.get(level, -1) < required_rank:
                    raise RuntimeError(
                        f"{slug}: {level} is below required {required_level}"
                    )

    if destination.exists():
        shutil.rmtree(destination)
    _copy_tree(main_root, destination)

    merged = json.loads(json.dumps(main_manifest))
    merged["scope"] = "main"
    merged["source_ref"] = source_ref
    merged["source_commit"] = source_commit
    merged["pull_request"] = None
    merged["workflow_run_id"] = workflow_run_id
    merged["generated_at"] = _now()

    current_cases = set(TECHNICAL_CASE_SLUGS)
    examples_root = destination / "examples"
    if examples_root.is_dir():
        for path in list(examples_root.iterdir()):
            if path.is_dir() and path.name not in current_cases:
                shutil.rmtree(path)
                merged["cases"].pop(path.name, None)

    for slug, case in overlay_manifest["cases"].items():
        for implementation, record in case["implementations"].items():
            source = overlay_root / "examples" / slug / implementation
            target = destination / "examples" / slug / implementation
            if target.exists():
                shutil.rmtree(target)
            _copy_tree(source, target)
            promoted_record = json.loads(json.dumps(record))
            promoted_record["build_scope"] = "main"
            merged.setdefault("cases", {}).setdefault(
                slug, {"implementations": {}}
            )["implementations"][implementation] = promoted_record

    overlay_diagrams = overlay_root / "qualification" / "diagrams"
    if overlay_diagrams.is_dir():
        target_diagrams = destination / "qualification" / "diagrams"
        if target_diagrams.exists():
            shutil.rmtree(target_diagrams)
        _copy_tree(overlay_diagrams, target_diagrams)

    merged["verification"] = {"level": "per-case", "status": "pass"}

    (destination / "build.json").write_text(
        json.dumps(merged, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_derived_index(destination)
    verify_build(destination, source_commit, require_complete=True, repo_root=repo_root)
    return merged


def resolve_preview(
    main_root: Path,
    overlay_root: Path | None,
    destination: Path,
) -> dict:
    if overlay_root is not None:
        overlay = verify_build(overlay_root)
        if _complete_overlay(overlay):
            if destination.exists():
                shutil.rmtree(destination)
            _copy_tree(overlay_root, destination)
            return load_manifest(destination)
    return resolve_overlay(main_root, overlay_root, destination)


def resolve_overlay(main_root: Path, overlay_root: Path | None, destination: Path) -> dict:
    main_root = Path(main_root)
    destination = Path(destination)
    verify_build(main_root, require_complete=True)
    if destination.exists():
        shutil.rmtree(destination)
    _copy_tree(main_root, destination)
    if overlay_root is None:
        return load_manifest(destination)

    overlay_root = Path(overlay_root)
    overlay = verify_build(overlay_root)
    for slug, case in overlay.get("cases", {}).items():
        for implementation in case.get("implementations", {}):
            source = overlay_root / "examples" / slug / implementation
            target = destination / "examples" / slug / implementation
            if target.exists():
                shutil.rmtree(target)
            _copy_tree(source, target)

    overlay_diagrams = overlay_root / "qualification" / "diagrams"
    if overlay_diagrams.is_dir():
        target_diagrams = destination / "qualification" / "diagrams"
        if target_diagrams.exists():
            shutil.rmtree(target_diagrams)
        _copy_tree(overlay_diagrams, target_diagrams)

    resolved = load_manifest(destination)
    for slug, case in overlay.get("cases", {}).items():
        resolved.setdefault("cases", {}).setdefault(
            slug, {"implementations": {}}
        )["implementations"].update(case.get("implementations", {}))
    resolved["overlay"] = {
        "scope": overlay["scope"],
        "source_commit": overlay["source_commit"],
        "pull_request": overlay.get("pull_request"),
    }
    (destination / "build.json").write_text(
        json.dumps(resolved, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_derived_index(destination)
    return resolved


def materialize_site_evidence(build_root: Path, destination: Path) -> None:
    """Create the legacy local site-evidence view from normalized build data.

    The site consumes this local view while all emitted technical URLs still
    point at the immutable build commit.
    """
    build_root = Path(build_root)
    destination = Path(destination)
    verify_build(build_root)
    if destination.exists():
        shutil.rmtree(destination)
    native = destination / "native"
    references = destination / "references"
    diagrams = destination / "diagrams"
    native.mkdir(parents=True)
    references.mkdir(parents=True)

    manifest = load_manifest(build_root)
    for slug, case in manifest.get("cases", {}).items():
        for implementation in case.get("implementations", {}):
            source = build_root / "examples" / slug / implementation
            if implementation == "scpf":
                _copy_tree(source, native / slug)
            else:
                _copy_tree(source, references / slug / implementation)

    qualification = build_root / "qualification"
    diagrams_source = qualification / "diagrams"
    if diagrams_source.is_dir():
        _copy_tree(diagrams_source, diagrams)

    refs = qualification / "references-summary.json"
    if refs.is_file():
        _copy_file(refs, references / "summary.json")


def prepare_stable_pages(site: Path, current_pages: Path, destination: Path) -> None:
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
        _copy_tree(previews, destination / "previews")


def remove_pr(root: Path, kind: str, pull_request: int) -> bool:
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
    return {
        "scope": args.scope,
        "source_ref": args.source_ref,
        "source_commit": args.source_commit,
        "pull_request": args.pull_request,
        "base_commit": args.base_commit,
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
    assemble.add_argument("--base-commit")
    assemble.add_argument("--forge-version", required=True)
    assemble.add_argument("--solidcraft-version")
    assemble.add_argument("--workflow-run-id", required=True)
    assemble.add_argument("--qualification-level", required=True)
    assemble.add_argument("--qualification-status", required=True)
    assemble.add_argument("--cases")

    verify = commands.add_parser("verify-build")
    verify.add_argument("--root", type=Path, required=True)
    verify.add_argument("--source-commit")
    verify.add_argument("--require-complete", action="store_true")

    promote = commands.add_parser("promote-overlay")
    promote.add_argument("--main", type=Path, required=True)
    promote.add_argument("--overlay", type=Path, required=True)
    promote.add_argument("--destination", type=Path, required=True)
    promote.add_argument("--required-level", required=True)
    promote.add_argument("--source-commit", required=True)
    promote.add_argument("--workflow-run-id", default="")

    resolve = commands.add_parser("resolve-overlay")
    resolve.add_argument("--main", type=Path, required=True)
    resolve.add_argument("--overlay", type=Path)
    resolve.add_argument("--destination", type=Path, required=True)

    preview = commands.add_parser("resolve-preview")
    preview.add_argument("--main", type=Path, required=True)
    preview.add_argument("--overlay", type=Path)
    preview.add_argument("--destination", type=Path, required=True)

    reusable = commands.add_parser("verify-current-hashes")
    reusable.add_argument("--root", type=Path, required=True)

    materialize = commands.add_parser("materialize-site-evidence")
    materialize.add_argument("--build-root", type=Path, required=True)
    materialize.add_argument("--destination", type=Path, required=True)

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
        cases = _selected_cases(args.cases, args.output_root, ROOT)
        assemble_build(
            args.output_root,
            args.destination,
            _metadata_from_args(args),
            cases=cases,
        )
        return 0
    if args.command == "verify-build":
        verify_build(
            args.root,
            args.source_commit,
            require_complete=args.require_complete,
        )
        return 0
    if args.command == "promote-overlay":
        promote_overlay(
            args.main,
            args.overlay,
            args.destination,
            required_level=args.required_level,
            source_commit=args.source_commit,
            workflow_run_id=args.workflow_run_id,
        )
        return 0
    if args.command == "resolve-overlay":
        resolve_overlay(args.main, args.overlay, args.destination)
        return 0
    if args.command == "resolve-preview":
        resolve_preview(args.main, args.overlay, args.destination)
        return 0
    if args.command == "verify-current-hashes":
        verify_current_hashes(args.root)
        return 0
    if args.command == "materialize-site-evidence":
        materialize_site_evidence(args.build_root, args.destination)
        return 0
    if args.command == "prepare-stable-pages":
        prepare_stable_pages(args.site, args.current_pages, args.destination)
        return 0
    if args.command == "remove-pr":
        remove_pr(args.root, args.kind, args.pull_request)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())

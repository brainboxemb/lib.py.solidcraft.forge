#!/usr/bin/env python3
"""Publish Forge build output and Pages with the pinned generic CI tool.

Forge owns gate policy, qualification meaning, site content and CSS. This module
only translates completed Forge items into tool.cad.ci build-store operations
and renders the site from the resolved generic view.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SITE = "https://brainboxemb.github.io/lib.py.solidcraft.forge"


def read_json(path: Path) -> object:
    """Read one required JSON file."""

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"missing publication input: {path}") from exc


def tool_path(source_root: Path = ROOT) -> Path:
    """Return the exact pinned tool entry point bootstrapped by the workflow."""

    path = source_root / "ext" / "cad-ci" / "cad-ci.py"
    if not path.is_file():
        raise RuntimeError(
            "missing ext/cad-ci/cad-ci.py; run scripts/bootstrap_cad_ci.py first"
        )
    return path


def run_tool(*args: str, capture: bool = False) -> str:
    """Run one pinned generic publication command."""

    command = [sys.executable, str(tool_path()), *args]
    if capture:
        return subprocess.check_output(
            command,
            cwd=ROOT,
            text=True,
        ).strip()
    subprocess.run(command, cwd=ROOT, check=True)
    return ""


def python(*args: str) -> None:
    """Run one Forge-owned site/provenance command."""

    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def plan_rows(path: Path) -> tuple[dict, ...]:
    """Return the exact generic items considered by the Forge pipeline."""

    data = read_json(path)
    if not isinstance(data, list):
        raise RuntimeError("tool-cad-ci-plan.json must contain a list")
    result: list[dict] = []
    for row in data:
        if not isinstance(row, dict):
            raise RuntimeError("tool-cad-ci-plan.json contains a non-object row")
        if not isinstance(row.get("id"), str) or not isinstance(row.get("path"), str):
            raise RuntimeError("generic plan row is missing id/path")
        result.append(row)
    return tuple(result)


def completed_items(plan: tuple[dict, ...], candidate_root: Path) -> tuple[str, ...]:
    """Return planned item IDs whose final generic item state is passing.

    Integration-only example runs deliberately have no item.json. They remain
    transient PR diagnostics and are not inserted into the durable build store.
    """

    result: list[str] = []
    for row in plan:
        state_path = candidate_root / row["path"] / "item.json"
        if not state_path.is_file():
            continue
        state = read_json(state_path)
        if not isinstance(state, dict) or state.get("status") != "pass":
            continue
        item_id = row["id"]
        if item_id not in result:
            result.append(item_id)
    return tuple(result)


def generic_main_available(build_root: Path) -> bool:
    """Return whether the checked-out build branch already has schema-1 main."""

    path = build_root / "main" / "build.json"
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return data.get("schema") == 1 and data.get("scope") == "main"


def tool_common(source_ref: str, source_sha: str) -> list[str]:
    """Return source-freshness arguments for generated-branch publication."""

    return [
        "--repo",
        str(ROOT),
        "--source-ref",
        source_ref,
        "--expected-source",
        source_sha,
    ]


def build_site(
    *,
    generic_root: Path,
    work: Path,
    source_sha: str,
    source_ref: str,
    workflow_run_id: str,
    build_commit: str,
    pull_request: int | None,
    overlay_items: tuple[str, ...],
    mask_cases: tuple[str, ...],
    stable: bool,
) -> Path:
    """Render and test Forge Pages from one complete generic build view."""

    evidence = work / "site-evidence"
    site = work / "site"
    if site.exists():
        shutil.rmtree(site)

    python(
        "scripts/generic_site.py",
        "--generic-root",
        str(generic_root),
        "--out",
        str(evidence),
        *(
            ["--pull-request", str(pull_request)]
            if pull_request is not None
            else []
        ),
        *(
            ["--overlay-items", *overlay_items]
            if overlay_items
            else []
        ),
        *(
            ["--mask-cases", *mask_cases]
            if mask_cases
            else []
        ),
    )

    manifest = evidence / "build.json"
    data = read_json(manifest)
    assert isinstance(data, dict)
    evidence_sha = str(data.get("source_commit") or source_sha)

    python(
        "site/build.py",
        "--out",
        str(site),
        "--source-sha",
        source_sha,
        "--native",
        str(evidence / "native"),
        "--references",
        str(evidence / "references"),
        "--diagram-root",
        str(evidence / "diagrams"),
        "--build-manifest",
        str(manifest),
        "--build-commit",
        build_commit,
        "--build-scope",
        "main",
    )

    test_args = [
        "site/test_site.py",
        str(site),
        source_sha,
        f"--evidence-sha={evidence_sha}",
        f"--build-commit={build_commit}",
    ]
    if stable:
        test_args += ["--require-native", "--require-references"]
    python(*test_args)

    provenance = [
        "site/provenance.py",
        "write-build",
        "--out",
        str(site / "provenance.json"),
        "--stage",
        "stable" if stable else "preview",
        "--source-ref",
        source_ref,
        "--source-commit",
        source_sha,
        "--build-commit",
        build_commit,
        "--build-manifest",
        str(manifest),
        "--workflow-run-id",
        workflow_run_id,
    ]
    if pull_request is not None:
        provenance += ["--pull-request", str(pull_request)]
    python(*provenance)
    return site


def execute(
    *,
    source_sha: str,
    source_ref: str,
    operation: str,
    pull_request: int,
    gate: str,
    cases: str,
    workflow_run_id: str,
    generated_build: Path,
    output_root: Path,
    publish: bool,
) -> str | None:
    """Publish the current Forge run through the generic build/Page stores."""

    plan = plan_rows(output_root / "tool-cad-ci-plan.json")
    candidate_root = ROOT / "build"
    complete_ids = completed_items(plan, candidate_root)
    has_main = generic_main_available(generated_build)

    work = output_root / "generic-publication"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    if operation == "pr":
        if pull_request < 1:
            raise ValueError("PR publication requires a positive pull request")
        if not has_main:
            # The cutover PR itself still sees the previous schema-2 build
            # branch. Its main push is deliberately forced through a full gate,
            # which creates the first complete generic baseline.
            print("Generic build/main is not available yet; PR publication deferred.")
            return None

        overlay: Path | None = None
        if complete_ids:
            overlay = work / "pr"
            run_tool(
                "build",
                "prepare-pr",
                "--repo",
                str(ROOT),
                "--candidate-root",
                str(candidate_root),
                "--out",
                str(overlay),
                "--source-commit",
                source_sha,
                "--pull-request",
                str(pull_request),
                "--items",
                *complete_ids,
            )
            if publish:
                build_commit = run_tool(
                    "publish",
                    "build",
                    *tool_common(source_ref, source_sha),
                    "--candidate",
                    str(overlay),
                    "--scope",
                    "pr",
                    "--pull-request",
                    str(pull_request),
                    "--message",
                    f"Publish Forge build PR #{pull_request} at {source_sha}",
                    capture=True,
                )
            else:
                build_commit = "build"
        else:
            if publish:
                # Do not let an earlier native overlay survive after a new
                # integration-only commit on the same pull request.
                build_commit = run_tool(
                    "publish",
                    "build-cleanup",
                    *tool_common(source_ref, source_sha),
                    "--pull-request",
                    str(pull_request),
                    "--message",
                    f"Clear Forge build PR #{pull_request} at {source_sha}",
                    capture=True,
                )
            else:
                build_commit = "build"

        resolved = work / "resolved"
        if overlay is None:
            shutil.copytree(generated_build / "main", resolved)
        else:
            run_tool(
                "build",
                "resolve",
                "--main",
                str(generated_build / "main"),
                "--overlay",
                str(overlay),
                "--out",
                str(resolved),
            )

        selected_cases = tuple(
            value.strip()
            for value in cases.split(",")
            if value.strip()
        )
        native_gate = gate in {"affected-q1-q6", "full-q1-q6"}
        masked = () if native_gate else selected_cases

        site = build_site(
            generic_root=resolved,
            work=work,
            source_sha=source_sha,
            source_ref=source_ref,
            workflow_run_id=workflow_run_id,
            build_commit=build_commit or "build",
            pull_request=pull_request,
            overlay_items=complete_ids,
            mask_cases=masked,
            stable=False,
        )
        if publish:
            run_tool(
                "publish",
                "pages",
                *tool_common(source_ref, source_sha),
                "--site",
                str(site),
                "--pull-request",
                str(pull_request),
                "--message",
                f"Publish Forge preview PR #{pull_request} at {source_sha}",
            )
        return None

    if operation != "main":
        raise ValueError(f"unsupported publication operation: {operation}")

    if has_main:
        if complete_ids:
            complete = work / "main"
            run_tool(
                "build",
                "update-main",
                "--repo",
                str(ROOT),
                "--main",
                str(generated_build / "main"),
                "--candidate-root",
                str(candidate_root),
                "--out",
                str(complete),
                "--source-commit",
                source_sha,
                "--items",
                *complete_ids,
            )
            publish_main = True
        else:
            complete = generated_build / "main"
            publish_main = False
    else:
        if gate != "full-q1-q6":
            raise RuntimeError(
                "first generic build/main publication requires a full native gate"
            )
        complete = work / "main"
        run_tool(
            "build",
            "prepare-main",
            "--repo",
            str(ROOT),
            "--candidate-root",
            str(candidate_root),
            "--out",
            str(complete),
            "--source-commit",
            source_sha,
        )
        publish_main = True

    if publish and publish_main:
        build_commit = run_tool(
            "publish",
            "build",
            *tool_common("main", source_sha),
            "--candidate",
            str(complete),
            "--scope",
            "main",
            "--message",
            f"Publish Forge build/main at {source_sha}",
            capture=True,
        )
    else:
        build_commit = "build"

    site = build_site(
        generic_root=complete,
        work=work,
        source_sha=source_sha,
        source_ref="main",
        workflow_run_id=workflow_run_id,
        build_commit=build_commit or "build",
        pull_request=None,
        overlay_items=(),
        mask_cases=(),
        stable=True,
    )
    if publish:
        run_tool(
            "publish",
            "pages",
            *tool_common("main", source_sha),
            "--site",
            str(site),
            "--message",
            f"Publish stable Forge site at {source_sha}",
        )
    return build_commit or None


def cleanup_build(pull_request: int) -> None:
    """Remove one PR build overlay through the generic publisher."""

    run_tool(
        "publish",
        "build-cleanup",
        "--repo",
        str(ROOT),
        "--pull-request",
        str(pull_request),
        "--message",
        f"Remove Forge build PR #{pull_request}",
    )


def cleanup_pages(pull_request: int) -> None:
    """Remove one PR Pages preview through the generic publisher."""

    run_tool(
        "publish",
        "pages-cleanup",
        "--repo",
        str(ROOT),
        "--pull-request",
        str(pull_request),
        "--message",
        f"Remove Forge preview PR #{pull_request}",
    )


def cleanup(pull_request: int) -> None:
    """Remove one PR build overlay and Pages preview through the generic tool."""

    cleanup_build(pull_request)
    cleanup_pages(pull_request)

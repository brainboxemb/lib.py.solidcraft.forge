#!/usr/bin/env python3
"""Run the Forge verification/publication pipeline outside GitHub Actions.

GitHub Actions should decide *when* to run this script and provide repository
credentials. This module owns *what* Forge does: preflight, qualification,
preview/stable publication and generated-output promotion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import publish_generated
from qualification.cases import supported_case_slugs


def run(args: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    subprocess.run(args, cwd=cwd, env=merged, check=True)


def output(args: list[str], *, cwd: Path = ROOT) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def python(*args: str, env: dict[str, str] | None = None) -> None:
    run([sys.executable, *args], env=env)


def docker_python(image: str, *args: str, extra_mounts: tuple[tuple[Path, str], ...] = ()) -> None:
    command = [
        "docker", "run", "--rm",
        "-v", f"{ROOT}:/workspace",
        "-w", "/workspace",
        "-e", "PYTHONPATH=/workspace/scpf:/workspace",
    ]
    for host, target in extra_mounts:
        command += ["-v", f"{host}:{target}"]
    command += [image, "python", *args]
    run(command)


def tool_cad_ci_path() -> Path:
    """Return the pinned external CI tool bootstrapped by the workflow."""

    path = ROOT / "ext" / "cad-ci" / "cad-ci.py"
    if not path.is_file():
        raise RuntimeError(
            "missing ext/cad-ci/cad-ci.py; run scripts/bootstrap_cad_ci.py first"
        )
    return path


def tool_cad_ci_env() -> dict[str, str]:
    """Provide Forge and repository imports to commands run from item folders."""

    parts = [str(ROOT / "scpf"), str(ROOT)]
    current = os.environ.get("PYTHONPATH", "")
    if current:
        parts.append(current)
    return {"PYTHONPATH": os.pathsep.join(parts)}


def selected_tool_cases(stage: str, cases: str) -> tuple[str, ...]:
    """Return concrete example items selected for this Forge stage."""

    supported = supported_case_slugs()
    if stage == "tool_qualification":
        return tuple(supported)

    requested = {
        value.strip()
        for value in cases.split(",")
        if value.strip()
    }
    return tuple(slug for slug in supported if slug in requested)


def evidence_items(
    verify_references: bool,
    verify_diagrams: bool,
) -> tuple[str, ...]:
    """Return shared evidence items selected explicitly by Forge."""

    result: list[str] = []
    if verify_references:
        result.append("reference-suite")
    if verify_diagrams:
        result.append("qualification-diagrams")
    return tuple(result)


def has_build_output(args: argparse.Namespace) -> bool:
    """Return whether this run produces a technical build overlay."""

    return (
        args.stage in {"model_verify", "tool_qualification"}
        or args.verify_references
        or args.verify_diagrams
    )


def run_tool_cad_ci_layers(
    out: Path,
    stage: str,
    cases: str,
    verify_references: bool,
    verify_diagrams: bool,
) -> None:
    """Run Forge build/test and selected example tool verification.

    The generic CI runner receives only concrete item names and a concrete step
    boundary. Forge owns the meaning of tool_build, tool_test and tool_verify.
    """

    tool = tool_cad_ci_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    selected = selected_tool_cases(stage, cases)
    rows: list[dict] = []
    seen: set[str] = set()

    items = (
        *(("forge-tool",) if stage != "none" else ()),
        *selected,
        *evidence_items(verify_references, verify_diagrams),
    )
    for item in items:
        plan = json.loads(
            subprocess.check_output(
                [
                    sys.executable,
                    str(tool),
                    "plan",
                    "--repo",
                    str(ROOT),
                    "--item",
                    item,
                    "--json",
                ],
                cwd=ROOT,
                env={**os.environ, **tool_cad_ci_env()},
                text=True,
            )
        )
        for row in plan:
            item_id = row.get("id")
            if isinstance(item_id, str) and item_id not in seen:
                seen.add(item_id)
                rows.append(row)

    if stage != "none":
        run(
            [
                sys.executable,
                str(tool),
                "run",
                "--repo",
                str(ROOT),
                "--item",
                "forge-tool",
            ],
            env=tool_cad_ci_env(),
        )
        for slug in selected:
            run(
                [
                    sys.executable,
                    str(tool),
                    "run",
                    "--repo",
                    str(ROOT),
                    "--item",
                    slug,
                    "--until",
                    "tool_verify",
                ],
                env=tool_cad_ci_env(),
            )

    out.write_text(
        json.dumps(rows, indent=2) + "\n",
        encoding="utf-8",
    )

def run_model_verify(item: str, image: str) -> None:
    """Run one Forge-owned model verification step in SolidCraft."""

    if not image:
        raise ValueError(f"{item} requires the qualification image")

    env = tool_cad_ci_env()
    env["FORGE_QUALIFICATION_IMAGE"] = image
    run(
        [
            sys.executable,
            str(tool_cad_ci_path()),
            "run",
            "--repo",
            str(ROOT),
            "--item",
            item,
            "--from",
            "model_verify",
        ],
        env=env,
    )


def run_tool_qualification(image: str) -> None:
    """Run the aggregate Forge qualification after all required model checks."""

    if not image:
        raise ValueError("tool_qualification requires the SolidCraft image")
    env = tool_cad_ci_env()
    env["FORGE_QUALIFICATION_IMAGE"] = image
    run(
        [
            sys.executable,
            str(tool_cad_ci_path()),
            "run",
            "--repo",
            str(ROOT),
            "--item",
            "tool-qualification",
        ],
        env=env,
    )


def run_tool_cad_ci_evidence(item: str, image: str) -> None:
    """Run one Forge-owned generated-evidence item in the selected image."""

    if not image:
        raise ValueError(f"{item} requires the qualification image")
    env = tool_cad_ci_env()
    env["FORGE_QUALIFICATION_IMAGE"] = image
    run(
        [
            sys.executable,
            str(tool_cad_ci_path()),
            "run",
            "--repo",
            str(ROOT),
            "--item",
            item,
        ],
        env=env,
    )


def preflight(source_sha: str, out: Path) -> None:
    """Run the existing cheap Forge preflight checks."""

    python("scripts/ci_preflight.py", "--source-sha", source_sha, "--site-out", str(out))


def smoke_image(image: str, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    docker_python(
        image,
        "qualification/case_runner.py",
        "simple-box",
        "--out",
        "/case-out",
        extra_mounts=((out, "/case-out"),),
    )

    replay = out / "stages" / "simple-box" / "02-replay.json"
    mutate = out / "stages" / "simple-box" / "06-mutate.json"
    replay_before = hashlib.sha256(replay.read_bytes()).hexdigest()
    mutate_before = hashlib.sha256(mutate.read_bytes()).hexdigest()

    docker_python(
        image,
        "qualification/case_runner.py",
        "simple-box",
        "--out",
        "/case-out",
        "--stage",
        "mutate",
        extra_mounts=((out, "/case-out"),),
    )

    replay_after = hashlib.sha256(replay.read_bytes()).hexdigest()
    mutate_after = hashlib.sha256(mutate.read_bytes()).hexdigest()
    if replay_before != replay_after:
        raise RuntimeError("mutate stage unexpectedly changed replay evidence")
    if mutate_before == mutate_after:
        raise RuntimeError("mutate stage did not refresh mutate evidence")
    state = json.loads(mutate.read_text(encoding="utf-8"))
    if state.get("status") != "pass":
        raise RuntimeError("simple-box mutate stage did not pass")


def verify_contracts(image: str, solidcraft_version: str, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    script = f"""
set -euo pipefail
python scripts/solidcraft_snapshot.py \
  --out /snapshot \
  --version {solidcraft_version!r} \
  --source-ref {('v' + solidcraft_version)!r}
diff -ru docs/vendor/solidcraft/{solidcraft_version}/runtime /snapshot
python scripts/solidcraft_snapshot.py \
  --check-pinned docs/vendor/solidcraft/{solidcraft_version}/runtime
"""
    run([
        "docker", "run", "--rm",
        "-v", f"{ROOT}:/workspace",
        "-v", f"{out}:/snapshot",
        "-w", "/workspace",
        "-e", "PYTHONPATH=/workspace/scpf:/workspace",
        image,
        "bash", "-lc", script,
    ])


def item_gate_args(args: argparse.Namespace) -> list[str]:
    """Build arguments for the transitional publication adapter."""

    command = [
        "qualification/item_gate.py",
        "--stage", args.stage,
        "--cases", args.cases,
        "--out", str(args.output_root / "gate"),
        "--build-out", str(args.output_root / "build"),
        "--source-sha", args.source_sha,
        "--scope", args.operation,
        "--source-ref", args.source_ref,
        "--workflow-run-id", args.workflow_run_id,
    ]
    if args.verify_references:
        command.append("--verify-references")
    if args.verify_diagrams:
        command.append("--verify-diagrams")
    if args.base_sha:
        command += ["--base-commit", args.base_sha]
    if args.operation == "pr":
        command += ["--pull-request", str(args.pull_request)]
    return command


def qualify(args: argparse.Namespace) -> None:
    """Run selected model verification and the optional aggregate qualification."""

    selected = selected_tool_cases(args.stage, args.cases)

    if args.stage == "model_verify":
        for slug in selected:
            run_model_verify(slug, args.image)
    elif args.stage == "tool_qualification":
        run_tool_qualification(args.image)

    for item in evidence_items(args.verify_references, args.verify_diagrams):
        run_tool_cad_ci_evidence(item, args.image)

    if has_build_output(args):
        # The publication adapter only translates completed generic item output.
        # It performs no additional model verification.
        python(*item_gate_args(args))


def publish_pr_candidate(args: argparse.Namespace) -> str:
    destination = f"pr/{args.pull_request}"
    if not has_build_output(args):
        if args.publish:
            publish_generated.publish(
                branch="build",
                operation="remove-dir",
                destination=destination,
                message=f"Remove obsolete build PR #{args.pull_request}",
            )
        return output(["git", "-C", str(args.generated_build), "rev-parse", "HEAD"])

    if not args.publish:
        return output(["git", "-C", str(args.generated_build), "rev-parse", "HEAD"])

    return publish_generated.publish(
        branch="build",
        operation="replace-dir",
        source=args.output_root / "build",
        destination=destination,
        source_ref=args.source_ref,
        expected_source=args.source_sha,
        repository=args.repository,
        pull_request=args.pull_request,
        message=f"Publish build PR #{args.pull_request}",
    )


def resolve_preview(args: argparse.Namespace, build_commit: str) -> None:
    resolved = args.output_root / "resolved"
    evidence = args.output_root / "evidence"
    site = args.output_root / "site"
    command = [
        "scripts/generated_output.py", "resolve-preview",
        "--main", str(args.generated_build / "main"),
        "--destination", str(resolved),
    ]
    if has_build_output(args):
        command += ["--overlay", str(args.output_root / "build")]
    python(*command)
    python(
        "scripts/generated_output.py", "materialize-site-evidence",
        "--build-root", str(resolved),
        "--destination", str(evidence),
    )

    manifest = resolved / "build.json"
    evidence_sha = json.loads(manifest.read_text(encoding="utf-8"))["source_commit"]
    python(
        "site/build.py",
        "--out", str(site),
        "--source-sha", args.source_sha,
        "--model-verify", str(evidence / "model_verify"),
        "--references", str(evidence / "references"),
        "--diagram-root", str(evidence / "diagrams"),
        "--build-manifest", str(manifest),
        "--build-commit", build_commit,
        "--build-scope", "main",
    )
    python(
        "site/test_site.py",
        str(site), args.source_sha,
        f"--evidence-sha={evidence_sha}",
        f"--build-commit={build_commit}",
    )
    python(
        "site/provenance.py", "write-build",
        "--out", str(site / "provenance.json"),
        "--stage", "preview",
        "--source-ref", args.source_ref,
        "--source-commit", args.source_sha,
        "--pull-request", str(args.pull_request),
        "--build-commit", build_commit,
        "--build-manifest", str(manifest),
        "--workflow-run-id", args.workflow_run_id,
    )

    if args.publish:
        publish_generated.publish(
            branch="gh-pages",
            operation="replace-dir",
            source=site,
            destination=f"previews/pr-{args.pull_request}",
            source_ref=args.source_ref,
            expected_source=args.source_sha,
            repository=args.repository,
            pull_request=args.pull_request,
            message=f"Publish preview PR #{args.pull_request}",
        )


def stable_build(args: argparse.Namespace) -> tuple[Path, str, str]:
    if not has_build_output(args):
        root = args.generated_build / "main"
        python("scripts/generated_output.py", "verify-build", "--root", str(root), "--require-complete")
        build_commit = output(["git", "-C", str(args.generated_build), "rev-parse", "HEAD"])
    else:
        root = args.output_root / "main"
        python(
            "scripts/generated_output.py", "promote-overlay",
            "--main", str(args.generated_build / "main"),
            "--overlay", str(args.output_root / "build"),
            "--destination", str(root),
            "--required-level", args.stage,
            "--source-commit", args.source_sha,
            "--workflow-run-id", args.workflow_run_id,
        )
        python(
            "scripts/generated_output.py", "verify-build",
            "--root", str(root),
            "--source-commit", args.source_sha,
            "--require-complete",
        )
        if args.publish:
            build_commit = publish_generated.publish(
                branch="build",
                operation="replace-dir",
                source=root,
                destination="main",
                source_ref="main",
                expected_source=args.source_sha,
                message=f"Publish build/main at {args.source_sha}",
            )
        else:
            build_commit = output(["git", "-C", str(args.generated_build), "rev-parse", "HEAD"])

    manifest = root / "build.json"
    evidence_sha = json.loads(manifest.read_text(encoding="utf-8"))["source_commit"]
    return root, build_commit, evidence_sha


def build_stable_site(args: argparse.Namespace, root: Path, build_commit: str, evidence_sha: str) -> None:
    evidence = args.output_root / "evidence"
    site = args.output_root / "site"
    python(
        "scripts/generated_output.py", "materialize-site-evidence",
        "--build-root", str(root),
        "--destination", str(evidence),
    )
    manifest = root / "build.json"
    python(
        "site/build.py",
        "--out", str(site),
        "--source-sha", args.source_sha,
        "--model-verify", str(evidence / "model_verify"),
        "--references", str(evidence / "references"),
        "--diagram-root", str(evidence / "diagrams"),
        "--build-manifest", str(manifest),
        "--build-commit", build_commit,
        "--build-scope", "main",
    )
    python(
        "site/test_site.py",
        str(site), args.source_sha,
        f"--evidence-sha={evidence_sha}",
        f"--build-commit={build_commit}",
        "--require-model-verify",
        "--require-references",
    )
    python(
        "site/provenance.py", "write-build",
        "--out", str(site / "provenance.json"),
        "--stage", "stable",
        "--source-ref", "main",
        "--source-commit", args.source_sha,
        "--build-commit", build_commit,
        "--build-manifest", str(manifest),
        "--workflow-run-id", args.workflow_run_id,
    )
    if args.publish:
        publish_generated.publish(
            branch="gh-pages",
            operation="replace-stable-pages",
            source=site,
            source_ref="main",
            expected_source=args.source_sha,
            message=f"Publish stable Forge site at {args.source_sha}",
        )


def parse_bool(value: str) -> bool:
    value = value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off", ""}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value}")


def write_outputs(path: Path | None, *, build_commit: str | None = None) -> None:
    if not path:
        return
    with path.open("a", encoding="utf-8") as handle:
        if build_commit:
            handle.write(f"build_commit={build_commit}\n")


def execute(args: argparse.Namespace) -> str | None:
    """Run migrated cheap layers first, then the existing Forge qualification."""

    run_tool_cad_ci_layers(
        args.output_root / "tool-cad-ci-plan.json",
        args.stage,
        args.cases,
        args.verify_references,
        args.verify_diagrams,
    )
    preflight(args.source_sha, args.output_root / "preflight-site")

    if args.verify_pipeline or args.image_built:
        if not args.image:
            raise ValueError("pipeline/image smoke requires --image")
        smoke_image(args.image, args.smoke_out)

    if args.verify_contracts:
        if not args.image:
            raise ValueError("contract verification requires --image")
        if not args.solidcraft_version:
            raise ValueError("contract verification requires --solidcraft-version")
        verify_contracts(args.image, args.solidcraft_version, args.contract_out)

    qualify(args)

    if args.operation == "pr":
        build_commit = publish_pr_candidate(args)
        resolve_preview(args, build_commit)
        return None

    root, build_commit, evidence_sha = stable_build(args)
    build_stable_site(args, root, build_commit, evidence_sha)
    return build_commit


def cleanup(pull_request: int) -> None:
    publish_generated.publish(
        branch="build",
        operation="remove-dir",
        destination=f"pr/{pull_request}",
        message=f"Remove build PR #{pull_request}",
    )
    publish_generated.publish(
        branch="gh-pages",
        operation="remove-dir",
        destination=f"previews/pr-{pull_request}",
        message=f"Remove preview PR #{pull_request}",
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run")
    run_parser.add_argument("--operation", choices=("pr", "main"), required=True)
    run_parser.add_argument("--source-sha", required=True)
    run_parser.add_argument("--base-sha", default="")
    run_parser.add_argument("--source-ref", required=True)
    run_parser.add_argument("--pull-request", type=int, default=0)
    run_parser.add_argument(
        "--stage",
        choices=("none", "tool_verify", "model_verify", "tool_qualification"),
        required=True,
    )
    run_parser.add_argument("--cases", default="")
    run_parser.add_argument("--verify-references", type=parse_bool, default=False)
    run_parser.add_argument("--verify-diagrams", type=parse_bool, default=False)
    run_parser.add_argument("--verify-pipeline", type=parse_bool, default=False)
    run_parser.add_argument("--image-built", type=parse_bool, default=False)
    run_parser.add_argument("--verify-contracts", type=parse_bool, default=False)
    run_parser.add_argument("--image", default="")
    run_parser.add_argument("--solidcraft-version", default="")
    run_parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    run_parser.add_argument("--workflow-run-id", default=os.environ.get("GITHUB_RUN_ID", "local"))
    run_parser.add_argument("--generated-build", type=Path, default=Path("generated-build"))
    run_parser.add_argument("--output-root", type=Path, default=Path("output"))
    run_parser.add_argument("--smoke-out", type=Path, default=Path(tempfile.gettempdir()) / "forge-simple-box")
    run_parser.add_argument("--contract-out", type=Path, default=Path(tempfile.gettempdir()) / "solidcraft-snapshot")
    run_parser.add_argument("--publish", type=parse_bool, default=False)
    run_parser.add_argument("--github-output", type=Path)

    cleanup_parser = sub.add_parser("cleanup")
    cleanup_parser.add_argument("--pull-request", type=int, required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    if args.command == "cleanup":
        cleanup(args.pull_request)
        return 0
    if args.operation == "pr" and args.pull_request <= 0:
        raise SystemExit("PR operation requires --pull-request")
    build_commit = execute(args)
    write_outputs(args.github_output, build_commit=build_commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run one qualification case as individually rerunnable stages."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
SCPF_ROOT = ROOT / "scpf"
if str(SCPF_ROOT) not in sys.path:
    sys.path.insert(0, str(SCPF_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.case_evidence import evidence_for
from qualification.case_selection import CASE_BY_SLUG
from qualification.cases import case_source_path, supported_case_slugs
from qualification.camera import camera as camera_for
from qualification.goal_overlay import render as render_goal_overlay
from qualification.native_cases import (
    POST_BUILD_INSPECTIONS,
    mutation_spec,
    validate_runtime_metadata,
)
from qualification.native_validation import VALIDATORS
from qualification.run_case_evidence import run as run_case_evidence
from qualification.run_post_build_inspections import run_post_build_inspections
from qualification.visual_validation import (
    load_baselines,
    render_views,
    validate_case as validate_visual_case,
)
from scpf.headless import run_document


STAGES = (
    "q1",
    "q2",
    "compile",
    "replay",
    "evaluate",
    "inspect",
    "render",
    "mutate",
    "evaluate-mutated",
    "post-build",
    "validate-native",
    "validate-visual",
    "gate",
)
STAGE_INDEX = {name: index + 1 for index, name in enumerate(STAGES)}


class MissingStageInput(RuntimeError):
    pass


@dataclass
class CaseContext:
    slug: str
    out: Path
    inputs: list[Path] = field(default_factory=list)
    outputs: list[Path] = field(default_factory=list)

    @property
    def native(self) -> Path:
        return self.out / "native" / self.slug

    @property
    def qualification(self) -> Path:
        return self.out / "qualification"

    @property
    def stages(self) -> Path:
        return self.out / "stages" / self.slug

    def reset_io(self) -> None:
        self.inputs.clear()
        self.outputs.clear()

    def require(self, *paths: Path) -> tuple[Path, ...]:
        missing = [path for path in paths if not path.is_file()]
        self.inputs.extend(paths)
        if missing:
            raise MissingStageInput(
                "missing stage input(s): "
                + ", ".join(_display(path) for path in missing)
            )
        return paths

    def produces(self, *paths: Path) -> tuple[Path, ...]:
        self.outputs.extend(paths)
        return paths


@dataclass(frozen=True)
class StageOutcome:
    status: str = "pass"
    reason: str | None = None


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _file_record(path: Path) -> dict:
    data = path.read_bytes()
    return {
        "path": _display(path),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(SCPF_ROOT), str(ROOT), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    env.setdefault("SOLIDCRAFT_GPU", "cpu")
    return env


def _run(command: list[str], *, cwd: Path = ROOT) -> None:
    subprocess.run(command, cwd=cwd, env=_env(), check=True)


def _state_path(ctx: CaseContext, stage: str) -> Path:
    return ctx.stages / f"{STAGE_INDEX[stage]:02d}-{stage}.json"


def _write_state(
    ctx: CaseContext,
    stage: str,
    *,
    status: str,
    started_at: str,
    duration: float,
    reason: str | None = None,
    error: str | None = None,
) -> None:
    ctx.stages.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": 1,
        "case": ctx.slug,
        "stage": stage,
        "number": STAGE_INDEX[stage],
        "status": status,
        "started_at": started_at,
        "duration_seconds": round(duration, 6),
        "inputs": [
            _file_record(path)
            for path in ctx.inputs
            if path.is_file()
        ],
        "outputs": [
            _file_record(path)
            for path in ctx.outputs
            if path.is_file()
        ],
    }
    if reason:
        payload["reason"] = reason
    if error:
        payload["error"] = error
    _state_path(ctx, stage).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def plan_stages(
    *,
    stage: str | None = None,
    start: str | None = None,
    until: str | None = None,
) -> tuple[str, ...]:
    for value in (stage, start, until):
        if value is not None and value not in STAGES:
            raise ValueError(
                f"unknown stage {value!r}; choose from {', '.join(STAGES)}"
            )
    if stage is not None:
        if start is not None or until is not None:
            raise ValueError("--stage cannot be combined with --from/--until")
        return (stage,)

    first = STAGES.index(start) if start else 0
    last = STAGES.index(until) if until else len(STAGES) - 1
    if first > last:
        raise ValueError("--from stage occurs after --until stage")
    return STAGES[first : last + 1]


def _q_stage(ctx: CaseContext, level: str) -> StageOutcome:
    stage_dir = ctx.stages / level / "evidence"
    stage_dir.mkdir(parents=True, exist_ok=True)
    for target in evidence_for(ctx.slug, level):
        ctx.require(ROOT / target["file"])
    result = run_case_evidence(level, stage_dir, ctx.slug)
    if result != 0:
        raise RuntimeError(f"{ctx.slug}: {level.upper()} evidence failed")
    source = stage_dir / "case-evidence" / level / f"{ctx.slug}.txt"
    ctx.require(source)
    target = (
        ctx.qualification
        / "case-evidence"
        / level
        / f"{ctx.slug}.txt"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    ctx.produces(target)
    return StageOutcome()


def _compile(ctx: CaseContext) -> StageOutcome:
    source = case_source_path(ctx.slug, "scpf")
    ctx.require(source)
    target = ctx.out / f"{ctx.slug}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            sys.executable,
            "-m",
            "scpf",
            str(source),
            "--out",
            str(target),
        ]
    )
    ctx.produces(target)
    return StageOutcome()


def _replay(ctx: CaseContext) -> StageOutcome:
    replay_path = ctx.out / f"{ctx.slug}.json"
    ctx.require(replay_path)
    ctx.native.mkdir(parents=True, exist_ok=True)
    outputs = (
        ctx.native / "model.sc",
        ctx.native / "model.step",
        ctx.native / "results.json",
        ctx.native / "replay-log.json",
    )
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    run_document(
        replay,
        save=outputs[0],
        export=outputs[1],
        results_out=outputs[2],
        replay_log_out=outputs[3],
        env=_env(),
        work_dir=ctx.native / "replay-work",
    )
    ctx.produces(*outputs)
    return StageOutcome()


def _evaluate(ctx: CaseContext) -> StageOutcome:
    model = ctx.native / "model.sc"
    ctx.require(model)
    target = ctx.native / "measurements.json"
    _run(
        [
            "solidcraft-cli",
            "eval",
            str(model),
            "--json-out",
            str(target),
        ]
    )
    ctx.produces(target)
    return StageOutcome()


def _inspect(ctx: CaseContext) -> StageOutcome:
    model = ctx.native / "model.sc"
    command = ROOT / "qualification" / "commands" / "inspect-joints.json"
    ctx.require(model, command)
    target = ctx.native / "joint-inspect.json"
    _run(
        [
            "solidcraft-cli",
            "run",
            str(command),
            "--in",
            str(model),
            "--param-check",
            "strict",
            "--results",
            "--json-out",
            str(target),
        ]
    )
    ctx.produces(target)
    return StageOutcome()


def _render(ctx: CaseContext) -> StageOutcome:
    model = ctx.native / "model.sc"
    measurements = ctx.native / "measurements.json"
    ctx.require(model, measurements)
    data = json.loads(measurements.read_text(encoding="utf-8"))

    baseline = ctx.native / "model.png"
    _run(
        [
            "solidcraft-cli",
            "snapshot",
            str(model),
            "--out",
            str(baseline),
            "--no-grid",
            "--no-axes",
        ]
    )
    ctx.produces(baseline)

    for view in render_views(ctx.slug):
        camera_path = ctx.native / f"camera-{view}.json"
        actual = ctx.native / f"model-{view}.png"
        goal = ctx.native / f"goal-{view}.png"
        overlay = ctx.native / f"overlay-{view}.png"
        camera = camera_for(data, view)
        camera_path.write_text(
            json.dumps(camera, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        _run(
            [
                "solidcraft-cli",
                "snapshot",
                str(model),
                "--out",
                str(actual),
                "--width",
                "720",
                "--height",
                "540",
                "--camera",
                json.dumps(camera, separators=(",", ":")),
                "--no-grid",
                "--no-axes",
            ]
        )
        render_goal_overlay(
            ctx.slug,
            camera_path,
            actual,
            goal,
            overlay,
        )
        ctx.produces(camera_path, actual, goal, overlay)
    return StageOutcome()


def _mutate(ctx: CaseContext) -> StageOutcome:
    spec = mutation_spec(ctx.slug)
    if spec is None:
        return StageOutcome("skipped", "case has no saved-design mutation")
    model = ctx.native / "model.sc"
    command = ROOT / spec["command"]
    ctx.require(model, command)
    target = ctx.native / spec["save"]
    _run(
        [
            "solidcraft-cli",
            "run",
            str(command),
            "--in",
            str(model),
            "--param-check",
            "strict",
            "--save",
            str(target),
        ]
    )
    ctx.produces(target)
    return StageOutcome()


def _evaluate_mutated(ctx: CaseContext) -> StageOutcome:
    spec = mutation_spec(ctx.slug)
    if spec is None:
        return StageOutcome("skipped", "case has no saved-design mutation")
    model = ctx.native / spec["save"]
    ctx.require(model)
    target = ctx.native / spec["measurements"]
    _run(
        [
            "solidcraft-cli",
            "eval",
            str(model),
            "--json-out",
            str(target),
        ]
    )
    ctx.produces(target)
    return StageOutcome()


def _post_build(ctx: CaseContext) -> StageOutcome:
    spec = POST_BUILD_INSPECTIONS.get(ctx.slug)
    if spec is None:
        return StageOutcome("skipped", "case has no post-build inspection")
    model = ctx.native / "model.sc"
    command = ROOT / spec["command"]
    ctx.require(model, command)
    summary = ctx.stages / "post-build" / "summary.tsv"
    run_post_build_inspections(
        ctx.out / "native",
        summary,
        cases=(ctx.slug,),
    )
    target = ctx.native / spec["output"]
    ctx.produces(target, summary)
    return StageOutcome()


def _validate_native(ctx: CaseContext) -> StageOutcome:
    baseline = ctx.native / "measurements.json"
    ctx.require(baseline)
    spec = mutation_spec(ctx.slug)
    if spec is not None:
        ctx.require(ctx.native / spec["measurements"])

    result = VALIDATORS[ctx.slug](ctx.native).result()
    target = ctx.native / "validation.json"
    target.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    ctx.produces(target)

    failures = []
    if result["q4"] != "pass":
        failures.append(f"Q4={result['q4']}")
    if CASE_BY_SLUG[ctx.slug].get("q5_required") and result["q5"] != "pass":
        failures.append(f"Q5={result['q5']}")
    if failures:
        raise RuntimeError(
            f"{ctx.slug}: native validation failed: " + ", ".join(failures)
        )
    return StageOutcome()


def _validate_visual(ctx: CaseContext) -> StageOutcome:
    required = [
        ctx.native / f"model-{view}.png"
        for view in render_views(ctx.slug)
    ]
    ctx.require(*required)
    baselines = load_baselines().get("cases", {})
    result = validate_visual_case(
        ctx.native,
        ctx.slug,
        baselines.get(ctx.slug),
    )
    target = ctx.native / "visual-validation.json"
    target.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    ctx.produces(target)
    if result["status"] != "pass":
        raise RuntimeError(
            f"{ctx.slug}: visual validation={result['status']}"
        )
    return StageOutcome()


def _gate(ctx: CaseContext) -> StageOutcome:
    native_path = ctx.native / "validation.json"
    visual_path = ctx.native / "visual-validation.json"
    ctx.require(native_path, visual_path)
    native = json.loads(native_path.read_text(encoding="utf-8"))
    visual = json.loads(visual_path.read_text(encoding="utf-8"))
    failures = []
    if native["q4"] != "pass":
        failures.append(f"Q4={native['q4']}")
    if CASE_BY_SLUG[ctx.slug].get("q5_required") and native["q5"] != "pass":
        failures.append(f"Q5={native['q5']}")
    if visual["status"] != "pass":
        failures.append(f"Q6={visual['status']}")
    if failures:
        raise RuntimeError(
            f"{ctx.slug}: gate failed: " + ", ".join(failures)
        )
    target = ctx.stages / "gate" / "result.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "schema": 1,
                "case": ctx.slug,
                "status": "pass",
                "q4": native["q4"],
                "q5": native["q5"],
                "q6": visual["status"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    ctx.produces(target)
    return StageOutcome()


STAGE_RUNNERS: dict[str, Callable[[CaseContext], StageOutcome]] = {
    "q1": lambda ctx: _q_stage(ctx, "q1"),
    "q2": lambda ctx: _q_stage(ctx, "q2"),
    "compile": _compile,
    "replay": _replay,
    "evaluate": _evaluate,
    "inspect": _inspect,
    "render": _render,
    "mutate": _mutate,
    "evaluate-mutated": _evaluate_mutated,
    "post-build": _post_build,
    "validate-native": _validate_native,
    "validate-visual": _validate_visual,
    "gate": _gate,
}


def run_case(
    slug: str,
    out: Path,
    *,
    stages: tuple[str, ...] = STAGES,
) -> dict[str, dict]:
    if slug not in supported_case_slugs():
        raise ValueError(f"unsupported qualification case: {slug}")
    validate_runtime_metadata()

    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    ctx = CaseContext(slug=slug, out=out)
    results: dict[str, dict] = {}

    for stage in stages:
        if stage not in STAGE_RUNNERS:
            raise ValueError(f"unknown stage: {stage}")
        ctx.reset_io()
        started_at = _now()
        started = time.perf_counter()
        print(
            f"[{STAGE_INDEX[stage]:02d}/{len(STAGES):02d}] "
            f"{slug}: {stage}"
        )
        try:
            outcome = STAGE_RUNNERS[stage](ctx)
        except Exception as exc:
            elapsed = time.perf_counter() - started
            _write_state(
                ctx,
                stage,
                status="fail",
                started_at=started_at,
                duration=elapsed,
                error=f"{type(exc).__name__}: {exc}",
            )
            raise

        elapsed = time.perf_counter() - started
        _write_state(
            ctx,
            stage,
            status=outcome.status,
            started_at=started_at,
            duration=elapsed,
            reason=outcome.reason,
        )
        results[stage] = json.loads(
            _state_path(ctx, stage).read_text(encoding="utf-8")
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=supported_case_slugs())
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "output" / "case",
    )
    parser.add_argument("--stage", choices=STAGES)
    parser.add_argument("--from", dest="start", choices=STAGES)
    parser.add_argument("--until", choices=STAGES)
    parser.add_argument(
        "--list-stages",
        action="store_true",
        help="print ordered stage names and exit",
    )
    args = parser.parse_args()

    if args.list_stages:
        for index, stage in enumerate(STAGES, 1):
            print(f"{index:02d} {stage}")
        return 0

    stages = plan_stages(
        stage=args.stage,
        start=args.start,
        until=args.until,
    )
    print(
        f"Case {args.case}; stages: "
        + " -> ".join(stages)
    )
    run_case(args.case, args.out, stages=stages)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

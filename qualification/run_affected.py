#!/usr/bin/env python3
"""Run Q1/Q2 plus full native qualification for selected Forge cases.

This is the short edit-check runner. It does not replace the full release gate:
SolidCraft upgrades and releases still run every Q1-Q6 case.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qualification.case_selection import (
    CASE_BY_SLUG,
    format_selection_help,
    parse_case_selection,
)
from qualification.native_cases import (
    POST_BUILD_INSPECTIONS,
    mutation_spec,
    validate_runtime_metadata,
)
from scpf.headless import run_document


def _run(
    command: list[str],
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    capture: bool = False,
) -> tuple[float, str]:
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=None,
    )
    elapsed = time.perf_counter() - started
    return elapsed, (completed.stdout or "")


def _solidcraft_env() -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("SOLIDCRAFT_GPU", "cpu")
    return env


def _camera(measurements: Path, view: str) -> str:
    _elapsed, output = _run(
        [
            sys.executable,
            "qualification/camera.py",
            str(measurements),
            view,
        ],
        capture=True,
    )
    return output.strip()


def _write_timings(out: Path, timings: dict) -> None:
    qualification = out / "qualification"
    qualification.mkdir(parents=True, exist_ok=True)
    (qualification / "affected-timings.json").write_text(
        json.dumps(timings, indent=2) + "\n",
        encoding="utf-8",
    )

    rows = ["case\tcompile\tbuild\teval\tsnapshot\tmutation\n"]
    for slug, values in timings["cases"].items():
        rows.append(
            "\t".join(
                [
                    slug,
                    f'{values["compile"]:.3f}',
                    f'{values["build"]:.3f}',
                    f'{values["eval"]:.3f}',
                    f'{values["snapshot"]:.3f}',
                    "" if values["mutation"] is None else f'{values["mutation"]:.3f}',
                ]
            )
            + "\n"
        )
    (qualification / "affected-timings.tsv").write_text(
        "".join(rows),
        encoding="utf-8",
    )


def _compile_case(slug: str, out: Path) -> float:
    out.mkdir(parents=True, exist_ok=True)
    elapsed, _ = _run(
        [
            sys.executable,
            "-m",
            "scpf",
            f"examples/{slug}/scpf/model.py",
            "--out",
            str(out / f"{slug}.json"),
        ]
    )
    return elapsed


def _build_case(slug: str, out: Path, env: dict[str, str]) -> tuple[float, float, float]:
    case_dir = out / "native" / slug
    case_dir.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    replay = json.loads(
        (out / f"{slug}.json").read_text(encoding="utf-8")
    )
    run_document(
        replay,
        save=case_dir / "model.sc",
        export=case_dir / "model.step",
        results_out=case_dir / "results.json",
        replay_log_out=case_dir / "replay-log.json",
        env=env,
        work_dir=case_dir / "replay-work",
    )
    build = time.perf_counter() - started

    evaluate, _ = _run(
        [
            "solidcraft-cli",
            "eval",
            str(case_dir / "model.sc"),
            "--json-out",
            str(case_dir / "measurements.json"),
        ],
        env=env,
    )

    _run(
        [
            "solidcraft-cli",
            "run",
            "qualification/commands/inspect-joints.json",
            "--in",
            str(case_dir / "model.sc"),
            "--param-check",
            "strict",
            "--results",
            "--json-out",
            str(case_dir / "joint-inspect.json"),
        ],
        env=env,
    )

    extra = POST_BUILD_INSPECTIONS.get(slug)
    if extra:
        _run(
            [
                "solidcraft-cli",
                "run",
                extra["command"],
                "--in",
                str(case_dir / "model.sc"),
                "--param-check",
                "strict",
                "--results",
                "--json-out",
                str(case_dir / extra["output"]),
            ],
            env=env,
        )

    snapshot_total = 0.0
    elapsed, _ = _run(
        [
            "solidcraft-cli",
            "snapshot",
            str(case_dir / "model.sc"),
            "--out",
            str(case_dir / "model.png"),
            "--no-grid",
            "--no-axes",
        ],
        env=env,
    )
    snapshot_total += elapsed

    for view in ("front", "right", "iso"):
        camera = _camera(case_dir / "measurements.json", view)
        (case_dir / f"camera-{view}.json").write_text(camera + "\n", encoding="utf-8")
        elapsed, _ = _run(
            [
                "solidcraft-cli",
                "snapshot",
                str(case_dir / "model.sc"),
                "--out",
                str(case_dir / f"model-{view}.png"),
                "--width",
                "720",
                "--height",
                "540",
                "--camera",
                camera,
                "--no-grid",
                "--no-axes",
            ],
            env=env,
        )
        snapshot_total += elapsed
        _run(
            [
                sys.executable,
                "qualification/goal_overlay.py",
                "--case",
                slug,
                "--camera",
                str(case_dir / f"camera-{view}.json"),
                "--actual",
                str(case_dir / f"model-{view}.png"),
                "--goal",
                str(case_dir / f"goal-{view}.png"),
                "--overlay",
                str(case_dir / f"overlay-{view}.png"),
            ]
        )

    return build, evaluate, snapshot_total


def _mutate_case(slug: str, out: Path, env: dict[str, str]) -> float | None:
    spec = mutation_spec(slug)
    if spec is None:
        return None

    case_dir = out / "native" / slug
    started = time.perf_counter()
    _run(
        [
            "solidcraft-cli",
            "run",
            spec["command"],
            "--in",
            str(case_dir / "model.sc"),
            "--param-check",
            "strict",
            "--save",
            str(case_dir / spec["save"]),
        ],
        env=env,
    )
    _run(
        [
            "solidcraft-cli",
            "eval",
            str(case_dir / spec["save"]),
            "--json-out",
            str(case_dir / spec["measurements"]),
        ],
        env=env,
    )
    return time.perf_counter() - started


def _run_validators(selection: str, out: Path) -> None:
    qualification = out / "qualification"
    native = out / "native"

    _run(
        [
            sys.executable,
            "qualification/native_validation.py",
            "--native-root",
            str(native),
            "--qualification-dir",
            str(qualification),
            "--cases",
            selection,
        ]
    )
    _run(
        [
            sys.executable,
            "qualification/visual_validation.py",
            "--native-root",
            str(native),
            "--qualification-dir",
            str(qualification),
            "--cases",
            selection,
        ]
    )


def _gate_selected(selected: tuple[str, ...], out: Path) -> None:
    qualification = out / "qualification"
    native = json.loads(
        (qualification / "native-validation.json").read_text(encoding="utf-8")
    )
    visual = json.loads(
        (qualification / "visual-validation.json").read_text(encoding="utf-8")
    )

    failures = []
    for slug in selected:
        native_result = native[slug]
        if native_result["q4"] != "pass":
            failures.append(f"{slug}: Q4={native_result['q4']}")
        if CASE_BY_SLUG[slug].get("q5_required") and native_result["q5"] != "pass":
            failures.append(f"{slug}: Q5={native_result['q5']}")
        if visual[slug]["status"] != "pass":
            failures.append(f"{slug}: Q6={visual[slug]['status']}")

    if failures:
        raise RuntimeError("selected qualification failed: " + "; ".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=format_selection_help(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--cases",
        required=True,
        help="comma/space separated case slugs, group:<name>, or all",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "output" / "affected",
        help="fresh output directory for selected qualification evidence",
    )
    args = parser.parse_args()

    selected = parse_case_selection(args.cases)
    validate_runtime_metadata()

    out = args.out.resolve()
    if out.exists():
        shutil.rmtree(out)
    (out / "native").mkdir(parents=True, exist_ok=True)
    (out / "qualification").mkdir(parents=True, exist_ok=True)

    timings = {
        "schema": 1,
        "selection": list(selected),
        "startup": None,
        "q1": None,
        "q2": None,
        "cases": {},
    }

    print("Affected qualification: " + ", ".join(selected))

    q1_global, _ = _run(
        [sys.executable, "-m", "unittest", "discover", "-s", "scpf/tests", "-v"]
    )
    q1_case, _ = _run(
        [
            sys.executable,
            "qualification/run_case_evidence.py",
            "--level",
            "q1",
            "--cases",
            ",".join(selected),
            "--out",
            str(out / "qualification"),
        ]
    )
    timings["q1"] = q1_global + q1_case

    q2_global, _ = _run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "qualification/tests",
            "-t",
            ".",
            "-v",
        ]
    )
    q2_case, _ = _run(
        [
            sys.executable,
            "qualification/run_case_evidence.py",
            "--level",
            "q2",
            "--cases",
            ",".join(selected),
            "--out",
            str(out / "qualification"),
        ]
    )
    timings["q2"] = q2_global + q2_case

    env = _solidcraft_env()
    timings["startup"], version = _run(
        ["solidcraft-cli", "--version"],
        env=env,
        capture=True,
    )
    print(version.strip())

    for slug in selected:
        print(f"\n== {slug} ==")
        compile_time = _compile_case(slug, out)
        build_time, eval_time, snapshot_time = _build_case(slug, out, env)
        mutation_time = _mutate_case(slug, out, env)
        timings["cases"][slug] = {
            "compile": compile_time,
            "build": build_time,
            "eval": eval_time,
            "snapshot": snapshot_time,
            "mutation": mutation_time,
        }

    _run_validators(",".join(selected), out)
    _gate_selected(selected, out)
    _write_timings(out, timings)

    print("\nTiming summary (seconds)")
    print(
        f"startup={timings['startup']:.3f} "
        f"q1={timings['q1']:.3f} q2={timings['q2']:.3f}"
    )
    for slug, values in timings["cases"].items():
        mutation = "-" if values["mutation"] is None else f'{values["mutation"]:.3f}'
        print(
            f"{slug}: compile={values['compile']:.3f} "
            f"build={values['build']:.3f} eval={values['eval']:.3f} "
            f"snapshot={values['snapshot']:.3f} mutation={mutation}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

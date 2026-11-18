#!/usr/bin/env python3
"""One-case end-to-end smoke for the qualification container.

This intentionally avoids the complete Q1/Q2/Q6 suite. It proves one vertical
path only: Forge -> SolidCraft -> saved design mutation -> native validator.
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


ROOT = Path(__file__).resolve().parents[2]
SCPF_ROOT = ROOT / "scpf"
if str(SCPF_ROOT) not in sys.path:
    sys.path.insert(0, str(SCPF_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.native_cases import mutation_spec
from scpf.headless import run_document


def run(command: list[str], *, env: dict[str, str]) -> float:
    started = time.perf_counter()
    subprocess.run(command, cwd=ROOT, env=env, check=True)
    return time.perf_counter() - started


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    out = args.out.resolve()
    if out.exists():
        shutil.rmtree(out)
    native = out / "native" / "simple-box"
    qualification = out / "qualification"
    native.mkdir(parents=True)
    qualification.mkdir(parents=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(SCPF_ROOT), str(ROOT), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    env.setdefault("SOLIDCRAFT_GPU", "cpu")

    timings: dict[str, float] = {}

    timings["solidcraft_startup"] = run(
        ["solidcraft-cli", "--version"],
        env=env,
    )

    replay_path = out / "simple-box.json"
    timings["forge_compile"] = run(
        [
            sys.executable,
            "-m",
            "scpf",
            "examples/simple-box/scpf/model.py",
            "--out",
            str(replay_path),
        ],
        env=env,
    )

    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    started = time.perf_counter()
    run_document(
        replay,
        save=native / "model.sc",
        export=native / "model.step",
        results_out=native / "results.json",
        replay_log_out=native / "replay-log.json",
        env=env,
        work_dir=native / "replay-work",
    )
    timings["native_replay"] = time.perf_counter() - started

    timings["native_eval"] = run(
        [
            "solidcraft-cli",
            "eval",
            str(native / "model.sc"),
            "--json-out",
            str(native / "measurements.json"),
        ],
        env=env,
    )

    mutation = mutation_spec("simple-box")
    if mutation is None:
        raise RuntimeError("simple-box mutation metadata is missing")

    timings["native_mutation"] = run(
        [
            "solidcraft-cli",
            "run",
            mutation["command"],
            "--in",
            str(native / "model.sc"),
            "--param-check",
            "strict",
            "--save",
            str(native / mutation["save"]),
        ],
        env=env,
    )

    timings["mutation_eval"] = run(
        [
            "solidcraft-cli",
            "eval",
            str(native / mutation["save"]),
            "--json-out",
            str(native / mutation["measurements"]),
        ],
        env=env,
    )

    timings["validation"] = run(
        [
            sys.executable,
            "qualification/native_validation.py",
            "--native-root",
            str(out / "native"),
            "--qualification-dir",
            str(qualification),
            "--cases",
            "simple-box",
        ],
        env=env,
    )

    result = json.loads(
        (qualification / "native-validation.json").read_text(encoding="utf-8")
    )["simple-box"]
    if result["q4"] != "pass" or result["q5"] != "pass":
        raise RuntimeError(
            f"simple-box integration failed: Q4={result['q4']} Q5={result['q5']}"
        )

    required = (
        native / "model.sc",
        native / "model.step",
        native / "measurements.json",
        native / mutation["measurements"],
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("simple-box smoke output missing: " + ", ".join(missing))

    (out / "smoke-timings.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "case": "simple-box",
                "status": "pass",
                "timings_seconds": timings,
                "total_seconds": sum(timings.values()),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("simple-box qualification-container smoke: PASS")
    for name, value in timings.items():
        print(f"  {name}: {value:.3f}s")
    print(f"  total: {sum(timings.values()):.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

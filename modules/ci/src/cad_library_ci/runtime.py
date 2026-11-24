"""Container dispatcher for model-local engine implementations."""
import argparse
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import traceback


def resolve(entry):
    module, function = entry.split(":", 1)
    return getattr(importlib.import_module(module), function)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def describe_error(exc):
    return "".join(traceback.format_exception_only(type(exc), exc)).strip()


def target_for(output, row):
    return output / "models" / row["owner"] / row["implementation"]


def build_row(row, output):
    artifact = target_for(output, row) / "model.stl"
    try:
        resolve(row["build_entry"])(Path(row["source"]), artifact)
        if not artifact.is_file() or not artifact.stat().st_size:
            raise RuntimeError("builder did not produce a nonempty STL")
        return {"status": "pass"}
    except Exception as exc:
        return {"status": "error", "error": describe_error(exc)}


def engine_batch(rows, output, interpreter):
    with tempfile.TemporaryDirectory(prefix="cad-engine-") as tmp:
        root = Path(tmp)
        manifest, report = root / "manifest.json", root / "report.json"
        write_json(manifest, {"schema": 1, "items": rows})
        try:
            completed = subprocess.run(
                [
                    interpreter,
                    "-m", "cad_library_ci.runtime",
                    "--manifest", str(manifest),
                    "--output", str(output),
                    "--build-report", str(report),
                ],
                check=False,
                timeout=1500,
            )
            payload = json.loads(report.read_text())
            expected_ids = {row["task_id"] for row in rows}
            if payload.get("schema") != 1 or set(payload["results"]) != expected_ids:
                raise RuntimeError("invalid engine batch report")
            results = payload["results"]
            if any(
                not isinstance(v, dict)
                or v.get("status") not in {"pass", "error"}
                for v in results.values()
            ):
                raise RuntimeError("invalid engine result")
            expected = (
                0 if all(v["status"] == "pass" for v in results.values()) else 1
            )
            if completed.returncode != expected:
                raise RuntimeError(
                    f"engine report disagrees with process exit {completed.returncode}"
                )
            return results
        except Exception as exc:
            return {
                row["task_id"]: {
                    "status": "error",
                    "error": describe_error(exc),
                }
                for row in rows
            }


def _build(manifest, output):
    rows = manifest.get("build_items", [])
    groups, built = {}, {}
    for row in rows:
        target = target_for(output, row)
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        interpreter = row.get("engine_python")
        if interpreter:
            groups.setdefault(interpreter, []).append(row)
        else:
            built[row["task_id"]] = build_row(row, output)
    for interpreter, group in groups.items():
        built.update(engine_batch(group, output, interpreter))

    for row in rows:
        status = built[row["task_id"]]
        write_json(
            target_for(output, row) / "build.json",
            {
                "schema": 1,
                "id": row["task_id"],
                "owner": row["owner"],
                "implementation": row["implementation"],
                "builder": row["builder"],
                "runtime": row.get("build_image", manifest.get("image")),
                "build_status": status["status"],
                "error": status.get("error"),
            },
        )
    return all(v["status"] == "pass" for v in built.values())


def _verify(manifest, output):
    rows = manifest.get("verify_items", [])
    passed = True
    results = []
    for row in rows:
        target = target_for(output, row)
        try:
            build = json.loads((target / "build.json").read_text())
        except Exception as exc:
            build = {"build_status": "error", "error": describe_error(exc)}
        result = {
            "id": row["task_id"],
            "owner": row["owner"],
            "implementation": row["implementation"],
            "builder": row["builder"],
            "runtime": row.get("build_image"),
            "verification_runtime": manifest.get("image"),
            "build_status": build.get("build_status", "error"),
            "verification_status": None,
            "status": "error",
        }
        if result["build_status"] == "pass":
            try:
                artifact = target / "model.stl"
                report = resolve(row["verify_entry"])(
                    row["adapter"],
                    artifact,
                    Path(row["definition"]),
                    target / "verification",
                    verification_id=row["task_id"],
                )
                status = report["status"]
                if status not in {"pass", "fail", "error"}:
                    raise ValueError(f"invalid verification status: {status}")
                result["verification_status"] = status
                result["status"] = status
                if status == "pass" and row.get("preview_entry"):
                    result["preview_status"] = "error"
                    resolve(row["preview_entry"])(
                        row["preview_adapter"], artifact, target
                    )
                    result["preview_status"] = "pass"
            except Exception as exc:
                result["error"] = describe_error(exc)
                result["status"] = "error"
                if result.get("preview_status") != "error":
                    result["verification_status"] = "error"
        else:
            result["error"] = build.get("error")

        write_json(target / "result.json", result)
        results.append(result)
        passed &= result["status"] == "pass"
        print(f"{row['task_id']}: {result['status']}", flush=True)

    if rows:
        write_json(
            output / f"batch-{manifest.get('runtime', 'runtime')}.json",
            {
                "schema": 3,
                "status": "pass" if passed else "fail",
                "results": results,
            },
        )
    return passed


def execute(manifest, output):
    if manifest.get("schema") != 3:
        raise ValueError("unsupported manifest")
    built = _build(manifest, output)
    verified = _verify(manifest, output)
    return 0 if built and verified else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build-report", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())

    if args.build_report:
        if manifest.get("schema") != 1:
            raise ValueError("unsupported engine manifest")
        rows = manifest.get("items", [])
        results = {
            row["task_id"]: build_row(row, args.output)
            for row in rows
        }
        write_json(args.build_report, {"schema": 1, "results": results})
        return 0 if all(r["status"] == "pass" for r in results.values()) else 1

    return execute(manifest, args.output)


if __name__ == "__main__":
    raise SystemExit(main())

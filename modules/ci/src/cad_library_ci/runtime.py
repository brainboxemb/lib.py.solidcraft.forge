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
    return "".join(
        traceback.format_exception_only(type(exc), exc)
    ).strip()


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
            if (
                payload.get("schema") != 1
                or set(payload["results"]) != expected_ids
            ):
                raise RuntimeError("invalid engine batch report")
            results = payload["results"]
            if any(
                not isinstance(value, dict)
                or value.get("status") not in {"pass", "error"}
                for value in results.values()
            ):
                raise RuntimeError("invalid engine result")
            expected = (
                0
                if all(
                    value["status"] == "pass"
                    for value in results.values()
                )
                else 1
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
    return all(value["status"] == "pass" for value in built.values())


def _verify(manifest, output):
    rows = manifest.get("verify_items", [])
    passed = True
    results = []

    for row in rows:
        target = target_for(output, row)
        stage_root = target / "verification" / row["stage_id"]
        try:
            build = json.loads(
                (target / "build.json").read_text(encoding="utf-8")
            )
        except Exception as exc:
            build = {
                "build_status": "error",
                "error": describe_error(exc),
            }

        result = {
            "schema": 1,
            "id": row["task_id"],
            "owner": row["owner"],
            "implementation": row["implementation"],
            "stage_id": row["stage_id"],
            "adapter": row["adapter"],
            "verification_runtime": manifest.get("image"),
            "status": "error",
        }

        if build.get("build_status") == "pass":
            try:
                artifact = target / row["artifact"]
                report = resolve(row["verify_entry"])(
                    row["adapter"],
                    artifact,
                    Path(row["definition"]),
                    stage_root,
                    verification_id=(
                        f"{row['owner']}-{row['implementation']}-{row['stage_id']}"
                    ),
                )
                status = report["status"]
                if status not in {"pass", "fail", "error"}:
                    raise ValueError(
                        f"invalid verification status: {status}"
                    )
                result["status"] = status
            except Exception as exc:
                result["error"] = describe_error(exc)
                result["status"] = "error"
        else:
            result["error"] = build.get("error")

        write_json(stage_root / "stage-result.json", result)
        results.append(result)
        passed &= result["status"] == "pass"
        print(
            f"{row['task_id']}:{row['stage_id']}: {result['status']}",
            flush=True,
        )

    if rows:
        write_json(
            output / f"batch-{manifest.get('runtime', 'runtime')}.json",
            {
                "schema": 4,
                "status": "pass" if passed else "fail",
                "results": results,
            },
        )
    return passed


def _preview(manifest, output):
    rows = manifest.get("preview_items", [])
    passed = True
    for row in rows:
        target = target_for(output, row)
        result = {
            "schema": 1,
            "id": row["task_id"],
            "owner": row["owner"],
            "implementation": row["implementation"],
            "status": "error",
        }
        try:
            build = json.loads(
                (target / "build.json").read_text(encoding="utf-8")
            )
            if build.get("build_status") != "pass":
                raise RuntimeError("preview requires a successful build")
            for stage_id in row.get("required_stages", []):
                stage = json.loads(
                    (
                        target
                        / "verification"
                        / stage_id
                        / "stage-result.json"
                    ).read_text(encoding="utf-8")
                )
                if stage.get("status") != "pass":
                    raise RuntimeError(
                        f"preview requires passing verification stage {stage_id}"
                    )
            resolve(row["preview_entry"])(
                row["preview_adapter"],
                target / row.get("artifact", "model.stl"),
                target,
            )
            result["status"] = "pass"
        except Exception as exc:
            result["error"] = describe_error(exc)
        write_json(target / "preview-result.json", result)
        passed &= result["status"] == "pass"
    return passed


def execute(manifest, output):
    if manifest.get("schema") != 4:
        raise ValueError("unsupported manifest")
    built = _build(manifest, output)
    verified = _verify(manifest, output)
    previewed = _preview(manifest, output)
    return 0 if built and verified and previewed else 1


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
        write_json(
            args.build_report,
            {"schema": 1, "results": results},
        )
        return 0 if all(
            result["status"] == "pass"
            for result in results.values()
        ) else 1

    return execute(manifest, args.output)


if __name__ == "__main__":
    raise SystemExit(main())

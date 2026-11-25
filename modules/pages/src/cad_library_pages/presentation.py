"""Read declared expectations and published evidence for model presentation."""
import json
import math
from html import escape


def _envelope(minimum, maximum, label):
    if not all(isinstance(v, (list, tuple)) and len(v) == 3 for v in (minimum, maximum)):
        return None
    if not all(isinstance(n, (int, float)) and not isinstance(n, bool)
               and math.isfinite(n) for n in [*minimum, *maximum]):
        return None
    if any(a > b for a, b in zip(minimum, maximum)):
        return None
    return (minimum, maximum, label)


def expected_setup(owner, ci, evidence):
    """Prefer accepted baseline expected body envelopes, never actual bounds."""
    implementations = ci.get("implementations", [])
    primary = ci.get("primary")
    ordered = sorted(implementations, key=lambda row: row["id"] != primary)
    if evidence:
        for impl in ordered:
            for stage in sorted((evidence / impl["id"] / "verification").glob("*/verification.json")):
                report = json.loads(stage.read_text(encoding="utf-8"))
                for check in report.get("checks", []):
                    if check.get("id") != "baseline":
                        continue
                    envelopes = check.get("evidence", {}).get("body_envelopes", {})
                    expected = [p.get("expected", {}) for p in envelopes.get("matched_pairs", [])]
                    expected += envelopes.get("unmatched_expected", [])
                    bodies = [_envelope(b.get("min"), b.get("max"), b.get("label") or f"Body {i + 1}")
                              for i, b in enumerate(expected)]
                    if bodies and all(bodies):
                        return bodies, f"Published {impl['id']} baseline: declared expected body envelopes"
    for stage in ci.get("verifications", []):
        if stage.get("adapter") != "mesh-geometry":
            continue
        definition = owner / stage.get("definition", "")
        if not definition.is_file() or not definition.resolve().is_relative_to(owner.resolve()):
            continue
        data = json.loads(definition.read_text(encoding="utf-8"))
        body = _envelope(data.get("bounds_min"), data.get("bounds_max"), "Overall envelope")
        if body:
            return [body], f"Declared geometry requirement: {stage['definition']}"
    return [], ""


def setup_svg(bodies):
    """Conceptual front projection, not a CAD rendering or verification image."""
    if not bodies:
        return ""
    xmin = min(lo[0] for lo, _, _ in bodies)
    xmax = max(hi[0] for _, hi, _ in bodies)
    zmin = min(lo[2] for lo, _, _ in bodies)
    zmax = max(hi[2] for _, hi, _ in bodies)
    scale = min(536 / max(xmax - xmin, 1), 248 / max(zmax - zmin, 1))
    xoff = (640 - (xmax - xmin) * scale) / 2
    yoff = 76 + (248 + (zmax - zmin) * scale) / 2
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 360" role="img" aria-label="Expected setup, conceptual front projection">',
             '<rect width="640" height="360" fill="#f6f9fd"/>',
             '<text x="24" y="32" font-size="19" font-weight="600" font-family="Segoe UI, sans-serif" fill="#182235">Expected setup — front projection</text>',
             '<text x="24" y="55" font-size="13" font-family="Segoe UI, sans-serif" fill="#526279">Declared envelopes · not a geometry rendering</text>']
    for i, (lo, hi, label) in enumerate(bodies):
        x = xoff + (lo[0] - xmin) * scale
        y = yoff - (hi[2] - zmin) * scale
        w = max((hi[0] - lo[0]) * scale, 1)
        h = max((hi[2] - lo[2]) * scale, 1)
        fill, stroke = (("#dce8f5", "#46627f"), ("#e5f2ea", "#47715d"))[i % 2]
        parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" fill-opacity=".65" stroke="{stroke}" stroke-width="2"/>')
        parts.append(f'<text x="{x + 5:.2f}" y="{y + 17:.2f}" font-size="12" font-family="Segoe UI, sans-serif" fill="#182235">{escape(str(label))}</text>')
    parts.append(f'<text x="24" y="345" font-size="13" font-family="Segoe UI, sans-serif" fill="#526279">Overall X: {xmax-xmin:g} mm · Z: {zmax-zmin:g} mm</text></svg>')
    return "".join(parts)


def command_sequence(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    commands = payload.get("commands", []) if isinstance(payload, dict) else payload
    if not isinstance(commands, list):
        raise ValueError(f"invalid command sequence: {path}")
    return [{"name": str(command.get("command", "Command")),
             "json": json.dumps(command, ensure_ascii=False, indent=2)}
            for command in commands]


def _value(value):
    """Display machine values without changing their meaning."""
    if isinstance(value, float):
        return format(value, ".12g")
    if isinstance(value, list) and all(isinstance(v, (int, float)) for v in value):
        return " × ".join(_value(v) for v in value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def comparison_rows(evidence):
    """Project explicit expected/actual pairs; never infer a PASS."""
    rows = []

    def add(label, expected, actual, status):
        rows.append({"label": label, "expected": _value(expected), "actual": _value(actual),
                     "status": "pass" if status is True else "fail" if status is False else "—"})

    for key, value in evidence.items():
        if not isinstance(value, dict):
            continue
        label = value.get("label") or key.replace("_", " ").capitalize()
        status = value.get("pass")
        if "expected" in value and "actual" in value:
            expected, actual = value["expected"], value["actual"]
            if isinstance(expected, dict) and isinstance(actual, dict):
                for name in sorted(expected.keys() | actual.keys()):
                    add(f"{label} / {name}", expected.get(name), actual.get(name), status)
            else:
                add(label, expected, actual, status)
        for name in sorted(value):
            if name.startswith("expected_"):
                suffix = name.removeprefix("expected_")
                actual_name = f"actual_{suffix}"
                if actual_name in value:
                    add(f"{label} / {suffix.replace('_', ' ')}", value[name], value[actual_name], status)
        if key == "body_envelopes":
            for i, pair in enumerate(value.get("matched_pairs", []), 1):
                expected, actual = pair.get("expected", {}), pair.get("actual", {})
                for bound in ("min", "max"):
                    if bound in expected and bound in actual:
                        add(f"Body {i} / {bound} [mm]", expected[bound], actual[bound], None)
    return rows


def implementation_evidence(root, blob_url, raw_url, state):
    """Use only artifacts actually present in this implementation's build."""
    data = {"status": state.get("status") or state.get("verification_status") or "unavailable",
            "previewurl": "", "files": [], "reports": [], "commands": [],
            "commandurl": "", "images": [], "checks": [], "visualviews": [],
            "drawings": []}
    if (root / "model.png").is_file():
        data["previewurl"] = f"{raw_url}/model.png"
    for name, label in (("model.stl", "STL"), ("model.step", "STEP"), ("model.sc", "Native model"),
                        ("result.json", "Build result")):
        if (root / name).is_file():
            data["files"].append({"label": label, "url": f"{blob_url}/{name}"})
    drawings = root / "drawings"
    if drawings.is_dir():
        for pdf in sorted(drawings.glob("*.pdf")):
            if pdf.is_file() and pdf.stat().st_size > 0:
                relative = pdf.relative_to(root).as_posix()
                preview = pdf.with_suffix(".png")
                preview_relative = (
                    preview.relative_to(root).as_posix()
                    if preview.is_file() and preview.stat().st_size > 0
                    else ""
                )
                data["drawings"].append({
                    "name": pdf.stem.replace("-", " "),
                    "bloburl": f"{blob_url}/{relative}",
                    "rawurl": f"{raw_url}/{relative}",
                    "previewurl": (
                        f"{raw_url}/{preview_relative}"
                        if preview_relative
                        else ""
                    ),
                })

    path = root / "solidcraft.json"
    if path.is_file():
        data["commands"] = command_sequence(path)
        data["commandurl"] = f"{blob_url}/solidcraft.json"
    reports = sorted((root / "verification").glob("*/verification.json"))
    legacy = root / "verification/verification.json"
    if not reports and legacy.is_file():
        reports = [legacy]
    for report in reports:
        relative = report.relative_to(root).as_posix()
        payload = json.loads(report.read_text(encoding="utf-8"))
        for check in payload.get("checks", []):
            check_evidence = check.get("evidence") or {}
            data["checks"].append({"stage": report.parent.name, "id": check.get("id", ""),
                                   "status": check.get("status", "unavailable"),
                                   "comparisons": comparison_rows(check_evidence)})
            visual_view = check_evidence.get("view")
            visual_paths = set()
            if isinstance(visual_view, str) and visual_view:
                images = []
                for field, label in (
                    ("actual_image", "Actual"),
                    ("goal_image", "Goal"),
                    ("overlay_image", "Overlay"),
                    ("diff_image", "Diff"),
                ):
                    rel = check_evidence.get(field)
                    if not isinstance(rel, str):
                        continue
                    candidate = report.parent / rel
                    if (
                        candidate.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}
                        and candidate.is_file()
                        and candidate.resolve().is_relative_to(root.resolve())
                    ):
                        image_path = candidate.resolve().relative_to(root.resolve()).as_posix()
                        images.append({"role": label, "url": f"{raw_url}/{image_path}"})
                        visual_paths.add(image_path)
                data["visualviews"].append({
                    "view": visual_view,
                    "status": check.get("status", "unavailable"),
                    "baseline_status": check_evidence.get("baseline_status", "missing"),
                    "expected_shape_status": check_evidence.get("expected_shape_status", "missing"),
                    "regression": check_evidence.get("regression"),
                    "images": images,
                })
            for artifact in check.get("artifacts", []):
                rel = artifact.get("path")
                if not isinstance(rel, str):
                    continue
                candidate = report.parent / rel
                if (candidate.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}
                        and candidate.is_file() and candidate.resolve().is_relative_to(root.resolve())):
                    image_path = candidate.resolve().relative_to(root.resolve()).as_posix()
                    if image_path not in visual_paths:
                        image = {"label": f"{report.parent.name} / {check.get('id', '')} / {rel}",
                                 "url": f"{raw_url}/{image_path}"}
                        if image not in data["images"]:
                            data["images"].append(image)
        data["reports"].append({"name": report.parent.name,
                                "url": f"{blob_url}/{relative}",
                                "json": json.dumps(payload, ensure_ascii=False, indent=2)})
    return data

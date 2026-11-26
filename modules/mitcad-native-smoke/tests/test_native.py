"""Run the first Forge model through the exact Mitcad v0.70.0 release."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "cadlib/src"))
sys.path.insert(0, str(ROOT / "modules/mitcad-reference/src"))
sys.path.insert(0, str(ROOT / "modules/verification/src"))

from cad_library_mitcad_reference import capture_runtime, git_blob_sha
from scpf import Axis, AxisLine, Box, Parameter, Polygon2D, Sketch
from scpf.backends.mitcad import compile_ir as compile_mitcad_ir
from scpf.backends.mitcad_headless import run_document
from scpf.ir import normalize_shape
from scpf.runner import run_script
from cad_verification.geometry import (
    load_geometry_contract,
    run_mesh_geometry_verification,
)


VERSION = "0.70.0"
ASSET_URL = (
    "https://github.com/mitcad/Mitcad/releases/download/v0.70.0/"
    "Mitcad-0.70.0-x86_64.AppImage"
)
ASSET_SHA256 = (
    "9e1e8919a0ccd8f48bba4b3d443c70fb92f44d6104357fc00c25bf4c18379551"
)
SOURCE_REFERENCE_BLOB = "40240776bc6885e228bf2fbd8e2534875aa61b85"
RUNTIME_REFERENCE_BLOB = "c839084ba223e814370a55c761644da362fabc93"
SIMPLE_BOX = ROOT / "models/simple-box/scpf/model.py"
NEGATIVE_CIRCLE = ROOT / "models/circle-negative-extrude/scpf/model.py"
TOPOLOGY_BOX = ROOT / "models/topology-face-boundary-box/scpf/model.py"


def ensure_appimage_runtime() -> None:
    """Install Mitcad's documented Ubuntu AppImage runtime libraries."""
    packages = [
        "libgl1",
        "libopengl0",
        "libegl1",
        "libglx-mesa0",
        "libgl1-mesa-dri",
        "libfontconfig1",
        "libfreetype6",
        "libdbus-1-3",
        "libglib2.0-0t64",
        "libx11-6",
        "libx11-xcb1",
        "libxext6",
        "libxrender1",
        "libxi6",
        "libsm6",
        "libice6",
        "libxkbcommon0",
        "libxkbcommon-x11-0",
        "libxcb-cursor0",
        "libxcb-icccm4",
        "libxcb-image0",
        "libxcb-keysyms1",
        "libxcb-render-util0",
        "libxcb-xinerama0",
        "libxcb-xkb1",
        "libxcb-shape0",
        "libxcb-randr0",
        "libwayland-client0",
        "libwayland-cursor0",
        "libwayland-egl1",
    ]
    subprocess.run(["sudo", "apt-get", "update", "-qq"], check=True)
    subprocess.run(
        ["sudo", "apt-get", "install", "-y", "-qq", *packages],
        check=True,
    )


def download_asset(destination: Path) -> None:
    request = Request(
        ASSET_URL,
        headers={"User-Agent": "Forge-Mitcad-Native-Smoke/1"},
    )
    digest = hashlib.sha256()
    with urlopen(request, timeout=120) as source, destination.open("wb") as out:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            out.write(chunk)
    actual = digest.hexdigest()
    if actual != ASSET_SHA256:
        raise AssertionError(
            f"Mitcad v{VERSION} AppImage digest mismatch: {actual}"
        )
    destination.chmod(
        destination.stat().st_mode
        | stat.S_IXUSR
        | stat.S_IXGRP
        | stat.S_IXOTH
    )


def cli_wrapper(root: Path, appimage: Path) -> Path:
    wrapper = root / "mitcad-cli"
    wrapper.write_text(
        "#!/bin/sh\n"
        "export APPIMAGE_EXTRACT_AND_RUN=1\n"
        "export QT_QPA_PLATFORM=offscreen\n"
        "exec " + repr(str(appimage)) + " cli \"$@\"\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    return wrapper


class MitcadNativeSmokeTests(unittest.TestCase):
    def test_simple_box_executes_in_exact_v070_release(self):
        with tempfile.TemporaryDirectory(prefix="forge-mitcad-native-") as tmp:
            root = Path(tmp)
            ensure_appimage_runtime()
            appimage = root / "Mitcad-0.70.0-x86_64.AppImage"
            download_asset(appimage)
            executable = cli_wrapper(root, appimage)

            cli_version, reference, catalog = capture_runtime(
                str(executable),
                workspace=root / "reference-workspace",
            )
            self.assertIn(VERSION, cli_version)
            self.assertEqual(
                git_blob_sha(reference),
                RUNTIME_REFERENCE_BLOB,
            )
            self.assertIn("add_feature", catalog["commands"])
            self.assertIn("box", catalog["features"])

            evidence = ROOT / "build/qualification/mitcad-v0.70.0"
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "runtime-commands.md").write_text(
                reference,
                encoding="utf-8",
            )
            (evidence / "commands.json").write_text(
                json.dumps(catalog, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            simple_box = run_document(
                run_script(SIMPLE_BOX, backend="mitcad"),
                save=root / "out/simple-box.mitcad",
                export=root / "out/simple-box.stl",
                executable=str(executable),
                work_dir=root / "simple-box-workspace",
            )

            self.assertEqual(simple_box["completed"], 4)
            self.assertEqual(len(simple_box["bodies"]), 1)
            box_body = simple_box["bodies"][0]
            self.assertEqual(box_body["kind"], "solid")
            self.assertAlmostEqual(box_body["volume"], 12000.0, places=5)
            for actual, expected in zip(
                box_body["bbox"]["min"],
                [-20.0, -15.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                box_body["bbox"]["max"],
                [20.0, 15.0, 10.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            circle = run_document(
                run_script(NEGATIVE_CIRCLE, backend="mitcad"),
                save=root / "out/circle-negative-extrude.mitcad",
                export=root / "out/circle-negative-extrude.stl",
                executable=str(executable),
                work_dir=root / "circle-workspace",
            )
            self.assertEqual(circle["completed"], 4)
            self.assertEqual(len(circle["bodies"]), 1)
            circle_body = circle["bodies"][0]
            self.assertEqual(circle_body["kind"], "solid")
            self.assertAlmostEqual(
                circle_body["volume"],
                3000.0 * 3.141592653589793,
                places=4,
            )
            for actual, expected in zip(
                circle_body["bbox"]["min"],
                [-10.0, -10.0, -30.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                circle_body["bbox"]["max"],
                [10.0, 10.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            for model_id in ("simple-box", "circle-negative-extrude"):
                source_stl = root / "out" / f"{model_id}.stl"
                retained_stl = evidence / f"{model_id}.stl"
                shutil.copy2(source_stl, retained_stl)
                report = run_mesh_geometry_verification(
                    retained_stl,
                    evidence / "verification" / model_id,
                    load_geometry_contract(
                        ROOT / "models" / model_id / "verification/geometry.json"
                    ),
                    verification_id=f"mitcad-{model_id}-geometry",
                )
                self.assertEqual(report["status"], "pass", report)

            topology = run_document(
                run_script(TOPOLOGY_BOX, backend="mitcad"),
                save=root / "out/topology-face-boundary-box.mitcad",
                export=root / "out/topology-face-boundary-box.stl",
                executable=str(executable),
                work_dir=root / "topology-workspace",
            )
            self.assertEqual(topology["completed"], 2)
            self.assertEqual(len(topology["bodies"]), 1)
            topology_body = topology["bodies"][0]
            self.assertEqual(topology_body["kind"], "solid")
            self.assertAlmostEqual(
                topology_body["volume"],
                28410.666666666664,
                places=4,
            )
            for actual, expected in zip(
                topology_body["bbox"]["min"],
                [-30.0, -20.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                topology_body["bbox"]["max"],
                [30.0, 20.0, 12.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            axis_x = Parameter("axis_x", 8)
            panel = Box(80, 46, 10)
            with Sketch(name="PassThrough", plane="XY") as profile:
                Polygon2D(
                    [
                        (12, -5),
                        (16, -5),
                        (16, 5),
                        (12, 5),
                    ],
                    plane="XY",
                )
            shifted_cut_shape = panel - profile.revolve(
                axis=AxisLine(
                    Axis.Y,
                    origin=(axis_x, 0, 0),
                ),
            )
            shifted_cut_document = compile_mitcad_ir(
                normalize_shape(shifted_cut_shape),
                "ShiftedRevolveCut",
            )

            # The native axis transport is parameter-driven in the compiled
            # document; the current value is not baked into the construction
            # line as the semantic source of truth.
            replay_sketch = shifted_cut_document["replay"][0]["commands"][0]["def"]
            construction = [
                entity
                for entity in replay_sketch["entities"]
                if entity.get("construction") is True
            ]
            self.assertEqual(len(construction), 1)
            self.assertIn(
                "axis_x",
                [
                    dimension["value"]
                    for dimension in replay_sketch["dimensions"]
                ],
            )

            shifted_cut = run_document(
                shifted_cut_document,
                save=root / "out/shifted-revolve-cut.mitcad",
                export=root / "out/shifted-revolve-cut.stl",
                executable=str(executable),
                work_dir=root / "shifted-revolve-cut-workspace",
            )
            self.assertEqual(shifted_cut["completed"], 4)
            self.assertEqual(len(shifted_cut["bodies"]), 1)
            shifted_body = shifted_cut["bodies"][0]
            self.assertEqual(shifted_body["kind"], "solid")
            self.assertAlmostEqual(
                shifted_body["volume"],
                36800.0 - 240.0 * 3.141592653589793,
                places=3,
            )
            for actual, expected in zip(
                shifted_body["bbox"]["min"],
                [-40.0, -23.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                shifted_body["bbox"]["max"],
                [40.0, 23.0, 10.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            shifted_stl = root / "out/shifted-revolve-cut.stl"
            retained_shifted_stl = evidence / "shifted-revolve-cut.stl"
            shutil.copy2(shifted_stl, retained_shifted_stl)
            self.assertGreater(retained_shifted_stl.stat().st_size, 0)

            for filename in (
                "simple-box.mitcad",
                "simple-box.stl",
                "circle-negative-extrude.mitcad",
                "circle-negative-extrude.stl",
                "topology-face-boundary-box.mitcad",
                "topology-face-boundary-box.stl",
                "shifted-revolve-cut.mitcad",
                "shifted-revolve-cut.stl",
            ):
                output = root / "out" / filename
                self.assertTrue(output.is_file(), filename)
                self.assertGreater(output.stat().st_size, 0, filename)

            (evidence / "native-smoke.txt").write_text(
                "\n".join(
                    [
                        f"version={cli_version}",
                        f"appimage_sha256={ASSET_SHA256}",
                        f"source_reference_blob={SOURCE_REFERENCE_BLOB}",
                        f"runtime_reference_blob={RUNTIME_REFERENCE_BLOB}",
                        f"simple_box_volume={box_body['volume']}",
                        f"simple_box_bbox={box_body['bbox']}",
                        f"negative_circle_volume={circle_body['volume']}",
                        f"negative_circle_bbox={circle_body['bbox']}",
                        "simple_box_generic_verification=pass",
                        "negative_circle_generic_verification=pass",
                        f"topology_volume={topology_body['volume']}",
                        f"topology_bbox={topology_body['bbox']}",
                        f"topology_bindings={topology['bindings']}",
                        f"shifted_revolve_cut_volume={shifted_body['volume']}",
                        f"shifted_revolve_cut_bbox={shifted_body['bbox']}",
                        f"shifted_revolve_cut_bindings={shifted_cut['bindings']}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )


if __name__ == "__main__":
    unittest.main()

"""Run the first Forge model through the exact Mitcad v0.70.0 release."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "cadlib/src"))
sys.path.insert(0, str(ROOT / "modules/mitcad-reference/src"))

from cad_library_mitcad_reference import capture_runtime, git_blob_sha
from scpf.backends.mitcad_headless import run_document
from scpf.runner import run_script


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

            for filename in (
                "simple-box.mitcad",
                "simple-box.stl",
                "circle-negative-extrude.mitcad",
                "circle-negative-extrude.stl",
                "topology-face-boundary-box.mitcad",
                "topology-face-boundary-box.stl",
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
                        f"topology_volume={topology_body['volume']}",
                        f"topology_bbox={topology_body['bbox']}",
                        f"topology_bindings={topology['bindings']}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )


if __name__ == "__main__":
    unittest.main()

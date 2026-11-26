"""Run the first Forge model through the exact Mitcad v0.70.0 release."""

from __future__ import annotations

import hashlib
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
REFERENCE_BLOB = "40240776bc6885e228bf2fbd8e2534875aa61b85"
MODEL = ROOT / "models/simple-box/scpf/model.py"


def ensure_appimage_runtime() -> None:
    """Install the one Ubuntu desktop library absent from GitHub's runner."""
    subprocess.run(["sudo", "apt-get", "update", "-qq"], check=True)
    subprocess.run(
        ["sudo", "apt-get", "install", "-y", "-qq", "libopengl0"],
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
            self.assertEqual(git_blob_sha(reference), REFERENCE_BLOB)
            self.assertIn("add_feature", catalog["commands"])
            self.assertIn("box", catalog["features"])

            command_document = run_script(MODEL, backend="mitcad")
            result = run_document(
                command_document,
                save=root / "out/simple-box.mitcad",
                export=root / "out/simple-box.stl",
                executable=str(executable),
                work_dir=root / "model-workspace",
            )

            self.assertEqual(result["completed"], 4)
            self.assertEqual(len(result["bodies"]), 1)
            body = result["bodies"][0]
            self.assertEqual(body["kind"], "solid")
            self.assertAlmostEqual(body["volume"], 12000.0, places=5)
            for actual, expected in zip(
                body["bbox"]["min"],
                [-20.0, -15.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                body["bbox"]["max"],
                [20.0, 15.0, 10.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            native = root / "out/simple-box.mitcad"
            stl = root / "out/simple-box.stl"
            self.assertTrue(native.is_file())
            self.assertGreater(native.stat().st_size, 0)
            self.assertTrue(stl.is_file())
            self.assertGreater(stl.stat().st_size, 0)

            evidence = ROOT / "build/qualification/mitcad-v0.70.0"
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "native-smoke.txt").write_text(
                "\n".join(
                    [
                        f"version={cli_version}",
                        f"appimage_sha256={ASSET_SHA256}",
                        f"reference_blob={REFERENCE_BLOB}",
                        f"volume={body['volume']}",
                        f"bbox={body['bbox']}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )


if __name__ == "__main__":
    unittest.main()

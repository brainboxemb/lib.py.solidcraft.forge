"""Tests for immutable SolidCraft runtime registry validation."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "solidcraft_runtime.py"


def load_runtime_module():
    """Load the runtime helper without making scripts a Python package."""

    spec = importlib.util.spec_from_file_location(
        "solidcraft_runtime_test_module",
        SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load solidcraft_runtime.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def completed(args, returncode=0, *, stdout="", stderr=""):
    """Build one literal subprocess result for a mocked Docker command."""

    return subprocess.CompletedProcess(
        args=args,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


class RuntimeRegistryTests(unittest.TestCase):
    def setUp(self):
        self.runtime = load_runtime_module()
        self.reference = "ghcr.io/example/runtime:runtime-abc"

    def test_image_exists_requires_manifest_and_real_pull(self):
        """A top-level manifest is insufficient without a consumable image."""

        with patch.object(
            self.runtime.subprocess,
            "run",
            side_effect=[
                completed(["docker", "manifest", "inspect", self.reference]),
                completed(["docker", "pull", self.reference]),
            ],
        ) as run:
            self.assertTrue(self.runtime.image_exists(self.reference))

        self.assertEqual(
            [call.args[0] for call in run.call_args_list],
            [
                ["docker", "manifest", "inspect", self.reference],
                ["docker", "pull", self.reference],
            ],
        )

    def test_missing_child_manifest_is_not_available(self):
        """A broken OCI index must be rebuilt instead of treated as present."""

        with patch.object(
            self.runtime.subprocess,
            "run",
            side_effect=[
                completed(["docker", "manifest", "inspect", self.reference]),
                completed(
                    ["docker", "pull", self.reference],
                    1,
                    stderr="child manifest sha256:abc not found",
                ),
            ],
        ):
            self.assertFalse(self.runtime.image_exists(self.reference))

    def test_missing_top_level_manifest_does_not_attempt_pull(self):
        """An absent tag remains the normal build-needed result."""

        with patch.object(
            self.runtime.subprocess,
            "run",
            return_value=completed(
                ["docker", "manifest", "inspect", self.reference],
                1,
                stderr="manifest unknown",
            ),
        ) as run:
            self.assertFalse(self.runtime.image_exists(self.reference))

        self.assertEqual(run.call_count, 1)

    def test_pull_authentication_error_is_not_reported_as_absence(self):
        """Credential/network errors may not silently trigger a rebuild."""

        with patch.object(
            self.runtime.subprocess,
            "run",
            side_effect=[
                completed(["docker", "manifest", "inspect", self.reference]),
                completed(
                    ["docker", "pull", self.reference],
                    1,
                    stderr="denied: permission_denied",
                ),
            ],
        ):
            with self.assertRaises(self.runtime.ImageLookupError):
                self.runtime.image_exists(self.reference)


if __name__ == "__main__":
    unittest.main()

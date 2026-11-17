"""The pinned SolidCraft runtime snapshot must match Forge source."""

from pathlib import Path
import subprocess
import sys
import unittest

from scpf.version import TESTED_SOLIDCRAFT_VERSION


ROOT = Path(__file__).resolve().parents[2]


class SolidCraftSnapshotTests(unittest.TestCase):
    def test_pinned_snapshot_matches_current_forge_commands(self):
        snapshot = (
            ROOT
            / "docs"
            / "vendor"
            / "solidcraft"
            / TESTED_SOLIDCRAFT_VERSION
            / "runtime"
        )
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "solidcraft_snapshot.py"),
                "--check-pinned",
                str(snapshot),
            ],
            check=True,
        )


if __name__ == "__main__":
    unittest.main()

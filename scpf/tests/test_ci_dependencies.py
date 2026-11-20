from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


forge_example = load_script("forge_example_ci_test", "scripts/forge_example.py")
verification_package = load_script(
    "verification_package_ci_test",
    "scripts/verification_package.py",
)


class CiDependencyTests(unittest.TestCase):
    def test_dependency_wheel_supports_separate_package_patterns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forge = root / "forge"
            verification = root / "verification"
            (forge / "dist").mkdir(parents=True)
            (verification / "dist").mkdir(parents=True)
            forge_wheel = forge / "dist" / "scpf-0.11.0-py3-none-any.whl"
            verification_wheel = (
                verification
                / "dist"
                / "brainboxemb_cad_verification_lib-0.12.0-py3-none-any.whl"
            )
            forge_wheel.write_bytes(b"forge")
            verification_wheel.write_bytes(b"verification")
            dependencies = {
                "forge-package": {"output_root": str(forge)},
                "cad-verification-package": {"output_root": str(verification)},
            }
            with patch.dict(
                os.environ,
                {"CAD_CI_DEPENDENCIES_JSON": json.dumps(dependencies)},
                clear=False,
            ):
                self.assertEqual(
                    forge_example.dependency_wheel(),
                    forge_wheel.resolve(),
                )
                self.assertEqual(
                    forge_example.dependency_wheel(
                        "cad-verification-package",
                        "brainboxemb_cad_verification_lib-*.whl",
                    ),
                    verification_wheel.resolve(),
                )

    def test_verification_wheel_version_reads_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            wheel = Path(tmp) / (
                "brainboxemb_cad_verification_lib-0.12.0-py3-none-any.whl"
            )
            with zipfile.ZipFile(wheel, "w") as archive:
                archive.writestr(
                    "brainboxemb_cad_verification_lib-0.12.0.dist-info/METADATA",
                    "Metadata-Version: 2.1\n"
                    "Name: brainboxemb-cad-verification-lib\n"
                    "Version: 0.12.0\n",
                )
            self.assertEqual(
                verification_package.wheel_version(wheel),
                "0.12.0",
            )


if __name__ == "__main__":
    unittest.main()

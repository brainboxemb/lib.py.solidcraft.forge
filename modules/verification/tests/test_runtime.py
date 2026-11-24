import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cad_verification.runtime import run


class RuntimeTests(unittest.TestCase):
    def test_dispatches_mesh_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "cad_verification.geometry.load_geometry_contract"
            ) as load, patch(
                "cad_verification.geometry.run_mesh_geometry_verification"
            ) as verify:
                run(
                    "mesh-geometry",
                    root / "model.stl",
                    root / "contract.json",
                    root / "verification",
                    verification_id="box",
                )
                verify.assert_called_once_with(
                    root / "model.stl",
                    root / "verification",
                    load.return_value,
                    verification_id="box",
                )

    def test_dispatches_solidcraft_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "cad_verification.adapters.solidcraft.run_solidcraft_verification_file"
            ) as verify:
                run(
                    "solidcraft-model",
                    root / "model.sc",
                    root / "verify.py",
                    root / "verification",
                    verification_id="box:native",
                )
                verify.assert_called_once_with(
                    root / "model.sc",
                    root / "verification",
                    root / "verify.py",
                )

    def test_unknown_adapter_fails(self):
        with self.assertRaises(ValueError):
            run(
                "unknown",
                Path("a"),
                Path("b"),
                Path("c"),
                verification_id="box",
            )


if __name__ == "__main__":
    unittest.main()

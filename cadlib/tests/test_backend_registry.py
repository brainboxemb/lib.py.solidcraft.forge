import unittest
from pathlib import Path

from scpf.backends import BackendAdapter, backend_ids, get_backend


ROOT = Path(__file__).resolve().parents[2]
SIMPLE_BOX = ROOT / "models/simple-box/scpf/model.py"


class BackendRegistryTests(unittest.TestCase):
    def test_stable_default_backend_contract_is_solidcraft(self):
        backend = get_backend("solidcraft")
        self.assertIsInstance(backend, BackendAdapter)
        self.assertEqual(backend.id, "solidcraft")
        self.assertEqual(backend.display_name, "SolidCraft")
        self.assertEqual(backend.executor, "solidcraft-cli")
        self.assertTrue(backend.supports_assemblies)
        self.assertFalse(backend.experimental)
        self.assertIn("stable-forge-surface", backend.capabilities)
        self.assertIn("native-topology", backend.capabilities)

    def test_mitcad_declares_only_qualified_experimental_slice(self):
        backend = get_backend("mitcad")
        self.assertEqual(backend.id, "mitcad")
        self.assertEqual(backend.display_name, "Mitcad")
        self.assertEqual(backend.document_family, "scpf-mitcad")
        self.assertEqual(backend.executor, "mitcad-mcp")
        self.assertFalse(backend.supports_assemblies)
        self.assertTrue(backend.experimental)
        self.assertEqual(
            backend.capabilities,
            frozenset(
                {
                    "primitive.box",
                    "sketch.circle",
                    "feature.extrude.distance",
                    "modify.chamfer.face-boundary",
                    "native-topology",
                }
            ),
        )

    def test_default_runner_output_equals_explicit_solidcraft(self):
        from scpf.runner import run_script

        self.assertEqual(
            run_script(SIMPLE_BOX),
            run_script(SIMPLE_BOX, backend="solidcraft"),
        )

    def test_backend_ids_are_explicit_and_unknown_is_rejected(self):
        self.assertEqual(backend_ids(), ("solidcraft", "mitcad"))
        with self.assertRaisesRegex(ValueError, "unknown SCPF backend"):
            get_backend("unknown")


if __name__ == "__main__":
    unittest.main()

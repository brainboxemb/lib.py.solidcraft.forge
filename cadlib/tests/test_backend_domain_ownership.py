"""Backend-domain ownership and runtime-independent lowering contracts."""

import unittest

from scpf import Box, Cylinder
from scpf.backends import get_backend
from scpf.backends.solidcraft import compile_ir as compile_solidcraft_ir
from scpf.backends.mitcad import compile_ir as compile_mitcad_ir
from scpf.ir import normalize_shape


class BackendDomainOwnershipTests(unittest.TestCase):
    def test_backend_entrypoints_are_owned_by_small_dispatch_modules(self):
        solidcraft = get_backend("solidcraft")
        mitcad = get_backend("mitcad")

        self.assertEqual(
            solidcraft.compile_ir.__module__,
            "scpf.backends.solidcraft.dispatch",
        )
        self.assertEqual(
            mitcad.compile_ir.__module__,
            "scpf.backends.mitcad.dispatch",
        )

    def test_solidcraft_primitive_ir_lowers_without_runtime(self):
        document = compile_solidcraft_ir(
            normalize_shape(Box(40, 30, 10)),
            "Panel",
        )

        self.assertIn("commands", document)
        commands = document["commands"]
        self.assertTrue(commands)
        self.assertEqual(commands[-1]["command"], "solid.box")
        self.assertEqual(commands[-1]["params"]["body_name"], "Panel")

    def test_mitcad_primitive_ir_lowers_without_runtime(self):
        document = compile_mitcad_ir(
            normalize_shape(Cylinder(d=20, h=12)),
            "Pin",
        )

        self.assertEqual(document["format"], "scpf-mitcad")
        self.assertEqual(document["backend"], "mitcad")
        self.assertTrue(document["commands"])
        self.assertEqual(document["commands"][-1]["cmd"], "add_feature")

    def test_domain_helpers_live_in_domain_modules(self):
        from scpf.backends.solidcraft import (
            _box_command,
            _solidcraft_profile_commands,
            _hole_commands,
            _chamfer_commands,
            _sheet_base_commands,
            _portable_configuration_commands,
        )
        from scpf.backends.mitcad import (
            _box_command as _mitcad_box_command,
            _mitcad_sketch_plane,
            _extrude_commands as _mitcad_extrude_commands,
            _mitcad_configuration_commands,
        )

        self.assertEqual(
            _box_command.__module__,
            "scpf.backends.solidcraft.primitives",
        )
        self.assertEqual(
            _solidcraft_profile_commands.__module__,
            "scpf.backends.solidcraft.sketch",
        )
        self.assertEqual(
            _hole_commands.__module__,
            "scpf.backends.solidcraft.features",
        )
        self.assertEqual(
            _chamfer_commands.__module__,
            "scpf.backends.solidcraft.operations",
        )
        self.assertEqual(
            _sheet_base_commands.__module__,
            "scpf.backends.solidcraft.sheet_metal",
        )
        self.assertEqual(
            _portable_configuration_commands.__module__,
            "scpf.backends.solidcraft.configuration",
        )
        self.assertEqual(
            _mitcad_box_command.__module__,
            "scpf.backends.mitcad.primitives",
        )
        self.assertEqual(
            _mitcad_sketch_plane.__module__,
            "scpf.backends.mitcad.sketch",
        )
        self.assertEqual(
            _mitcad_extrude_commands.__module__,
            "scpf.backends.mitcad.operations",
        )
        self.assertEqual(
            _mitcad_configuration_commands.__module__,
            "scpf.backends.mitcad.configuration",
        )


if __name__ == "__main__":
    unittest.main()

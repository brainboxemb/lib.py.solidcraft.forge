"""Legacy feature-lowering ownership and compatibility contracts."""

import inspect
import unittest

import scpf.features as compatibility
from scpf.compiler import legacy_features


class LegacyFeatureLoweringOwnershipTests(unittest.TestCase):
    def test_root_features_facade_preserves_representative_identity(self):
        names = (
            "_is_feature_tree",
            "_hole_commands",
            "_resolve_feature_edges",
            "_explicit_sketch_commands",
            "_native_feature_name",
            "_to_commands",
            "compile_features",
        )
        for name in names:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(compatibility, name),
                    getattr(legacy_features, name),
                )

    def test_representative_helpers_have_compiler_domain_owners(self):
        expected = {
            legacy_features._is_feature_tree:
                "scpf.compiler.legacy_features.detect",
            legacy_features._resolve_feature_edges:
                "scpf.compiler.legacy_features.topology",
            legacy_features._hole_commands:
                "scpf.compiler.legacy_features.features",
            legacy_features._explicit_sketch_commands:
                "scpf.compiler.legacy_features.sketch",
            legacy_features._pattern_count_parameter_names:
                "scpf.compiler.legacy_features.parameters",
            legacy_features._native_feature_name:
                "scpf.compiler.legacy_features.history",
            legacy_features._to_commands:
                "scpf.compiler.legacy_features.dispatch",
            legacy_features.compile_features:
                "scpf.compiler.legacy_features.dispatch",
        }
        for implementation, module in expected.items():
            with self.subTest(implementation=implementation):
                self.assertEqual(implementation.__module__, module)

    def test_root_features_defines_no_lowering_implementation(self):
        owned = {
            name
            for name, value in vars(compatibility).items()
            if (
                inspect.isclass(value) or inspect.isfunction(value)
            )
            and getattr(value, "__module__", None) == "scpf.features"
        }
        self.assertEqual(owned, set())


if __name__ == "__main__":
    unittest.main()

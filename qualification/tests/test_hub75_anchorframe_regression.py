"""Diagnostic command tests for the HUB75-like AnchorFrame regression."""

from pathlib import Path
import unittest

from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "examples" / "hub75-anchorframe-regression"


def commands(variant):
    return run_script(CASE / variant / "model.py")["commands"]


def of(rows, command):
    return [row["params"] for row in rows if row["command"] == command]


class Hub75AnchorFrameDiagnosticTests(unittest.TestCase):
    def test_both_variants_compile_same_reusable_component_counts(self):
        anchor = commands("scpf")
        baseline = commands("placement")

        for rows in (anchor, baseline):
            components = [row["name"] for row in of(rows, "component.create")]
            self.assertEqual(
                components,
                ["CornerBrackets", "SideBoard", "LProfile"],
            )

            copies = of(rows, "occurrence.copy")
            self.assertEqual(
                sum(row["component"] == "SideBoard" for row in copies),
                1,
            )
            self.assertEqual(
                sum(row["component"] == "LProfile" for row in copies),
                7,
            )

    def test_anchorframe_variant_authors_exactly_eight_relationships(self):
        rows = commands("scpf")
        joints = of(rows, "joint.create")

        self.assertEqual(len(joints), 8)
        self.assertTrue(all(row["type"] == "rigid" for row in joints))
        self.assertTrue(
            all(row["name"].startswith("Attach LProfile:") for row in joints)
        )

    def test_side_board_placements_remain_symbolic_in_both_variants(self):
        for variant in ("scpf", "placement"):
            moves = [
                row
                for row in of(commands(variant), "occurrence.move")
                if row["occurrence"].startswith("SideBoard:")
            ]
            self.assertEqual(len(moves), 2)
            self.assertTrue(
                all(
                    "opening_width" in str(row["translate"])
                    and "cabinet_depth" in str(row["translate"])
                    for row in moves
                )
            )

    def test_group_grounding_follows_relationship_semantics(self):
        anchor_group = next(
            row
            for row in of(commands("scpf"), "component.create")
            if row["name"] == "CornerBrackets"
        )
        placement_group = next(
            row
            for row in of(commands("placement"), "component.create")
            if row["name"] == "CornerBrackets"
        )

        self.assertFalse(anchor_group["grounded"])
        self.assertTrue(placement_group["grounded"])

    def test_attached_child_seed_remains_numeric_solver_seed(self):
        """Do not confuse seed lowering with the AnchorFrame regression.

        Historical Forge 79b2be2 already emitted concrete occurrence.move
        seeds for attached children while the same HUB75 A/B AnchorFrames
        qualified natively. The semantic relationship is owned by the eight
        rigid joints; only the explicit Placement baseline keeps its child
        positions parameter-driven.
        """

        anchor_moves = [
            row
            for row in of(commands("scpf"), "occurrence.move")
            if row["occurrence"].startswith("LProfile:")
        ]
        baseline_moves = [
            row
            for row in of(commands("placement"), "occurrence.move")
            if row["occurrence"].startswith("LProfile:")
        ]

        self.assertEqual(len(anchor_moves), 8)
        self.assertEqual(len(baseline_moves), 8)
        self.assertTrue(
            all(
                all(isinstance(value, (int, float)) for value in row["translate"])
                for row in anchor_moves
            )
        )
        self.assertTrue(
            all(
                any(isinstance(value, str) for value in row["translate"])
                for row in baseline_moves
            )
        )
        self.assertEqual(len(of(commands("scpf"), "joint.create")), 8)
        self.assertEqual(len(of(commands("placement"), "joint.create")), 0)


if __name__ == "__main__":
    unittest.main()

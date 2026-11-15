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
            self.assertEqual(components, ["SideBoard", "LProfile"])

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
                    for row in moves
                )
            )

    def test_current_first_divergence_is_attached_child_seed_lowering(self):
        """Record the regression before changing lowering.

        The Python attachment calculation retains parameter dependencies in the
        child Placement. Current assembly lowering intentionally converts an
        attached occurrence's seed move to concrete numbers. The independent
        Placement baseline keeps equivalent positions symbolic.
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
                not any(isinstance(value, str) for value in row["translate"])
                for row in anchor_moves
            ),
            "diagnostic changed: attached seeds are no longer flattened",
        )
        self.assertTrue(
            any(
                any(isinstance(value, str) for value in row["translate"])
                for row in baseline_moves
            )
        )

        self.assertEqual(len(of(commands("placement"), "joint.create")), 0)


if __name__ == "__main__":
    unittest.main()

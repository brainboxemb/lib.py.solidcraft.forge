"""Guard the staged Forge model-processing declaration."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"

EXPECTED_PROCESSED = {
    "anchor-topology-mutation",
    "anchored-holes",
    "assembly-decorator",
    "attach-angle",
    "components",
    "four-corner-l",
    "group-hierarchy",
    "hole-family",
    "parameter-scope",
    "parent-derived-child-size",
    "repeated-parent-attachments",
    "sheet-fold",
    "simple-box",
    "top-sketch-after-chamfer",
    "bracket",
    "circle-negative-extrude",
    "circular-feature-pattern",
    "eight-flightcase-corners",
    "primitive-csg",
    "rectangular-pattern",
    "round-top-sketch",
    "rounded-rectangle-sketch",
    "selective-profile-extrude",
    "slot-family",
    "xz-anchor",
}


class CiProcessSelectionContractTests(unittest.TestCase):
    """Keep the explicitly migrated Qualification set visible to CAD-CI."""

    def test_only_staged_proof_models_are_processed(self):
        """Declare process state for all 32 historical Qualification items."""

        configured = {}
        for ci_path in sorted(EXAMPLES.glob("*/ci.yml")):
            text = ci_path.read_text(encoding="utf-8")
            match = re.search(
                r"^process:\s*(true|false)\s*$",
                text,
                re.MULTILINE,
            )
            self.assertIsNotNone(
                match,
                f"missing explicit process declaration: {ci_path}",
            )
            configured[ci_path.parent.name] = match.group(1) == "true"

        self.assertEqual(len(configured), 32)
        self.assertEqual(
            {slug for slug, enabled in configured.items() if enabled},
            EXPECTED_PROCESSED,
        )


if __name__ == "__main__":
    unittest.main()

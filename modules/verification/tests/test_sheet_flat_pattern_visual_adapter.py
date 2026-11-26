"""Native sheet flat-pattern visual adapter contracts."""

import unittest

from cad_verification.adapters.sheet_flat_pattern_visual import (
    _match_perforations,
    parse_perforation_circles,
)


DXF = """0
SECTION
2
ENTITIES
0
CIRCLE
8
PERFORATION
10
-10
20
0
40
2.5
0
CIRCLE
8
PERFORATION
10
0
20
0
40
2.5
0
CIRCLE
8
OTHER
10
10
20
0
40
2.5
0
ENDSEC
0
EOF
"""


class SheetFlatPatternVisualAdapterTests(unittest.TestCase):
    def test_parser_reads_only_native_perforation_circles(self):
        self.assertEqual(
            parse_perforation_circles(DXF),
            [
                {"center": (-10.0, 0.0), "diameter": 5.0},
                {"center": (0.0, 0.0), "diameter": 5.0},
            ],
        )

    def test_matching_checks_count_centers_and_diameter(self):
        expected = [
            {"center": (-10.0, 0.0), "diameter": 5.0},
            {"center": (0.0, 0.0), "diameter": 5.0},
        ]
        actual = parse_perforation_circles(DXF)
        passed, evidence = _match_perforations(actual, expected, 0.001)
        self.assertTrue(passed)
        self.assertEqual(evidence["actual_count"], 2)

        bad = list(actual)
        bad[1] = {"center": (1.0, 0.0), "diameter": 5.0}
        passed, _ = _match_perforations(bad, expected, 0.001)
        self.assertFalse(passed)


if __name__ == "__main__":
    unittest.main()

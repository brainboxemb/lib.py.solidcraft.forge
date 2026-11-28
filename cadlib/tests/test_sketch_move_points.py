import unittest

from scpf import Sketch, compile_model


class SketchMovePointsTests(unittest.TestCase):
    def test_connected_clamp_profile_moves_six_semantic_points_in_one_solve(self):
        outer = 4.8083261121
        inner = 3.3941125497
        lip = 4.1012193309

        target_outer = (4.5461363383, 5.3228417592)
        target_inner = (3.2472402417, 3.8020298280)
        target_lip = (3.89668829, 4.5624357936)

        with Sketch(name="ClampProfile96", plane="XY") as sketch:
            profile = sketch.profile(start=(outer, outer))
            profile.arc_center_to(
                (outer, -outer), center=(0.0, 0.0), clockwise=False
            )
            profile.arc_center_to(
                (inner, -inner), center=(lip, -lip), clockwise=False
            )
            profile.arc_center_to(
                (inner, inner), center=(0.0, 0.0), clockwise=True
            )
            profile.arc_center_to(
                (outer, outer), center=(lip, lip), clockwise=False
            )
            profile.close()
            sketch.move_points([
                ((outer, outer), target_outer),
                ((outer, -outer), (target_outer[0], -target_outer[1])),
                ((inner, -inner), (target_inner[0], -target_inner[1])),
                ((inner, inner), target_inner),
                ((lip, -lip), (target_lip[0], -target_lip[1])),
                ((lip, lip), target_lip),
            ])

        body = sketch.extrude(12)
        commands = compile_model(body, "Clamp")["commands"]

        arcs = [
            command for command in commands
            if command["command"] == "sketch.arc.center_point"
        ]
        self.assertEqual(
            [arc["params"]["id"] for arc in arcs],
            ["a1", "a2", "a3", "a4"],
        )

        move = next(
            command for command in commands
            if command["command"] == "sketch.move_points"
        )
        self.assertEqual(
            [item["point"] for item in move["params"]["moves"]],
            [
                "a1.start",
                "a1.end",
                "a2.end",
                "a3.end",
                "a2.center",
                "a4.center",
            ],
        )
        self.assertEqual(
            [item["to"] for item in move["params"]["moves"]],
            [
                [target_outer[0], target_outer[1]],
                [target_outer[0], -target_outer[1]],
                [target_inner[0], -target_inner[1]],
                [target_inner[0], target_inner[1]],
                [target_lip[0], -target_lip[1]],
                [target_lip[0], target_lip[1]],
            ],
        )

    def test_move_points_rejects_non_finite_targets(self):
        with Sketch(name="Profile", plane="XY") as sketch:
            profile = sketch.profile(start=(10, 0))
            profile.arc_center_to((0, 10), center=(0, 0))
            profile.line_to((10, 0))
            profile.close()
            with self.assertRaisesRegex(ValueError, "fixed finite"):
                sketch.move_points([((10, 0), (float("inf"), 1))])


if __name__ == "__main__":
    unittest.main()

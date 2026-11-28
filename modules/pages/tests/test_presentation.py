import json
from pathlib import Path
import tempfile
import unittest

from cad_library_pages.presentation import expected_setup, setup_svg, implementation_evidence, comparison_rows


class PresentationTests(unittest.TestCase):
    def test_setup_uses_declared_expectation_not_actual_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            owner = Path(tmp)
            evidence = owner / "build"
            stage = evidence / "primary/verification/native"
            stage.mkdir(parents=True)
            (stage / "verification.json").write_text(json.dumps({"checks": [{
                "id": "baseline",
                "evidence": {"body_envelopes": {"matched_pairs": [{
                    "expected": {"min": [0, 0, 0], "max": [40, 30, 10], "label": "Target & body"},
                    "actual": {"min": [0, 0, 0], "max": [99, 99, 99]},
                }]}}
            }]}))
            ci = {"primary": "primary", "implementations": [{"id": "primary"}]}
            bodies, source = expected_setup(owner, ci, evidence)
            self.assertEqual(bodies[0][1], [40, 30, 10])
            self.assertIn("declared expected", source)
            svg = setup_svg(bodies)
            self.assertIn("Overall X: 40 mm", svg)
            self.assertIn("Target &amp; body", svg)
            self.assertNotIn("99 mm", svg)

    def test_comparison_uses_explicit_expected_measured_and_status(self):
        rows = comparison_rows({
            "parameters": {"expected": {"length": 40}, "actual": {"length": 39}, "pass": False},
            "bounds": {"expected_min": [0, 0, 0], "actual_min": [0, 0, 0], "pass": True},
            "body_envelopes": {"pass": True, "matched_pairs": [{
                "expected": {"min": [0, 0, 0]}, "actual": {"min": [0, 0, 0]}
            }]},
            "unpaired": {"actual": 123},
        })
        self.assertEqual(rows[0], {"label": "Parameters / length", "expected": "40", "actual": "39", "status": "fail"})
        self.assertEqual(rows[1]["status"], "pass")
        self.assertEqual(rows[2]["status"], "—")
        self.assertEqual(len(rows), 3)

    def test_source_only_uses_explicit_geometry_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            owner = Path(tmp)
            (owner / "geometry.json").write_text(json.dumps({
                "bounds_min": [-20, -15, 0], "bounds_max": [20, 15, 10]
            }))
            ci = {"verifications": [{"adapter": "mesh-geometry", "definition": "geometry.json"}]}
            bodies, source = expected_setup(owner, ci, None)
            self.assertEqual(bodies[0][0], [-20, -15, 0])
            self.assertIn("Declared geometry requirement", source)
            self.assertEqual(expected_setup(owner, {}, None), ([], ""))
            self.assertEqual(setup_svg([]), "")

    def test_implementation_owns_its_own_image_commands_and_stage_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "verification/geometry"
            stage.mkdir(parents=True)
            (stage / "actual.png").touch()
            (stage / "verification.json").write_text(json.dumps({"checks": [{"id": "geometry", "status": "pass", "artifacts": [{"path": "actual.png"}, {"path": "missing.png"}]}]}))
            (root / "model.png").touch()
            (root / "solidcraft.json").write_text(json.dumps({
                "commands": [{"command": "solid.box", "params": {"length": 40}}]
            }))
            data = implementation_evidence(root, "https://example.org/blob/reference", "https://example.org/raw/reference", {"status": "pass"})
            self.assertEqual(data["previewurl"], "https://example.org/raw/reference/model.png")
            self.assertEqual(data["commands"][0]["name"], "solid.box")
            self.assertEqual(data["checks"], [{"stage": "geometry", "id": "geometry", "status": "pass", "comparisons": []}])
            self.assertEqual(len(data["images"]), 1)
            self.assertTrue(data["images"][0]["url"].endswith("/verification/geometry/actual.png"))
            self.assertIn("verification/geometry/verification.json", data["reports"][0]["url"])
            missing = implementation_evidence(root / "missing", "blob", "raw", {})
            self.assertEqual(missing["previewurl"], "")
            self.assertEqual(missing["commands"], [])
            self.assertEqual(missing["status"], "unavailable")


    def test_visual_verification_stays_grouped_by_view_and_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "verification/visual"
            view = stage / "visual/front"
            view.mkdir(parents=True)
            for name in ("actual.png", "goal.png", "overlay.png", "diff.png"):
                (view / name).write_bytes(name.encode())
            (stage / "verification.json").write_text(json.dumps({
                "metadata": {"kind": "solidcraft-visual"},
                "checks": [{
                    "id": "front",
                    "status": "pass",
                    "evidence": {
                        "view": "front",
                        "actual_image": "visual/front/actual.png",
                        "goal_image": "visual/front/goal.png",
                        "overlay_image": "visual/front/overlay.png",
                        "diff_image": "visual/front/diff.png",
                        "baseline_status": "pass",
                        "expected_shape_status": "pass",
                        "regression": {
                            "mean_absolute_difference": 0.001,
                            "changed_pixel_fraction": 0.0,
                        },
                    },
                    "artifacts": [
                        {"path": "visual/front/actual.png"},
                        {"path": "visual/front/goal.png"},
                        {"path": "visual/front/overlay.png"},
                        {"path": "visual/front/diff.png"},
                    ],
                }],
            }))
            data = implementation_evidence(
                root,
                "https://example.org/blob/scpf",
                "https://example.org/raw/scpf",
                {"status": "pass"},
            )
            self.assertEqual(len(data["visualviews"]), 1)
            visual = data["visualviews"][0]
            self.assertEqual(visual["view"], "front")
            self.assertEqual(visual["status"], "pass")
            self.assertEqual(visual["baseline_status"], "pass")
            self.assertEqual(visual["expected_shape_status"], "pass")
            self.assertEqual(
                [image["role"] for image in visual["images"]],
                ["Actual", "Goal", "Overlay", "Diff"],
            )
            self.assertEqual(data["images"], [])


if __name__ == "__main__":
    unittest.main()

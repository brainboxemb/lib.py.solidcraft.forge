"""Requirement tests for reusable mesh geometry verification."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import trimesh

import cad_verification.geometry as geometry_module
from cad_verification import (
    CheckOutcome,
    GeometryContract,
    MeshLoadError,
    SurfaceDistanceProbe,
    VerificationCheck,
    VerificationConfigError,
    VerificationContext,
    VerificationFailure,
    geometry_contract_from_mapping,
    load_geometry_contract,
    run_mesh_geometry_verification,
    validate_mesh_geometry,
    verify,
)


class GeometryVerificationTests(unittest.TestCase):
    """Requirement-traceable tests for issue #7."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_mesh(self, name: str, mesh: trimesh.Trimesh) -> Path:
        path = self.root / name
        path.write_bytes(mesh.export(file_type="stl"))
        return path

    def cube(self) -> trimesh.Trimesh:
        return trimesh.creation.box(extents=(10.0, 20.0, 30.0))

    def cube_path(self) -> Path:
        return self.write_mesh("cube.stl", self.cube())

    def bounds_only(self, tolerance: float = 0.001) -> GeometryContract:
        return GeometryContract(
            bounds_min=(-5.0, -10.0, -15.0),
            bounds_max=(5.0, 10.0, 15.0),
            bounds_tolerance_mm=tolerance,
        )

    def full_contract(self) -> GeometryContract:
        return GeometryContract(
            bounds_min=(-5.0, -10.0, -15.0),
            bounds_max=(5.0, 10.0, 15.0),
            bounds_tolerance_mm=0.001,
            volume_mm3=6000.0,
            volume_tolerance_mm3=0.001,
            watertight=True,
            surface_distance_probes=(
                SurfaceDistanceProbe(
                    "on-x-face",
                    (5.0, 0.0, 0.0),
                    0.0,
                    0.001,
                ),
                SurfaceDistanceProbe(
                    "outside-x-face",
                    (10.0, 0.0, 0.0),
                    5.0,
                    0.001,
                ),
            ),
        )

    def test_r1_geometry_contract_validation(self):
        minimal = self.bounds_only()
        self.assertEqual(minimal.bounds_min, (-5.0, -10.0, -15.0))
        self.assertEqual(self.full_contract().volume_mm3, 6000.0)

        for minimum, maximum in (
            ((0, 0), (1, 1, 1)),
            ((0, 0, 0, 0), (1, 1, 1)),
        ):
            with self.subTest(minimum=minimum):
                with self.assertRaises(VerificationConfigError):
                    GeometryContract(minimum, maximum, 0.01)

        with self.assertRaises(VerificationConfigError):
            GeometryContract((0, 0, 0), (-1, 1, 1), 0.01)
        with self.assertRaises(VerificationConfigError):
            GeometryContract((0, 0, 0), (1, 1, 1), -0.01)
        with self.assertRaises(VerificationConfigError):
            GeometryContract(
                (0, 0, 0),
                (1, 1, 1),
                0.01,
                volume_mm3=1.0,
            )
        probe = SurfaceDistanceProbe("same", (0, 0, 0), 0, 0)
        with self.assertRaises(VerificationConfigError):
            GeometryContract(
                (0, 0, 0),
                (1, 1, 1),
                0.01,
                surface_distance_probes=(probe, probe),
            )
        with self.assertRaises(VerificationConfigError):
            GeometryContract(
                (0, 0, 0),
                (1, 1, 1),
                0.01,
                bounds_sufficient=False,
            )

        detailed = GeometryContract(
            (0, 0, 0),
            (1, 1, 1),
            0.01,
            volume_mm3=1.0,
            volume_tolerance_mm3=0.1,
            bounds_sufficient=False,
        )
        self.assertFalse(detailed.bounds_sufficient)

    def test_r2_surface_distance_probe_validation(self):
        probe = SurfaceDistanceProbe("edge", (1, 2, 3), 4, 0.1)
        self.assertEqual(probe.point, (1.0, 2.0, 3.0))

        invalid = (
            dict(label="", point=(0, 0, 0), distance_mm=0, tolerance_mm=0),
            dict(label="x", point=(0, 0), distance_mm=0, tolerance_mm=0),
            dict(label="x", point=(0, 0, 0), distance_mm=-1, tolerance_mm=0),
            dict(label="x", point=(0, 0, 0), distance_mm=0, tolerance_mm=-1),
        )
        for values in invalid:
            with self.subTest(values=values):
                with self.assertRaises(VerificationConfigError):
                    SurfaceDistanceProbe(**values)

    def test_r3_validate_mesh_geometry_returns_json_compatible_evidence(self):
        evidence = validate_mesh_geometry(
            self.cube_path(),
            self.full_contract(),
        )
        encoded = json.dumps(evidence, sort_keys=True)
        self.assertIn('"bounds"', encoded)
        self.assertTrue(evidence["bounds"]["pass"])

    def test_r4_stl_loading_errors_and_valid_mesh(self):
        with self.assertRaises(MeshLoadError):
            validate_mesh_geometry(
                self.root / "missing.stl",
                self.bounds_only(),
            )

        empty = self.root / "empty.stl"
        empty.write_bytes(b"")
        with self.assertRaises(MeshLoadError):
            validate_mesh_geometry(empty, self.bounds_only())

        malformed = self.root / "malformed.stl"
        malformed.write_text("this is not STL geometry", encoding="utf-8")
        with self.assertRaises(MeshLoadError):
            validate_mesh_geometry(malformed, self.bounds_only())

        evidence = validate_mesh_geometry(
            self.cube_path(),
            self.bounds_only(),
        )
        self.assertTrue(evidence["bounds"]["pass"])

        no_geometry = trimesh.Trimesh(
            vertices=[],
            faces=[],
            process=False,
        )
        placeholder = self.root / "placeholder.stl"
        placeholder.write_text("solid empty\nendsolid empty\n", encoding="utf-8")
        with mock.patch.object(
            geometry_module.trimesh,
            "load",
            return_value=no_geometry,
        ):
            with self.assertRaises(MeshLoadError):
                validate_mesh_geometry(
                    placeholder,
                    self.bounds_only(),
                )

        left = trimesh.creation.box(extents=(2.0, 2.0, 2.0))
        left.apply_translation((-3.0, 0.0, 0.0))
        right = trimesh.creation.box(extents=(2.0, 2.0, 2.0))
        right.apply_translation((3.0, 0.0, 0.0))
        scene = trimesh.Scene({"left": left, "right": right})
        scene_path = self.root / "scene.stl"
        scene_path.write_text("solid placeholder\nendsolid placeholder\n", encoding="utf-8")
        scene_contract = GeometryContract(
            bounds_min=(-4.0, -1.0, -1.0),
            bounds_max=(4.0, 1.0, 1.0),
            bounds_tolerance_mm=0.001,
        )
        with mock.patch.object(
            geometry_module.trimesh,
            "load",
            return_value=scene,
        ):
            scene_evidence = validate_mesh_geometry(
                scene_path,
                scene_contract,
            )
        self.assertTrue(scene_evidence["bounds"]["pass"])

    def test_r5_bounds_exact_tolerance_and_failure_evidence(self):
        path = self.cube_path()
        exact = validate_mesh_geometry(path, self.bounds_only())
        self.assertEqual(exact["bounds"]["max_delta_mm"], 0.0)

        inside = GeometryContract(
            bounds_min=(-5.0005, -10.0, -15.0),
            bounds_max=(5.0, 10.0, 15.0),
            bounds_tolerance_mm=0.001,
        )
        self.assertTrue(
            validate_mesh_geometry(path, inside)["bounds"]["pass"]
        )

        outside = GeometryContract(
            bounds_min=(-5.01, -10.0, -15.0),
            bounds_max=(5.0, 10.0, 15.0),
            bounds_tolerance_mm=0.001,
        )
        with self.assertRaises(VerificationFailure) as caught:
            validate_mesh_geometry(path, outside)
        evidence = caught.exception.evidence["bounds"]
        self.assertFalse(evidence["pass"])
        self.assertIn("expected_min", evidence)
        self.assertIn("actual_min", evidence)
        self.assertEqual(evidence["tolerance_mm"], 0.001)

    def test_r6_volume_check_is_optional_and_toleranced(self):
        path = self.cube_path()
        correct = self.full_contract()
        self.assertTrue(
            validate_mesh_geometry(path, correct)["volume"]["pass"]
        )

        wrong = GeometryContract(
            (-5, -10, -15),
            (5, 10, 15),
            0.001,
            volume_mm3=5990.0,
            volume_tolerance_mm3=0.5,
        )
        with self.assertRaises(VerificationFailure) as caught:
            validate_mesh_geometry(path, wrong)
        self.assertFalse(caught.exception.evidence["volume"]["pass"])

        inside = GeometryContract(
            (-5, -10, -15),
            (5, 10, 15),
            0.001,
            volume_mm3=5999.6,
            volume_tolerance_mm3=0.5,
        )
        self.assertTrue(
            validate_mesh_geometry(path, inside)["volume"]["pass"]
        )

        bounds_only = validate_mesh_geometry(path, self.bounds_only())
        self.assertNotIn("volume", bounds_only)

    def test_r7_watertight_pass_and_fail(self):
        closed = self.cube_path()
        open_mesh = self.cube()
        open_mesh.update_faces(
            [index < len(open_mesh.faces) - 2 for index in range(len(open_mesh.faces))]
        )
        open_mesh.remove_unreferenced_vertices()
        opened = self.write_mesh("open.stl", open_mesh)

        closed_true = GeometryContract(
            (-5, -10, -15),
            (5, 10, 15),
            0.001,
            watertight=True,
        )
        open_false = GeometryContract(
            (-5, -10, -15),
            (5, 10, 15),
            0.001,
            watertight=False,
        )
        self.assertTrue(
            validate_mesh_geometry(closed, closed_true)["watertight"]["pass"]
        )
        self.assertTrue(
            validate_mesh_geometry(opened, open_false)["watertight"]["pass"]
        )

        with self.assertRaises(VerificationFailure):
            validate_mesh_geometry(
                closed,
                GeometryContract(
                    (-5, -10, -15),
                    (5, 10, 15),
                    0.001,
                    watertight=False,
                ),
            )
        with self.assertRaises(VerificationFailure):
            validate_mesh_geometry(
                opened,
                GeometryContract(
                    (-5, -10, -15),
                    (5, 10, 15),
                    0.001,
                    watertight=True,
                ),
            )

    def test_r8_surface_distance_probes_pass_fail_and_keep_order(self):
        path = self.cube_path()
        contract = GeometryContract(
            (-5, -10, -15),
            (5, 10, 15),
            0.001,
            surface_distance_probes=(
                SurfaceDistanceProbe("surface", (5, 0, 0), 0, 0.001),
                SurfaceDistanceProbe("outside", (10, 0, 0), 5, 0.001),
            ),
        )
        probes = validate_mesh_geometry(
            path,
            contract,
        )["surface_distance_probes"]
        self.assertEqual(
            [probe["label"] for probe in probes],
            ["surface", "outside"],
        )
        self.assertTrue(all(probe["pass"] for probe in probes))

        failing = GeometryContract(
            (-5, -10, -15),
            (5, 10, 15),
            0.001,
            surface_distance_probes=(
                SurfaceDistanceProbe("wrong", (10, 0, 0), 4, 0.001),
            ),
        )
        with self.assertRaises(VerificationFailure) as caught:
            validate_mesh_geometry(path, failing)
        self.assertEqual(
            caught.exception.evidence["surface_distance_probes"][0]["label"],
            "wrong",
        )
        self.assertFalse(
            caught.exception.evidence["surface_distance_probes"][0]["pass"]
        )

    def test_r9_failure_evidence_keeps_prior_passing_checks(self):
        contract = GeometryContract(
            (-5, -10, -15),
            (5, 10, 15),
            0.001,
            volume_mm3=5000,
            volume_tolerance_mm3=0.1,
        )
        with self.assertRaises(VerificationFailure) as caught:
            validate_mesh_geometry(self.cube_path(), contract)
        evidence = caught.exception.evidence
        self.assertTrue(evidence["bounds"]["pass"])
        self.assertFalse(evidence["volume"]["pass"])

    def test_r10_verify_integration_maps_pass_fail_and_error(self):
        mesh = self.cube_path()

        def run(contract, path=mesh):
            output = self.root / (
                "output-" + str(len(list(self.root.glob("output-*"))))
            )
            context = VerificationContext(
                verification_id="geometry-test",
                input_path=path,
                output_dir=output,
            )

            def check(_ctx):
                return CheckOutcome.passed(
                    evidence=validate_mesh_geometry(path, contract)
                )

            report = verify(
                context,
                (VerificationCheck("geometry", check),),
            )
            stored = json.loads(
                (output / "verification.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report, stored)
            return report

        self.assertEqual(run(self.bounds_only())["status"], "pass")

        wrong = GeometryContract(
            (-6, -10, -15),
            (5, 10, 15),
            0.001,
        )
        failed = run(wrong)
        self.assertEqual(failed["status"], "fail")
        self.assertEqual(failed["checks"][0]["status"], "fail")

        errored = run(self.bounds_only(), self.root / "missing.stl")
        self.assertEqual(errored["status"], "error")
        self.assertEqual(errored["checks"][0]["status"], "error")
        self.assertIn("MeshLoadError", errored["checks"][0]["error"])

    def test_r11_geometry_evidence_is_deterministic(self):
        path = self.cube_path()
        first = validate_mesh_geometry(path, self.full_contract())
        second = validate_mesh_geometry(path, self.full_contract())
        self.assertEqual(first, second)

    def test_r12_geometry_module_has_no_consumer_dependencies(self):
        source = inspect.getsource(geometry_module)
        forbidden = (
            "solidcraft",
            "pythonscad",
            "pybosl2",
            "cadquery",
            "build123d",
            "simple-box",
        )
        for name in forbidden:
            with self.subTest(name=name):
                self.assertNotIn(name, source.lower())


    def test_r13_schema_one_contract_file_loads_without_consumer_code(self):
        """Existing reference_geometry.json data maps to GeometryContract."""

        path = self.root / "reference_geometry.json"
        path.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "bounds_min": [-5, -10, -15],
                    "bounds_max": [5, 10, 15],
                    "bounds_tolerance_mm": 0.25,
                    "volume_mm3": 6000,
                    "volume_tolerance_mm3": 1,
                    "watertight": True,
                    "bounds_sufficient": False,
                    "surface_distance_probes": [
                        {
                            "label": "outside-x",
                            "point": [10, 0, 0],
                            "distance_mm": 5,
                            "tolerance_mm": 0.1,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        contract = load_geometry_contract(path)
        self.assertEqual(contract.bounds_min, (-5.0, -10.0, -15.0))
        self.assertFalse(contract.bounds_sufficient)
        self.assertEqual(contract.surface_distance_probes[0].label, "outside-x")

    def test_r14_contract_mapping_rejects_schema_and_field_drift(self):
        """Malformed contract files fail before geometry is evaluated."""

        base = {
            "schema": 1,
            "bounds_min": [0, 0, 0],
            "bounds_max": [1, 1, 1],
            "bounds_tolerance_mm": 0.1,
        }
        self.assertEqual(
            geometry_contract_from_mapping(base).bounds_tolerance_mm,
            0.1,
        )

        with self.assertRaisesRegex(
            VerificationConfigError,
            "unsupported geometry contract schema",
        ):
            geometry_contract_from_mapping({**base, "schema": 2})

        with self.assertRaisesRegex(
            VerificationConfigError,
            "unsupported field",
        ):
            geometry_contract_from_mapping({**base, "typo": True})

        broken = self.root / "broken.json"
        broken.write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(
            VerificationConfigError,
            "invalid geometry contract JSON",
        ):
            load_geometry_contract(broken)

    def test_r15_mesh_runner_uses_standard_verification_report(self):
        """Mesh verification reuses verify() pass/fail report semantics."""

        output = self.root / "mesh-report"
        report = run_mesh_geometry_verification(
            self.cube_path(),
            output,
            self.bounds_only(),
            verification_id="mesh-test",
        )
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["checks"][0]["id"], "geometry")
        self.assertEqual(
            report,
            json.loads((output / "verification.json").read_text(encoding="utf-8")),
        )

        failing = GeometryContract(
            (-6, -10, -15),
            (5, 10, 15),
            0.001,
        )
        failed = run_mesh_geometry_verification(
            self.cube_path(),
            self.root / "mesh-fail",
            failing,
            verification_id="mesh-fail",
        )
        self.assertEqual(failed["status"], "fail")
        self.assertEqual(failed["checks"][0]["status"], "fail")


if __name__ == "__main__":
    unittest.main()

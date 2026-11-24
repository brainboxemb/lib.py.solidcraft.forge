"""Requirement tests for the SolidCraft CAD-tool verification adapter."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cad_verification import (
    BodyEnvelope,
    SolidCraftBodyExpectation,
    SolidCraftBodyGroupExpectation,
    SolidCraftEvidenceError,
    SolidCraftModelExpectation,
    SolidCraftSketchExpectation,
    SolidCraftTimelineExpectation,
    VerificationFailure,
    evaluate_solidcraft_model,
    inspect_solidcraft_model,
    mutate_solidcraft_model,
    verify_solidcraft_measurements,
)
import cad_verification.adapters.solidcraft as solidcraft_module


class SolidCraftAdapterTests(unittest.TestCase):
    def measurements(self):
        return {
            "body_count": 1,
            "bodies": [
                {
                    "name": "Plate",
                    "bbox": {
                        "min": [-20.0, -15.0, 0.0],
                        "max": [20.0, 15.0, 10.0],
                    },
                    "volume_mm3": 12000.0,
                    "faces": 6,
                    "center_of_mass": [0.0, 0.0, 5.0],
                    "sheet_metal": False,
                    "closed": True,
                }
            ],
            "params": [
                {"name": "length", "value": 40.0},
                {"name": "width", "value": 30.0},
                {"name": "height", "value": 10.0},
            ],
            "timeline": [
                {
                    "type": "BoxFeature",
                    "name": "Base",
                    "error": None,
                    "warning": None,
                }
            ],
            "sketches": [
                {
                    "name": "Profile",
                    "profiles": 1,
                    "curves": 4,
                    "dof": 0,
                    "status": "solved",
                }
            ],
        }

    def expectation(self):
        return SolidCraftModelExpectation(
            body_count=1,
            body_envelopes=(
                BodyEnvelope(
                    (-20.0, -15.0, 0.0),
                    (20.0, 15.0, 10.0),
                    "plate",
                ),
            ),
            bounds_tolerance=0.001,
            parameters={
                "length": 40.0,
                "width": 30.0,
                "height": 10.0,
            },
            named_bodies=(
                SolidCraftBodyExpectation(
                    name_prefix="Plate",
                    minimum=(-20.0, -15.0, 0.0),
                    maximum=(20.0, 15.0, 10.0),
                    bounds_tolerance=0.001,
                    volume_mm3=12000.0,
                    volume_tolerance=0.01,
                    sheet_metal=False,
                    closed=True,
                ),
            ),
            timeline=(
                SolidCraftTimelineExpectation(
                    feature_type="BoxFeature",
                    name="Base",
                    check_name=True,
                    error=None,
                    warning=None,
                ),
            ),
            sketches=(
                SolidCraftSketchExpectation(
                    name="Profile",
                    profiles=1,
                    curves=4,
                    status="solved",
                ),
            ),
        )

    def test_model_expectation_verifies_solidcraft_measurements(self):
        evidence = verify_solidcraft_measurements(
            self.measurements(),
            self.expectation(),
        )

        self.assertEqual(
            list(evidence),
            [
                "body_count",
                "body_envelopes",
                "parameters",
                "named_bodies",
                "timeline",
                "sketches",
            ],
        )
        self.assertTrue(evidence["body_count"]["pass"])
        self.assertTrue(evidence["body_envelopes"]["pass"])
        self.assertTrue(evidence["parameters"]["pass"])
        self.assertTrue(evidence["named_bodies"][0]["volume"]["pass"])
        self.assertTrue(evidence["timeline"]["pass"])
        self.assertTrue(evidence["sketches"][0]["pass"])


    def test_sketch_can_check_only_status(self):
        data = self.measurements()
        data["sketches"][0]["profiles"] = 99
        data["sketches"][0]["curves"] = 123

        expectation = SolidCraftModelExpectation(
            sketches=(
                SolidCraftSketchExpectation(
                    name="Profile",
                    status="solved",
                ),
            ),
        )

        evidence = verify_solidcraft_measurements(data, expectation)
        self.assertEqual(
            evidence["sketches"][0]["expected"],
            {"name": "Profile", "status": "solved"},
        )
        self.assertEqual(
            evidence["sketches"][0]["actual"],
            {"name": "Profile", "status": "solved"},
        )

    def test_partial_sketch_requires_declared_field(self):
        data = self.measurements()
        del data["sketches"][0]["status"]

        with self.assertRaisesRegex(
            SolidCraftEvidenceError,
            r"sketches\[0\]\.status",
        ):
            verify_solidcraft_measurements(
                data,
                SolidCraftModelExpectation(
                    sketches=(
                        SolidCraftSketchExpectation(
                            name="Profile",
                            status="solved",
                        ),
                    ),
                ),
            )

    def test_sketch_expectation_requires_property_check(self):
        from cad_verification import VerificationConfigError

        with self.assertRaisesRegex(
            VerificationConfigError,
            "at least one property",
        ):
            SolidCraftSketchExpectation(name="Profile")

    def test_sketch_count_checks_only_total_rows(self):
        data = self.measurements()
        data["sketches"][0] = "incidental-row-shape"

        evidence = verify_solidcraft_measurements(
            data,
            SolidCraftModelExpectation(sketch_count=1),
        )
        self.assertTrue(evidence["sketch_count"]["pass"])

    def test_timeline_type_counts_allow_unrelated_types(self):
        data = self.measurements()
        data["timeline"].append({"type": "OtherFeature", "name": 123})

        evidence = verify_solidcraft_measurements(
            data,
            SolidCraftModelExpectation(
                timeline_type_counts={
                    "BoxFeature": 1,
                    "HoleFeature": 0,
                }
            ),
        )

        self.assertEqual(
            evidence["timeline_type_counts"]["actual"],
            {"BoxFeature": 1, "HoleFeature": 0},
        )

    def test_sole_body_expectation_does_not_require_native_name(self):
        data = self.measurements()
        body = data["bodies"][0]
        del body["name"]
        body["face_types"] = {"cylinder": 2, "plane": 6}

        evidence = verify_solidcraft_measurements(
            data,
            SolidCraftModelExpectation(
                body_count=1,
                named_bodies=(
                    SolidCraftBodyExpectation(
                        volume_mm3=12000.0,
                        volume_tolerance=0.01,
                        face_type_counts={"cylinder": 2},
                        sheet_metal=False,
                        closed=True,
                    ),
                ),
            ),
        )

        row = evidence["named_bodies"][0]
        self.assertEqual(row["selector"], "sole")
        self.assertNotIn("name_prefix", row)
        self.assertNotIn("body_name", row)
        self.assertTrue(row["volume"]["pass"])
        self.assertTrue(row["face_type_counts"]["pass"])
        self.assertTrue(row["sheet_metal"]["pass"])
        self.assertTrue(row["closed"]["pass"])

    def test_sole_body_expectation_requires_exactly_one_body(self):
        data = self.measurements()
        data["bodies"].append(
            {
                "bbox": {
                    "min": [30.0, -15.0, 0.0],
                    "max": [70.0, 15.0, 10.0],
                },
                "volume_mm3": 12000.0,
            }
        )

        with self.assertRaisesRegex(
            VerificationFailure,
            "sole body count",
        ):
            verify_solidcraft_measurements(
                data,
                SolidCraftModelExpectation(
                    named_bodies=(
                        SolidCraftBodyExpectation(
                            volume_mm3=12000.0,
                        ),
                    ),
                ),
            )

    def test_body_face_count_and_center_of_mass_are_optional_checks(self):
        expectation = SolidCraftModelExpectation(
            named_bodies=(
                SolidCraftBodyExpectation(
                    face_count=6,
                    center_of_mass=(0.0, 0.0, 5.0),
                    center_of_mass_tolerance=0.001,
                ),
            ),
        )

        evidence = verify_solidcraft_measurements(
            self.measurements(),
            expectation,
        )
        row = evidence["named_bodies"][0]
        self.assertTrue(row["face_count"]["pass"])
        self.assertTrue(row["center_of_mass"]["pass"])
        self.assertNotIn("face_type_counts", row)

    def test_body_center_of_mass_uses_tolerance(self):
        data = self.measurements()
        data["bodies"][0]["center_of_mass"] = [0.0005, 0.0, 5.0]

        evidence = verify_solidcraft_measurements(
            data,
            SolidCraftModelExpectation(
                named_bodies=(
                    SolidCraftBodyExpectation(
                        center_of_mass=(0.0, 0.0, 5.0),
                        center_of_mass_tolerance=0.001,
                    ),
                ),
            ),
        )
        self.assertTrue(
            evidence["named_bodies"][0]["center_of_mass"]["pass"]
        )

        with self.assertRaises(VerificationFailure):
            verify_solidcraft_measurements(
                data,
                SolidCraftModelExpectation(
                    named_bodies=(
                        SolidCraftBodyExpectation(
                            center_of_mass=(0.0, 0.0, 5.0),
                            center_of_mass_tolerance=0.0001,
                        ),
                    ),
                ),
            )

    def test_sparse_center_of_mass_checks_only_requested_axes(self):
        data = self.measurements()
        data["bodies"][0]["center_of_mass"] = [0.0005, "ignored", None]

        evidence = verify_solidcraft_measurements(
            data,
            SolidCraftModelExpectation(
                named_bodies=(
                    SolidCraftBodyExpectation(
                        center_of_mass=(0.0, None, None),
                        center_of_mass_tolerance=0.001,
                    ),
                ),
            ),
        )

        center = evidence["named_bodies"][0]["center_of_mass"]
        self.assertEqual(list(center["components"]), ["x"])
        self.assertTrue(center["components"]["x"]["pass"])

    def test_sparse_center_of_mass_mismatch_is_verification_failure(self):
        data = self.measurements()
        data["bodies"][0]["center_of_mass"] = [0.01, "ignored", None]

        with self.assertRaises(VerificationFailure):
            verify_solidcraft_measurements(
                data,
                SolidCraftModelExpectation(
                    named_bodies=(
                        SolidCraftBodyExpectation(
                            center_of_mass=(0.0, None, None),
                            center_of_mass_tolerance=0.001,
                        ),
                    ),
                ),
            )

    def test_sparse_center_of_mass_rejects_all_omitted_axes(self):
        from cad_verification import VerificationConfigError

        with self.assertRaisesRegex(
            VerificationConfigError,
            "at least one axis",
        ):
            SolidCraftBodyExpectation(
                center_of_mass=(None, None, None),
            )

    def test_sparse_center_of_mass_validates_requested_axis(self):
        data = self.measurements()
        data["bodies"][0]["center_of_mass"] = ["broken", 0.0, 5.0]

        with self.assertRaisesRegex(
            SolidCraftEvidenceError,
            r"center_of_mass\[0\]",
        ):
            verify_solidcraft_measurements(
                data,
                SolidCraftModelExpectation(
                    named_bodies=(
                        SolidCraftBodyExpectation(
                            center_of_mass=(0.0, None, None),
                        ),
                    ),
                ),
            )

    def test_requested_body_face_count_requires_integer_evidence(self):
        data = self.measurements()
        data["bodies"][0]["faces"] = "six"

        with self.assertRaisesRegex(
            SolidCraftEvidenceError,
            r"bodies\[0\]\.faces",
        ):
            verify_solidcraft_measurements(
                data,
                SolidCraftModelExpectation(
                    named_bodies=(
                        SolidCraftBodyExpectation(face_count=6),
                    ),
                ),
            )

    def test_requested_center_of_mass_requires_xyz_numeric_evidence(self):
        data = self.measurements()
        data["bodies"][0]["center_of_mass"] = [0.0, 5.0]

        with self.assertRaisesRegex(
            SolidCraftEvidenceError,
            "exactly three",
        ):
            verify_solidcraft_measurements(
                data,
                SolidCraftModelExpectation(
                    named_bodies=(
                        SolidCraftBodyExpectation(
                            center_of_mass=(0.0, 0.0, 5.0),
                        ),
                    ),
                ),
            )

    def test_body_expectation_rejects_invalid_new_configuration(self):
        from cad_verification import VerificationConfigError

        with self.assertRaises(VerificationConfigError):
            SolidCraftBodyExpectation(face_count=-1)

        with self.assertRaisesRegex(
            VerificationConfigError,
            "exactly three",
        ):
            SolidCraftBodyExpectation(center_of_mass=(0.0, 1.0))

        with self.assertRaises(VerificationConfigError):
            SolidCraftBodyExpectation(
                center_of_mass=(0.0, 0.0, 0.0),
                center_of_mass_tolerance=-0.1,
            )

    def test_sketch_dof_is_sparse_and_exact(self):
        expectation = SolidCraftModelExpectation(
            sketches=(
                SolidCraftSketchExpectation(
                    name="Profile",
                    dof=0,
                ),
            ),
        )
        evidence = verify_solidcraft_measurements(
            self.measurements(),
            expectation,
        )
        self.assertEqual(
            evidence["sketches"][0]["expected"],
            {"name": "Profile", "dof": 0},
        )
        self.assertEqual(
            evidence["sketches"][0]["actual"],
            {"name": "Profile", "dof": 0},
        )

        data = self.measurements()
        data["sketches"][0]["dof"] = 1
        with self.assertRaises(VerificationFailure):
            verify_solidcraft_measurements(data, expectation)

    def test_requested_sketch_dof_requires_non_negative_integer(self):
        data = self.measurements()
        data["sketches"][0]["dof"] = "zero"
        with self.assertRaisesRegex(
            SolidCraftEvidenceError,
            r"sketches\[0\]\.dof",
        ):
            verify_solidcraft_measurements(
                data,
                SolidCraftModelExpectation(
                    sketches=(
                        SolidCraftSketchExpectation(
                            name="Profile",
                            dof=0,
                        ),
                    ),
                ),
            )

        from cad_verification import VerificationConfigError
        with self.assertRaises(VerificationConfigError):
            SolidCraftSketchExpectation(name="Profile", dof=-1)

    def test_named_body_face_type_counts_are_partial(self):
        data = self.measurements()
        data["bodies"][0]["face_types"] = {
            "cylinder": 2,
            "plane": "not-requested",
        }

        evidence = verify_solidcraft_measurements(
            data,
            SolidCraftModelExpectation(
                named_bodies=(
                    SolidCraftBodyExpectation(
                        name_prefix="Plate",
                        face_type_counts={
                            "cone": 0,
                            "cylinder": 2,
                        },
                    ),
                ),
            ),
        )

        self.assertEqual(
            evidence["named_bodies"][0]["face_type_counts"]["actual"],
            {"cone": 0, "cylinder": 2},
        )

    def test_requested_face_type_count_must_be_integer(self):
        data = self.measurements()
        data["bodies"][0]["face_types"] = {"cylinder": "two"}

        with self.assertRaisesRegex(
            SolidCraftEvidenceError,
            r"face_types\.cylinder",
        ):
            verify_solidcraft_measurements(
                data,
                SolidCraftModelExpectation(
                    named_bodies=(
                        SolidCraftBodyExpectation(
                            name_prefix="Plate",
                            face_type_counts={"cylinder": 2},
                        ),
                    ),
                ),
            )

    def test_count_expectation_rejects_negative_configuration(self):
        from cad_verification import VerificationConfigError

        with self.assertRaises(VerificationConfigError):
            SolidCraftModelExpectation(sketch_count=-1)

        with self.assertRaises(VerificationConfigError):
            SolidCraftModelExpectation(
                timeline_type_counts={"HoleFeature": -1}
            )

    def test_timeline_can_ignore_generated_name(self):
        data = self.measurements()
        data["timeline"][0]["name"] = "Box1"

        expectation = SolidCraftModelExpectation(
            timeline=(
                SolidCraftTimelineExpectation(
                    feature_type="BoxFeature",
                    error=None,
                    warning=None,
                ),
            ),
        )

        evidence = verify_solidcraft_measurements(data, expectation)
        self.assertTrue(evidence["timeline"]["pass"])
        self.assertEqual(
            evidence["timeline"]["expected"],
            [
                {
                    "type": "BoxFeature",
                    "error": None,
                    "warning": None,
                }
            ],
        )
        self.assertNotIn("name", evidence["timeline"]["actual"][0])

    def test_timeline_name_can_be_checked_explicitly(self):
        data = self.measurements()

        expectation = SolidCraftModelExpectation(
            timeline=(
                SolidCraftTimelineExpectation(
                    feature_type="BoxFeature",
                    name="Base",
                    check_name=True,
                    error=None,
                    warning=None,
                ),
            ),
        )
        self.assertTrue(
            verify_solidcraft_measurements(data, expectation)["timeline"]["pass"]
        )

        data["timeline"][0]["name"] = "Box1"
        with self.assertRaises(VerificationFailure):
            verify_solidcraft_measurements(data, expectation)

    def test_disabled_timeline_field_rejects_supplied_value(self):
        from cad_verification import VerificationConfigError

        with self.assertRaises(VerificationConfigError):
            SolidCraftTimelineExpectation(
                feature_type="BoxFeature",
                name="Base",
                check_name=False,
            )

    def test_model_mismatch_is_verification_failure(self):
        data = self.measurements()
        data["params"][0]["value"] = 41.0

        with self.assertRaises(VerificationFailure):
            verify_solidcraft_measurements(data, self.expectation())

    def test_malformed_body_is_evidence_error_and_is_not_skipped(self):
        data = self.measurements()
        data["bodies"].append({"name": "Broken", "bbox": None})
        data["body_count"] = 2

        expectation = SolidCraftModelExpectation(
            body_count=2,
            body_envelopes=(
                BodyEnvelope(
                    (-20.0, -15.0, 0.0),
                    (20.0, 15.0, 10.0),
                ),
                BodyEnvelope((0, 0, 0), (1, 1, 1)),
            ),
            bounds_tolerance=0.001,
        )

        with self.assertRaisesRegex(
            SolidCraftEvidenceError,
            r"bodies\[1\]\.bbox",
        ):
            verify_solidcraft_measurements(data, expectation)

    def test_parameter_match_exact_remains_default(self):
        data = self.measurements()
        data["params"].append({"name": "unrelated", "value": 99.0})

        with self.assertRaises(VerificationFailure):
            verify_solidcraft_measurements(
                data,
                SolidCraftModelExpectation(parameters={"length": 40.0}),
            )

    def test_parameter_subset_compares_only_requested_names(self):
        data = self.measurements()
        expectation = SolidCraftModelExpectation(
            parameters={"length": 40.0},
            parameter_match="subset",
        )

        evidence = verify_solidcraft_measurements(data, expectation)

        self.assertEqual(
            evidence["parameters"]["expected"],
            {"length": 40.0},
        )
        self.assertEqual(
            evidence["parameters"]["actual"],
            {"length": 40.0},
        )
        self.assertTrue(evidence["parameters"]["pass"])

    def test_parameter_subset_requires_requested_name(self):
        with self.assertRaises(VerificationFailure):
            verify_solidcraft_measurements(
                self.measurements(),
                SolidCraftModelExpectation(
                    parameters={"missing": 1.0},
                    parameter_match="subset",
                ),
            )

    def test_parameter_subset_still_validates_unrelated_rows(self):
        data = self.measurements()
        data["params"].append({"name": "broken", "value": "not-a-number"})

        with self.assertRaisesRegex(SolidCraftEvidenceError, r"params\[3\]"):
            verify_solidcraft_measurements(
                data,
                SolidCraftModelExpectation(
                    parameters={"length": 40.0},
                    parameter_match="subset",
                ),
            )

    def test_invalid_parameter_match_is_configuration_error(self):
        from cad_verification import VerificationConfigError

        with self.assertRaisesRegex(
            VerificationConfigError,
            "parameter_match",
        ):
            SolidCraftModelExpectation(
                parameters={"length": 40.0},
                parameter_match="loose",
            )

    def test_malformed_parameter_row_is_evidence_error(self):
        data = self.measurements()
        data["params"][0] = {"name": "length", "value": "forty"}

        with self.assertRaisesRegex(SolidCraftEvidenceError, r"params\[0\]"):
            verify_solidcraft_measurements(
                data,
                SolidCraftModelExpectation(parameters={"length": 40.0}),
            )

    def test_body_group_matches_multiple_prefixed_bodies(self):
        data = self.measurements()
        first = data["bodies"][0]
        first["name"] = "Block"
        second = {
            **first,
            "name": "Block (Block:2)",
            "bbox": {
                "min": [20.0, -15.0, 0.0],
                "max": [60.0, 15.0, 10.0],
            },
        }
        data["bodies"].append(second)
        data["body_count"] = 2

        expectation = SolidCraftModelExpectation(
            body_groups=(
                SolidCraftBodyGroupExpectation(
                    name_prefix="Block",
                    count=2,
                    body_envelopes=(
                        BodyEnvelope(
                            (20.0, -15.0, 0.0),
                            (60.0, 15.0, 10.0),
                        ),
                        BodyEnvelope(
                            (-20.0, -15.0, 0.0),
                            (20.0, 15.0, 10.0),
                        ),
                    ),
                    bounds_tolerance=0.001,
                ),
            ),
        )

        evidence = verify_solidcraft_measurements(data, expectation)
        group = evidence["body_groups"][0]
        self.assertEqual(
            group["matched_names"],
            ["Block", "Block (Block:2)"],
        )
        self.assertTrue(group["count"]["pass"])
        self.assertTrue(group["body_envelopes"]["pass"])

    def test_body_group_count_mismatch_fails(self):
        with self.assertRaises(VerificationFailure):
            verify_solidcraft_measurements(
                self.measurements(),
                SolidCraftModelExpectation(
                    body_groups=(
                        SolidCraftBodyGroupExpectation(
                            name_prefix="Plate",
                            count=2,
                        ),
                    ),
                ),
            )

    def test_body_group_envelope_count_must_match_group_count(self):
        from cad_verification import VerificationConfigError

        with self.assertRaisesRegex(
            VerificationConfigError,
            "body_envelopes length",
        ):
            SolidCraftBodyGroupExpectation(
                name_prefix="Block",
                count=2,
                body_envelopes=(
                    BodyEnvelope((0, 0, 0), (1, 1, 1)),
                ),
            )

    def test_named_body_must_match_exactly_once(self):
        data = self.measurements()
        duplicate = dict(data["bodies"][0])
        duplicate["name"] = "Plate copy"
        data["bodies"].append(duplicate)
        data["body_count"] = 2

        expectation = SolidCraftModelExpectation(
            named_bodies=(
                SolidCraftBodyExpectation(name_prefix="Plate"),
            )
        )

        with self.assertRaises(VerificationFailure):
            verify_solidcraft_measurements(data, expectation)

    def test_evaluate_command_and_json_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            destination = root / "measurements.json"
            destination.write_text(
                json.dumps(self.measurements()),
                encoding="utf-8",
            )

            with patch.object(solidcraft_module, "run_command") as run:
                result = evaluate_solidcraft_model(model, destination)

            run.assert_called_once_with(
                [
                    "solidcraft-cli",
                    "eval",
                    str(model),
                    "--json-out",
                    str(destination),
                ]
            )
            self.assertEqual(result["body_count"], 1)

    def test_mutate_command_is_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            command = root / "change.json"
            destination = root / "changed.sc"

            with patch.object(solidcraft_module, "run_command") as run:
                mutate_solidcraft_model(model, command, destination)

            run.assert_called_once_with(
                [
                    "solidcraft-cli",
                    "run",
                    str(command),
                    "--in",
                    str(model),
                    "--param-check",
                    "strict",
                    "--save",
                    str(destination),
                ]
            )

    def test_inspection_command_and_json_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            command = root / "inspect.json"
            destination = root / "inspection.json"
            destination.write_text(
                json.dumps([{"flat_size_mm": [80, 40, 2]}]),
                encoding="utf-8",
            )

            with patch.object(solidcraft_module, "run_command") as run:
                result = inspect_solidcraft_model(
                    model,
                    command,
                    destination,
                )

            run.assert_called_once_with(
                [
                    "solidcraft-cli",
                    "run",
                    str(command),
                    "--in",
                    str(model),
                    "--param-check",
                    "strict",
                    "--results",
                    "--json-out",
                    str(destination),
                ]
            )
            self.assertEqual(result[0]["flat_size_mm"], [80, 40, 2])

    def test_invalid_json_is_solidcraft_evidence_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "measurements.json"
            destination.write_text("{broken", encoding="utf-8")

            with patch.object(solidcraft_module, "run_command"):
                with self.assertRaises(SolidCraftEvidenceError):
                    evaluate_solidcraft_model(
                        Path(tmp) / "model.sc",
                        destination,
                    )

    def test_adapter_has_no_forge_or_ci_dependency(self):
        source = inspect.getsource(solidcraft_module).lower()
        forbidden_imports = (
            "import scpf",
            "from scpf",
            "import scons",
            "from scons",
            "cad_ci",
            "tool.cad.ci",
        )
        for value in forbidden_imports:
            with self.subTest(value=value):
                self.assertNotIn(value, source)


if __name__ == "__main__":
    unittest.main()

"""Requirement tests for declarative SolidCraft model verification."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cad_verification import (
    SolidCraftInspection,
    SolidCraftInspectionCheck,
    SolidCraftInspectionSelect,
    SolidCraftMeasurementChangeExpectation,
    SolidCraftModelExpectation,
    SolidCraftSavedDesign,
    SolidCraftVerification,
    VerificationConfigError,
    load_solidcraft_verification,
    run_solidcraft_verification,
    run_solidcraft_verification_file,
)
import cad_verification.adapters.solidcraft as solidcraft_module


def _measurements(length: float = 40.0) -> dict:
    """Return one minimal valid SolidCraft measurement object."""

    half = length / 2.0
    return {
        "body_count": 1,
        "bodies": [
            {
                "name": "Box",
                "bbox": {
                    "min": [-half, -15.0, 0.0],
                    "max": [half, 15.0, 10.0],
                },
            }
        ],
        "params": [
            {"name": "length", "value": length},
            {"name": "width", "value": 30.0},
            {"name": "height", "value": 10.0},
        ],
    }


def _expectation(length: float = 40.0) -> SolidCraftModelExpectation:
    """Return matching model-specific expectation data."""

    half = length / 2.0
    from cad_verification import BodyEnvelope

    return SolidCraftModelExpectation(
        body_count=1,
        body_envelopes=(
            BodyEnvelope(
                (-half, -15.0, 0.0),
                (half, 15.0, 10.0),
                "box",
            ),
        ),
        bounds_tolerance=0.001,
        parameters={
            "length": length,
            "width": 30.0,
            "height": 10.0,
        },
    )


class DeclarativeSolidCraftVerificationTests(unittest.TestCase):
    def test_baseline_definition_produces_report_and_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "input" / "model.sc"
            model.parent.mkdir()
            model.write_text("native", encoding="utf-8")
            output = root / "verification"

            definition = SolidCraftVerification(
                verification_id="simple-box",
                baseline=_expectation(),
                metadata={"title": "Simple box"},
            )

            def evaluate(_model, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                data = _measurements()
                destination.write_text(json.dumps(data), encoding="utf-8")
                return data

            with patch.object(
                solidcraft_module,
                "evaluate_solidcraft_model",
                side_effect=evaluate,
            ) as evaluate_mock:
                report = run_solidcraft_verification(
                    model,
                    output,
                    definition,
                )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(
                [row["id"] for row in report["checks"]],
                ["baseline"],
            )
            self.assertEqual(report["metadata"], {"title": "Simple box"})
            self.assertTrue(
                (output / "baseline" / "measurements.json").is_file()
            )
            self.assertTrue((output / "verification.json").is_file())
            evaluate_mock.assert_called_once_with(
                model.resolve(),
                output.resolve() / "baseline" / "measurements.json",
            )

    def test_saved_design_starts_from_original_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            model.write_text("native", encoding="utf-8")
            command_a = root / "length-50.json"
            command_b = root / "length-60.json"
            command_a.write_text("{}", encoding="utf-8")
            command_b.write_text("{}", encoding="utf-8")
            output = root / "out"

            definition = SolidCraftVerification(
                verification_id="simple-box",
                baseline=_expectation(40.0),
                saved_designs=(
                    SolidCraftSavedDesign(
                        id="length_50",
                        command_path=command_a,
                        expectation=_expectation(50.0),
                    ),
                    SolidCraftSavedDesign(
                        id="length_60",
                        command_path=command_b,
                        expectation=_expectation(60.0),
                    ),
                ),
            )

            mutations = []

            def mutate(source, command, destination):
                mutations.append((source, command, destination))
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text("changed", encoding="utf-8")
                return destination

            def evaluate(source, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                if "length_50" in destination.as_posix():
                    data = _measurements(50.0)
                elif "length_60" in destination.as_posix():
                    data = _measurements(60.0)
                else:
                    data = _measurements(40.0)
                destination.write_text(json.dumps(data), encoding="utf-8")
                return data

            with (
                patch.object(
                    solidcraft_module,
                    "mutate_solidcraft_model",
                    side_effect=mutate,
                ),
                patch.object(
                    solidcraft_module,
                    "evaluate_solidcraft_model",
                    side_effect=evaluate,
                ),
            ):
                report = run_solidcraft_verification(
                    model,
                    output,
                    definition,
                )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(
                [row["id"] for row in report["checks"]],
                [
                    "baseline",
                    "saved_design_length_50",
                    "saved_design_length_60",
                ],
            )
            self.assertEqual(len(mutations), 2)
            self.assertEqual(mutations[0][0], model.resolve())
            self.assertEqual(mutations[1][0], model.resolve())
            self.assertTrue(
                (output / "saved_designs" / "length_50" / "model.sc").is_file()
            )
            self.assertTrue(
                (
                    output
                    / "saved_designs"
                    / "length_60"
                    / "measurements.json"
                ).is_file()
            )

    def test_saved_design_numeric_change_reuses_baseline_measurement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            model.write_text("native", encoding="utf-8")
            command = root / "length-50.json"
            command.write_text("{}", encoding="utf-8")
            output = root / "out"

            definition = SolidCraftVerification(
                verification_id="simple-box",
                baseline=_expectation(40.0),
                saved_designs=(
                    SolidCraftSavedDesign(
                        id="length_50",
                        command_path=command,
                        expectation=_expectation(50.0),
                        changes=(
                            SolidCraftMeasurementChangeExpectation(
                                id="length_changed",
                                path=("params", 0, "value"),
                                minimum_absolute_delta=0.01,
                            ),
                        ),
                    ),
                ),
            )

            def mutate(_source, _command, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text("changed", encoding="utf-8")
                return destination

            evaluations = []

            def evaluate(_source, destination):
                evaluations.append(destination)
                destination.parent.mkdir(parents=True, exist_ok=True)
                data = (
                    _measurements(50.0)
                    if "saved_designs" in destination.as_posix()
                    else _measurements(40.0)
                )
                destination.write_text(json.dumps(data), encoding="utf-8")
                return data

            with (
                patch.object(
                    solidcraft_module,
                    "mutate_solidcraft_model",
                    side_effect=mutate,
                ),
                patch.object(
                    solidcraft_module,
                    "evaluate_solidcraft_model",
                    side_effect=evaluate,
                ),
            ):
                report = run_solidcraft_verification(
                    model,
                    output,
                    definition,
                )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(len(evaluations), 2)
            evidence = report["checks"][1]["evidence"]["changes"][0]
            self.assertEqual(evidence["id"], "length_changed")
            self.assertEqual(evidence["path"], ["params", 0, "value"])
            self.assertEqual(
                evidence["comparison"]["actual"]["baseline"],
                40.0,
            )
            self.assertEqual(
                evidence["comparison"]["actual"]["mutated"],
                50.0,
            )
            self.assertEqual(
                evidence["comparison"]["actual"]["absolute_delta"],
                10.0,
            )

    def test_saved_design_numeric_change_threshold_is_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            model.write_text("native", encoding="utf-8")
            command = root / "length-50.json"
            command.write_text("{}", encoding="utf-8")

            definition = SolidCraftVerification(
                verification_id="simple-box",
                baseline=_expectation(40.0),
                saved_designs=(
                    SolidCraftSavedDesign(
                        id="length_50",
                        command_path=command,
                        expectation=_expectation(50.0),
                        changes=(
                            SolidCraftMeasurementChangeExpectation(
                                id="length_changed",
                                path=("params", 0, "value"),
                                minimum_absolute_delta=10.0,
                            ),
                        ),
                    ),
                ),
            )

            def mutate(_source, _command, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text("changed", encoding="utf-8")

            def evaluate(_source, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                data = (
                    _measurements(50.0)
                    if "saved_designs" in destination.as_posix()
                    else _measurements(40.0)
                )
                destination.write_text(json.dumps(data), encoding="utf-8")
                return data

            with (
                patch.object(
                    solidcraft_module,
                    "mutate_solidcraft_model",
                    side_effect=mutate,
                ),
                patch.object(
                    solidcraft_module,
                    "evaluate_solidcraft_model",
                    side_effect=evaluate,
                ),
            ):
                report = run_solidcraft_verification(
                    model,
                    root / "out",
                    definition,
                )

            self.assertEqual(report["status"], "fail")
            self.assertEqual(
                report["checks"][1]["evidence"]["actual"]["absolute_delta"],
                10.0,
            )

    def test_saved_design_numeric_change_missing_path_is_evidence_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            model.write_text("native", encoding="utf-8")
            command = root / "change.json"
            command.write_text("{}", encoding="utf-8")

            definition = SolidCraftVerification(
                verification_id="simple-box",
                baseline=_expectation(),
                saved_designs=(
                    SolidCraftSavedDesign(
                        id="change",
                        command_path=command,
                        expectation=_expectation(),
                        changes=(
                            SolidCraftMeasurementChangeExpectation(
                                id="missing",
                                path=("bodies", 0, "center_of_mass", 0),
                                minimum_absolute_delta=0.01,
                            ),
                        ),
                    ),
                ),
            )

            def mutate(_source, _command, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text("changed", encoding="utf-8")

            def evaluate(_source, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                data = _measurements()
                destination.write_text(json.dumps(data), encoding="utf-8")
                return data

            with (
                patch.object(
                    solidcraft_module,
                    "mutate_solidcraft_model",
                    side_effect=mutate,
                ),
                patch.object(
                    solidcraft_module,
                    "evaluate_solidcraft_model",
                    side_effect=evaluate,
                ),
            ):
                report = run_solidcraft_verification(
                    model,
                    root / "out",
                    definition,
                )

            self.assertEqual(report["status"], "error")
            self.assertIn(
                "SolidCraftEvidenceError",
                report["checks"][1]["error"],
            )

    def test_saved_design_numeric_change_rejects_invalid_configuration(self):
        with self.assertRaises(VerificationConfigError):
            SolidCraftMeasurementChangeExpectation(
                id="bad",
                path=(),
                minimum_absolute_delta=0.01,
            )
        with self.assertRaises(VerificationConfigError):
            SolidCraftMeasurementChangeExpectation(
                id="bad",
                path=("bodies", -1),
                minimum_absolute_delta=0.01,
            )
        with self.assertRaises(VerificationConfigError):
            SolidCraftMeasurementChangeExpectation(
                id="bad",
                path=("bodies", 0),
                minimum_absolute_delta=-0.01,
            )

    def test_inspection_exact_result_is_verified_and_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            model.write_text("native", encoding="utf-8")
            command = root / "inspect.json"
            command.write_text("{}", encoding="utf-8")
            output = root / "out"

            expected = [{"name": "Box", "grounded": True}]
            definition = SolidCraftVerification(
                verification_id="inspection-model",
                baseline=_expectation(),
                inspections=(
                    SolidCraftInspection(
                        id="components",
                        command_path=command,
                        expected=expected,
                    ),
                ),
            )

            def evaluate(_source, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                data = _measurements()
                destination.write_text(json.dumps(data), encoding="utf-8")
                return data

            def inspect_model(_source, _command, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(
                    json.dumps(expected),
                    encoding="utf-8",
                )
                return expected

            with (
                patch.object(
                    solidcraft_module,
                    "evaluate_solidcraft_model",
                    side_effect=evaluate,
                ),
                patch.object(
                    solidcraft_module,
                    "inspect_solidcraft_model",
                    side_effect=inspect_model,
                ) as inspect_mock,
            ):
                report = run_solidcraft_verification(
                    model,
                    output,
                    definition,
                )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(
                [row["id"] for row in report["checks"]],
                ["baseline", "inspection_components"],
            )
            self.assertTrue(
                (output / "inspections" / "components" / "results.json").is_file()
            )
            inspect_mock.assert_called_once_with(
                model.resolve(),
                command,
                output.resolve()
                / "inspections"
                / "components"
                / "results.json",
            )

    def test_projected_inspection_checks_select_and_compare_stable_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            model.write_text("native", encoding="utf-8")
            command = root / "inspect.json"
            command.write_text("{}", encoding="utf-8")
            output = root / "out"

            result = [
                {
                    "rows": [
                        {"definition": "Panel", "count": 2, "id": 99},
                        {"definition": "Frame", "count": 1, "id": 42},
                    ],
                    "flat_size": [80.0004, 40.0, 2.0],
                    "center": [-20.0004, 0.0003],
                    "metadata": {"rule": "A", "revision": "ignored"},
                }
            ]
            definition = SolidCraftVerification(
                verification_id="inspection-model",
                baseline=_expectation(),
                inspections=(
                    SolidCraftInspection(
                        id="projected",
                        command_path=command,
                        checks=(
                            SolidCraftInspectionCheck(
                                id="root_count",
                                count=1,
                            ),
                            SolidCraftInspectionCheck(
                                id="rows_count",
                                path=(0, "rows"),
                                count=2,
                            ),
                            SolidCraftInspectionCheck(
                                id="frame_count",
                                path=(
                                    0,
                                    "rows",
                                    SolidCraftInspectionSelect(
                                        "definition",
                                        "Frame",
                                    ),
                                    "count",
                                ),
                                expected=1,
                            ),
                            SolidCraftInspectionCheck(
                                id="flat_size",
                                path=(0, "flat_size"),
                                expected=[80.0, 40.0, 2.0],
                                tolerance=0.001,
                            ),
                            SolidCraftInspectionCheck(
                                id="center",
                                path=(0, "center"),
                                expected=[-20.0, 0.0],
                                tolerance=0.001,
                            ),
                            SolidCraftInspectionCheck(
                                id="metadata_count",
                                path=(0, "metadata"),
                                count=2,
                            ),
                        ),
                    ),
                ),
            )

            def evaluate(_source, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                data = _measurements()
                destination.write_text(json.dumps(data), encoding="utf-8")
                return data

            def inspect_model(_source, _command, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(json.dumps(result), encoding="utf-8")
                return result

            with (
                patch.object(
                    solidcraft_module,
                    "evaluate_solidcraft_model",
                    side_effect=evaluate,
                ),
                patch.object(
                    solidcraft_module,
                    "inspect_solidcraft_model",
                    side_effect=inspect_model,
                ),
            ):
                report = run_solidcraft_verification(
                    model,
                    output,
                    definition,
                )

            self.assertEqual(report["status"], "pass")
            evidence = report["checks"][-1]["evidence"]
            self.assertEqual(
                [row["id"] for row in evidence["checks"]],
                [
                    "root_count",
                    "rows_count",
                    "frame_count",
                    "flat_size",
                    "center",
                    "metadata_count",
                ],
            )
            self.assertEqual(
                evidence["checks"][2]["path"][2],
                {
                    "select": {
                        "field": "definition",
                        "value": "Frame",
                    }
                },
            )
            self.assertNotIn("result", evidence)
            self.assertNotIn("revision", json.dumps(evidence))
            self.assertTrue(
                (
                    output
                    / "inspections"
                    / "projected"
                    / "results.json"
                ).is_file()
            )

    def test_projected_inspection_selector_mismatch_is_verification_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            model.write_text("native", encoding="utf-8")
            command = root / "inspect.json"
            command.write_text("{}", encoding="utf-8")
            result = [{"rows": [{"definition": "Panel", "count": 2}]}]

            definition = SolidCraftVerification(
                verification_id="inspection-model",
                baseline=_expectation(),
                inspections=(
                    SolidCraftInspection(
                        id="projected",
                        command_path=command,
                        checks=(
                            SolidCraftInspectionCheck(
                                id="frame",
                                path=(
                                    0,
                                    "rows",
                                    SolidCraftInspectionSelect(
                                        "definition",
                                        "Frame",
                                    ),
                                    "count",
                                ),
                                expected=1,
                            ),
                        ),
                    ),
                ),
            )

            def evaluate(_source, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                data = _measurements()
                destination.write_text(json.dumps(data), encoding="utf-8")
                return data

            def inspect_model(_source, _command, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(json.dumps(result), encoding="utf-8")
                return result

            with (
                patch.object(
                    solidcraft_module,
                    "evaluate_solidcraft_model",
                    side_effect=evaluate,
                ),
                patch.object(
                    solidcraft_module,
                    "inspect_solidcraft_model",
                    side_effect=inspect_model,
                ),
            ):
                report = run_solidcraft_verification(
                    model,
                    root / "out",
                    definition,
                )

            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["checks"][-1]["status"], "fail")

    def test_projected_inspection_missing_path_is_evidence_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            model.write_text("native", encoding="utf-8")
            command = root / "inspect.json"
            command.write_text("{}", encoding="utf-8")
            result = [{"value": 1}]

            definition = SolidCraftVerification(
                verification_id="inspection-model",
                baseline=_expectation(),
                inspections=(
                    SolidCraftInspection(
                        id="projected",
                        command_path=command,
                        checks=(
                            SolidCraftInspectionCheck(
                                id="missing",
                                path=(0, "missing"),
                                expected=1,
                            ),
                        ),
                    ),
                ),
            )

            def evaluate(_source, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                data = _measurements()
                destination.write_text(json.dumps(data), encoding="utf-8")
                return data

            def inspect_model(_source, _command, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(json.dumps(result), encoding="utf-8")
                return result

            with (
                patch.object(
                    solidcraft_module,
                    "evaluate_solidcraft_model",
                    side_effect=evaluate,
                ),
                patch.object(
                    solidcraft_module,
                    "inspect_solidcraft_model",
                    side_effect=inspect_model,
                ),
            ):
                report = run_solidcraft_verification(
                    model,
                    root / "out",
                    definition,
                )

            self.assertEqual(report["status"], "error")
            self.assertIn(
                "SolidCraftEvidenceError",
                report["checks"][-1]["error"],
            )

    def test_projected_inspection_rejects_ambiguous_configuration(self):
        with self.assertRaisesRegex(
            VerificationConfigError,
            "exactly one",
        ):
            SolidCraftInspectionCheck(
                id="bad",
                expected=1,
                count=1,
            )

        with self.assertRaisesRegex(
            VerificationConfigError,
            "mutually exclusive",
        ):
            SolidCraftInspection(
                id="bad",
                command_path=Path("inspect.json"),
                expected={"value": 1},
                checks=(
                    SolidCraftInspectionCheck(
                        id="value",
                        path=("value",),
                        expected=1,
                    ),
                ),
            )

    def test_inspection_mismatch_is_normal_verification_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            model.write_text("native", encoding="utf-8")
            command = root / "inspect.json"
            command.write_text("{}", encoding="utf-8")

            definition = SolidCraftVerification(
                verification_id="inspection-model",
                baseline=_expectation(),
                inspections=(
                    SolidCraftInspection(
                        id="result",
                        command_path=command,
                        expected={"value": 2},
                    ),
                ),
            )

            def evaluate(_source, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                data = _measurements()
                destination.write_text(json.dumps(data), encoding="utf-8")
                return data

            def inspect_model(_source, _command, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text('{"value": 3}', encoding="utf-8")
                return {"value": 3}

            with (
                patch.object(
                    solidcraft_module,
                    "evaluate_solidcraft_model",
                    side_effect=evaluate,
                ),
                patch.object(
                    solidcraft_module,
                    "inspect_solidcraft_model",
                    side_effect=inspect_model,
                ),
            ):
                report = run_solidcraft_verification(
                    model,
                    root / "out",
                    definition,
                )

            self.assertEqual(report["status"], "fail")
            self.assertEqual(
                report["checks"][-1]["id"],
                "inspection_result",
            )

    def test_inspection_can_retain_result_without_exact_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model.sc"
            model.write_text("native", encoding="utf-8")
            command = root / "inspect.json"
            command.write_text("{}", encoding="utf-8")

            definition = SolidCraftVerification(
                verification_id="inspection-model",
                baseline=_expectation(),
                inspections=(
                    SolidCraftInspection(
                        id="capture",
                        command_path=command,
                    ),
                ),
            )

            def evaluate(_source, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                data = _measurements()
                destination.write_text(json.dumps(data), encoding="utf-8")
                return data

            def inspect_model(_source, _command, destination):
                result = None
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text("null", encoding="utf-8")
                return result

            with (
                patch.object(
                    solidcraft_module,
                    "evaluate_solidcraft_model",
                    side_effect=evaluate,
                ),
                patch.object(
                    solidcraft_module,
                    "inspect_solidcraft_model",
                    side_effect=inspect_model,
                ),
            ):
                report = run_solidcraft_verification(
                    model,
                    root / "out",
                    definition,
                )

            self.assertEqual(report["status"], "pass")

    def test_definition_rejects_invalid_and_duplicate_ids(self):
        with self.assertRaises(VerificationConfigError):
            SolidCraftSavedDesign(
                id="Not valid",
                command_path=Path("change.json"),
                expectation=_expectation(),
            )

        with self.assertRaises(VerificationConfigError):
            SolidCraftVerification(
                verification_id="simple-box",
                baseline=_expectation(),
                saved_designs=(
                    SolidCraftSavedDesign(
                        id="same",
                        command_path=Path("one.json"),
                        expectation=_expectation(),
                    ),
                    SolidCraftSavedDesign(
                        id="same",
                        command_path=Path("two.json"),
                        expectation=_expectation(),
                    ),
                ),
            )

    def test_runner_has_no_forge_or_ci_dependency(self):
        source = inspect.getsource(solidcraft_module).lower()
        forbidden = (
            "import scpf",
            "from scpf",
            "cad_ci_item",
            "cad_ci_output",
            "import scons",
            "from scons",
            "tool.cad.ci",
        )
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, source)


    def test_definition_file_loader_and_runner_remove_consumer_launcher_glue(self):
        """Model-local VERIFICATION config loads and delegates to the existing runner."""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            definition_path = root / "verify.py"
            definition_path.write_text(
                "from cad_verification import (\n"
                "    SolidCraftModelExpectation, SolidCraftVerification,\n"
                ")\n"
                "VERIFICATION = SolidCraftVerification(\n"
                "    verification_id='file-test',\n"
                "    baseline=SolidCraftModelExpectation(body_count=1),\n"
                ")\n",
                encoding="utf-8",
            )

            definition = load_solidcraft_verification(definition_path)
            self.assertIsInstance(definition, SolidCraftVerification)
            self.assertEqual(definition.verification_id, "file-test")

            model = root / "model.sc"
            output = root / "output"
            with patch.object(
                solidcraft_module,
                "run_solidcraft_verification",
                return_value={"status": "pass"},
            ) as runner:
                result = run_solidcraft_verification_file(
                    model,
                    output,
                    definition_path,
                )

            self.assertEqual(result, {"status": "pass"})
            called_model, called_output, called_definition = runner.call_args.args
            self.assertEqual(called_model, model)
            self.assertEqual(called_output, output)
            self.assertIsInstance(called_definition, SolidCraftVerification)
            self.assertEqual(called_definition.verification_id, "file-test")

    def test_definition_loader_rejects_missing_verification_export(self):
        """A Python file is configuration only when it exports the required object."""

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "verify.py"
            path.write_text("VALUE = 1\n", encoding="utf-8")
            with self.assertRaisesRegex(
                VerificationConfigError,
                "must export VERIFICATION",
            ):
                load_solidcraft_verification(path)


if __name__ == "__main__":
    unittest.main()

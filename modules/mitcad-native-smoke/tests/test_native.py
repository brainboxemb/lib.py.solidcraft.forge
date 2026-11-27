"""Run the first Forge model through the exact Mitcad v0.70.0 release."""

from __future__ import annotations

import hashlib
import json
from math import asin, pi, sqrt
import os
from pathlib import Path
import stat
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "cadlib/src"))
sys.path.insert(0, str(ROOT / "modules/mitcad-reference/src"))
sys.path.insert(0, str(ROOT / "modules/verification/src"))

from cad_library_mitcad_reference import capture_runtime, git_blob_sha
from scpf import Anchor, Axis, AxisLine, Box, Circle2D, Cone, Edges, Faces, Parameter, Polygon2D, Sketch, Sphere
from scpf.backends.mitcad import compile_ir as compile_mitcad_ir
from scpf.backends.mitcad_headless import run_document, run_saved_configuration
from scpf.ir import normalize_shape
from scpf.runner import run_script
from cad_verification.geometry import (
    load_geometry_contract,
    run_mesh_geometry_verification,
)


VERSION = "0.70.0"
ASSET_URL = (
    "https://github.com/mitcad/Mitcad/releases/download/v0.70.0/"
    "Mitcad-0.70.0-x86_64.AppImage"
)
ASSET_SHA256 = (
    "9e1e8919a0ccd8f48bba4b3d443c70fb92f44d6104357fc00c25bf4c18379551"
)
SOURCE_REFERENCE_BLOB = "40240776bc6885e228bf2fbd8e2534875aa61b85"
RUNTIME_REFERENCE_BLOB = "c839084ba223e814370a55c761644da362fabc93"
SIMPLE_BOX = ROOT / "models/simple-box/scpf/model.py"
NEGATIVE_CIRCLE = ROOT / "models/circle-negative-extrude/scpf/model.py"
TOPOLOGY_BOX = ROOT / "models/topology-face-boundary-box/scpf/model.py"
SHIFTED_AXIS_REVOLVE = ROOT / "models/shifted-axis-revolve/scpf/model.py"
PRIMITIVE_CSG = ROOT / "models/primitive-csg/scpf/model.py"


def ensure_appimage_runtime() -> None:
    """Install Mitcad's documented Ubuntu AppImage runtime libraries."""
    packages = [
        "libgl1",
        "libopengl0",
        "libegl1",
        "libglx-mesa0",
        "libgl1-mesa-dri",
        "libfontconfig1",
        "libfreetype6",
        "libdbus-1-3",
        "libglib2.0-0t64",
        "libx11-6",
        "libx11-xcb1",
        "libxext6",
        "libxrender1",
        "libxi6",
        "libsm6",
        "libice6",
        "libxkbcommon0",
        "libxkbcommon-x11-0",
        "libxcb-cursor0",
        "libxcb-icccm4",
        "libxcb-image0",
        "libxcb-keysyms1",
        "libxcb-render-util0",
        "libxcb-xinerama0",
        "libxcb-xkb1",
        "libxcb-shape0",
        "libxcb-randr0",
        "libwayland-client0",
        "libwayland-cursor0",
        "libwayland-egl1",
    ]
    subprocess.run(["sudo", "apt-get", "update", "-qq"], check=True)
    subprocess.run(
        ["sudo", "apt-get", "install", "-y", "-qq", *packages],
        check=True,
    )


def download_asset(destination: Path) -> None:
    request = Request(
        ASSET_URL,
        headers={"User-Agent": "Forge-Mitcad-Native-Smoke/1"},
    )
    digest = hashlib.sha256()
    with urlopen(request, timeout=120) as source, destination.open("wb") as out:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            out.write(chunk)
    actual = digest.hexdigest()
    if actual != ASSET_SHA256:
        raise AssertionError(
            f"Mitcad v{VERSION} AppImage digest mismatch: {actual}"
        )
    destination.chmod(
        destination.stat().st_mode
        | stat.S_IXUSR
        | stat.S_IXGRP
        | stat.S_IXOTH
    )


def cli_wrapper(root: Path, appimage: Path) -> Path:
    wrapper = root / "mitcad-cli"
    wrapper.write_text(
        "#!/bin/sh\n"
        "export APPIMAGE_EXTRACT_AND_RUN=1\n"
        "export QT_QPA_PLATFORM=offscreen\n"
        "exec " + repr(str(appimage)) + " cli \"$@\"\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    return wrapper


class MitcadNativeSmokeTests(unittest.TestCase):
    def test_simple_box_executes_in_exact_v070_release(self):
        with tempfile.TemporaryDirectory(prefix="forge-mitcad-native-") as tmp:
            root = Path(tmp)
            ensure_appimage_runtime()
            appimage = root / "Mitcad-0.70.0-x86_64.AppImage"
            download_asset(appimage)
            executable = cli_wrapper(root, appimage)

            cli_version, reference, catalog = capture_runtime(
                str(executable),
                workspace=root / "reference-workspace",
            )
            self.assertIn(VERSION, cli_version)
            self.assertEqual(
                git_blob_sha(reference),
                RUNTIME_REFERENCE_BLOB,
            )
            self.assertIn("add_feature", catalog["commands"])
            self.assertIn("box", catalog["features"])

            evidence = ROOT / "build/qualification/mitcad-v0.70.0"
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "runtime-commands.md").write_text(
                reference,
                encoding="utf-8",
            )
            (evidence / "commands.json").write_text(
                json.dumps(catalog, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            simple_box = run_document(
                run_script(SIMPLE_BOX, backend="mitcad"),
                save=root / "out/simple-box.mitcad",
                export=root / "out/simple-box.stl",
                executable=str(executable),
                work_dir=root / "simple-box-workspace",
            )

            self.assertEqual(simple_box["completed"], 4)
            self.assertEqual(len(simple_box["bodies"]), 1)
            box_body = simple_box["bodies"][0]
            self.assertEqual(box_body["kind"], "solid")
            self.assertAlmostEqual(box_body["volume"], 12000.0, places=5)
            for actual, expected in zip(
                box_body["bbox"]["min"],
                [-20.0, -15.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                box_body["bbox"]["max"],
                [20.0, 15.0, 10.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            circle = run_document(
                run_script(NEGATIVE_CIRCLE, backend="mitcad"),
                save=root / "out/circle-negative-extrude.mitcad",
                export=root / "out/circle-negative-extrude.stl",
                executable=str(executable),
                work_dir=root / "circle-workspace",
            )
            self.assertEqual(circle["completed"], 4)
            self.assertEqual(len(circle["bodies"]), 1)
            circle_body = circle["bodies"][0]
            self.assertEqual(circle_body["kind"], "solid")
            self.assertAlmostEqual(
                circle_body["volume"],
                3000.0 * 3.141592653589793,
                places=4,
            )
            for actual, expected in zip(
                circle_body["bbox"]["min"],
                [-10.0, -10.0, -30.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                circle_body["bbox"]["max"],
                [10.0, 10.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            for model_id in ("simple-box", "circle-negative-extrude"):
                source_stl = root / "out" / f"{model_id}.stl"
                retained_stl = evidence / f"{model_id}.stl"
                shutil.copy2(source_stl, retained_stl)
                report = run_mesh_geometry_verification(
                    retained_stl,
                    evidence / "verification" / model_id,
                    load_geometry_contract(
                        ROOT / "models" / model_id / "verification/geometry.json"
                    ),
                    verification_id=f"mitcad-{model_id}-geometry",
                )
                self.assertEqual(report["status"], "pass", report)

            topology = run_document(
                run_script(TOPOLOGY_BOX, backend="mitcad"),
                save=root / "out/topology-face-boundary-box.mitcad",
                export=root / "out/topology-face-boundary-box.stl",
                executable=str(executable),
                work_dir=root / "topology-workspace",
            )
            self.assertEqual(topology["completed"], 2)
            self.assertEqual(len(topology["bodies"]), 1)
            topology_body = topology["bodies"][0]
            self.assertEqual(topology_body["kind"], "solid")
            self.assertAlmostEqual(
                topology_body["volume"],
                28410.666666666664,
                places=4,
            )
            for actual, expected in zip(
                topology_body["bbox"]["min"],
                [-30.0, -20.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                topology_body["bbox"]["max"],
                [30.0, 20.0, 12.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            polygon_width = Parameter("polygon_width", 10)
            polygon_height = Parameter("polygon_height", 4)
            polygon_half = polygon_width / 2
            polygon_crown = polygon_height + 1
            with Sketch(name="ParametricPolygon", plane="XZ") as polygon_profile:
                Polygon2D(
                    [
                        (0, 0),
                        (0, polygon_height),
                        (polygon_half, polygon_crown),
                        (polygon_width, 0),
                    ],
                    plane="XZ",
                )
            polygon_document = compile_mitcad_ir(
                normalize_shape(polygon_profile.revolve(axis=Axis.X)),
                "ParametricPolygonRevolve",
            )
            polygon_sketch = polygon_document["commands"][-2]["def"]
            self.assertEqual(len(polygon_sketch["dimensions"]), 8)
            self.assertEqual(
                [dimension["type"] for dimension in polygon_sketch["dimensions"]],
                [
                    "horizontal_distance", "vertical_distance",
                    "horizontal_distance", "vertical_distance",
                    "horizontal_distance", "vertical_distance",
                    "horizontal_distance", "vertical_distance",
                ],
            )
            self.assertTrue(polygon_sketch["entities"][0]["fixed"])

            polygon_native = run_document(
                polygon_document,
                save=root / "out/parameterized-polygon-revolve.mitcad",
                export=root / "out/parameterized-polygon-revolve.stl",
                executable=str(executable),
                work_dir=root / "parameterized-polygon-revolve-workspace",
            )
            self.assertEqual(len(polygon_native["bodies"]), 1)
            polygon_body = polygon_native["bodies"][0]
            self.assertEqual(polygon_body["kind"], "solid")
            self.assertAlmostEqual(
                polygon_body["volume"],
                pi * (430.0 / 3.0),
                places=3,
            )
            for actual, expected in zip(
                polygon_body["bbox"]["min"],
                [0.0, -5.0, -5.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                polygon_body["bbox"]["max"],
                [10.0, 5.0, 5.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            mixed_shared = Parameter("mixed_shared", 4)
            with Sketch(name="MixedRoleRevolve", plane="XZ") as mixed_profile:
                Polygon2D(
                    [
                        (0, 0),
                        (0, mixed_shared),
                        (10, mixed_shared),
                        (10, 0),
                    ],
                    plane="XZ",
                )
            mixed_document = compile_mitcad_ir(
                normalize_shape(
                    mixed_profile.revolve(
                        axis=Axis.X,
                        angle=mixed_shared,
                    )
                ),
                "MixedRoleRevolve",
            )
            self.assertEqual(
                mixed_document["commands"][0],
                {
                    "cmd": "add_parameter",
                    "name": "mixed_shared",
                    "unit": "",
                    "expression": "4",
                },
            )
            mixed_sketch = mixed_document["commands"][-2]["def"]
            self.assertIn(
                "mixed_shared * 1 mm",
                [
                    dimension["value"]
                    for dimension in mixed_sketch["dimensions"]
                ],
            )
            self.assertEqual(
                mixed_document["commands"][-1]["def"]["extent"],
                {
                    "type": "angle",
                    "angle": "mixed_shared * 1 deg",
                },
            )

            mixed_native = run_document(
                mixed_document,
                save=root / "out/mixed-role-revolve.mitcad",
                export=root / "out/mixed-role-revolve.stl",
                executable=str(executable),
                work_dir=root / "mixed-role-revolve-workspace",
            )
            self.assertEqual(len(mixed_native["bodies"]), 1)
            mixed_body = mixed_native["bodies"][0]
            self.assertEqual(mixed_body["kind"], "solid")
            self.assertAlmostEqual(
                mixed_body["volume"],
                16.0 * pi / 9.0,
                places=3,
            )
            self.assertAlmostEqual(mixed_body["bbox"]["min"][0], 0.0, places=5)
            self.assertAlmostEqual(mixed_body["bbox"]["max"][0], 10.0, places=5)

            mixed_expression_shared = Parameter(
                "mixed_expression_shared",
                4,
            )
            mixed_expression_height = mixed_expression_shared + 1
            with Sketch(
                name="MixedRoleExpression",
                plane="XZ",
            ) as mixed_expression_profile:
                Polygon2D(
                    [
                        (0, 0),
                        (0, mixed_expression_height),
                        (10, mixed_expression_height),
                        (10, 0),
                    ],
                    plane="XZ",
                )
            mixed_expression_document = compile_mitcad_ir(
                normalize_shape(
                    mixed_expression_profile.revolve(
                        axis=Axis.X,
                        angle=mixed_expression_shared,
                    )
                ),
                "MixedRoleExpression",
            )
            self.assertEqual(
                mixed_expression_document["commands"][0],
                {
                    "cmd": "add_parameter",
                    "name": "mixed_expression_shared",
                    "unit": "",
                    "expression": "4",
                },
            )
            mixed_expression_sketch = (
                mixed_expression_document["commands"][-2]["def"]
            )
            self.assertIn(
                "(mixed_expression_shared * 1 mm) + (1 mm)",
                [
                    dimension["value"]
                    for dimension in mixed_expression_sketch["dimensions"]
                ],
            )
            self.assertEqual(
                mixed_expression_document["commands"][-1]["def"]["extent"],
                {
                    "type": "angle",
                    "angle": "mixed_expression_shared * 1 deg",
                },
            )

            mixed_expression_native = run_document(
                mixed_expression_document,
                save=root / "out/mixed-role-expression-revolve.mitcad",
                export=root / "out/mixed-role-expression-revolve.stl",
                executable=str(executable),
                work_dir=root / "mixed-role-expression-revolve-workspace",
            )
            self.assertEqual(len(mixed_expression_native["bodies"]), 1)
            mixed_expression_body = mixed_expression_native["bodies"][0]
            self.assertEqual(mixed_expression_body["kind"], "solid")
            self.assertAlmostEqual(
                mixed_expression_body["volume"],
                25.0 * pi / 9.0,
                places=3,
            )
            self.assertAlmostEqual(
                mixed_expression_body["bbox"]["min"][0],
                0.0,
                places=5,
            )
            self.assertAlmostEqual(
                mixed_expression_body["bbox"]["max"][0],
                10.0,
                places=5,
            )

            asymmetric_chamfer_document = compile_mitcad_ir(
                normalize_shape(
                    Box(
                        60,
                        40,
                        12,
                        anchor=Anchor.BOTTOM,
                    ).chamfer(
                        0.18,
                        distance2=0.65,
                        edges=Edges.from_faces(Faces.TOP),
                    )
                ),
                "AsymmetricChamfer",
            )
            asymmetric_stage = asymmetric_chamfer_document["replay"][0]
            self.assertEqual(
                asymmetric_stage["bind_face_boundary_edges"]["face_name"],
                "reference_face",
            )
            asymmetric_set = (
                asymmetric_stage["commands"][0]["def"]["sets"][0]
            )
            self.assertEqual(
                asymmetric_set["size"],
                {
                    "type": "two_distances",
                    "distance1": 0.18,
                    "distance2": 0.65,
                },
            )
            self.assertEqual(
                asymmetric_set["reference_face"],
                {"$mitcad_bind": "reference_face"},
            )

            asymmetric_chamfer_native = run_document(
                asymmetric_chamfer_document,
                save=root / "out/asymmetric-chamfer.mitcad",
                export=root / "out/asymmetric-chamfer.stl",
                executable=str(executable),
                work_dir=root / "asymmetric-chamfer-workspace",
            )
            self.assertEqual(len(asymmetric_chamfer_native["bodies"]), 1)
            asymmetric_chamfer_body = asymmetric_chamfer_native["bodies"][0]
            self.assertEqual(asymmetric_chamfer_body["kind"], "solid")
            self.assertEqual(
                asymmetric_chamfer_native["bindings"]["reference_face"],
                "F1:top",
            )
            self.assertAlmostEqual(
                asymmetric_chamfer_body["volume"],
                28788.32808,
                places=3,
            )
            for actual, expected in zip(
                asymmetric_chamfer_body["bbox"]["min"],
                [-30.0, -20.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                asymmetric_chamfer_body["bbox"]["max"],
                [30.0, 20.0, 12.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            fillet_cone_document = compile_mitcad_ir(
                normalize_shape(
                    Box(
                        50,
                        40,
                        20,
                        anchor=Anchor.BOTTOM,
                    ).fillet(
                        2,
                        edges=Edges.VERTICAL,
                    )
                    + Cone(
                        d=18,
                        top_d=10,
                        h=8,
                        anchor=Anchor.BOTTOM,
                    ).at(
                        0,
                        0,
                        18,
                        anchor=Anchor.BOTTOM,
                    )
                ),
                "FilletConeBoolean",
            )
            self.assertEqual(
                [
                    row["def"]["type"]
                    for row in fillet_cone_document["commands"]
                    if row["cmd"] == "add_feature"
                ],
                ["box"],
            )
            fillet_cone_stage = fillet_cone_document["replay"][0]
            self.assertEqual(
                fillet_cone_stage["bind_parallel_edges"],
                {
                    "name": "parallel_edges",
                    "body": "body",
                    "axis": "Z",
                    "expected": 4,
                },
            )
            self.assertEqual(
                [
                    row["def"]["type"]
                    for row in fillet_cone_stage["commands"]
                    if row["cmd"] == "add_feature"
                ],
                ["fillet", "construction_plane", "cone"],
            )
            self.assertEqual(
                fillet_cone_stage["commands"][-1]["def"]["operation"],
                "join",
            )

            fillet_cone_native = run_document(
                fillet_cone_document,
                save=root / "out/fillet-cone-boolean.mitcad",
                export=root / "out/fillet-cone-boolean.stl",
                executable=str(executable),
                work_dir=root / "fillet-cone-boolean-workspace",
            )
            self.assertEqual(len(fillet_cone_native["bodies"]), 1)
            fillet_cone_body = fillet_cone_native["bodies"][0]
            self.assertEqual(fillet_cone_body["kind"], "solid")
            self.assertEqual(
                len(fillet_cone_native["bindings"]["parallel_edges"]),
                4,
            )
            self.assertAlmostEqual(
                fillet_cone_body["volume"],
                39680.0 + 338.0 * pi,
                places=3,
            )
            for actual, expected in zip(
                fillet_cone_body["bbox"]["min"],
                [-25.0, -20.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                fillet_cone_body["bbox"]["max"],
                [25.0, 20.0, 26.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            top_face_fillet_document = compile_mitcad_ir(
                normalize_shape(
                    Box(
                        60,
                        40,
                        12,
                        anchor=Anchor.BOTTOM,
                    ).fillet(
                        2,
                        edges=Edges.from_faces(Faces.TOP),
                    )
                ),
                "TopFaceBoundaryFillet",
            )
            self.assertEqual(
                [
                    row["def"]["type"]
                    for row in top_face_fillet_document["commands"]
                    if row["cmd"] == "add_feature"
                ],
                ["box"],
            )
            top_face_fillet_stage = top_face_fillet_document["replay"][0]
            self.assertNotIn(
                "bind_parallel_edges",
                top_face_fillet_stage,
            )
            self.assertEqual(
                top_face_fillet_stage["bind_face_boundary_edges"],
                {
                    "name": "edges",
                    "body": "body",
                    "face": {
                        "surface": "plane",
                        "normal": [0, 0, 1],
                        "normal_tolerance": 1e-6,
                    },
                },
            )

            top_face_fillet_native = run_document(
                top_face_fillet_document,
                save=root / "out/top-face-boundary-fillet.mitcad",
                export=root / "out/top-face-boundary-fillet.stl",
                executable=str(executable),
                work_dir=root / "top-face-boundary-fillet-workspace",
            )
            self.assertEqual(len(top_face_fillet_native["bodies"]), 1)
            top_face_fillet_body = top_face_fillet_native["bodies"][0]
            self.assertEqual(top_face_fillet_body["kind"], "solid")
            self.assertEqual(
                len(top_face_fillet_native["bindings"]["edges"]),
                4,
            )
            self.assertAlmostEqual(
                top_face_fillet_body["volume"],
                28631.38638124875,
                places=6,
            )
            for actual, expected in zip(
                top_face_fillet_body["bbox"]["min"],
                [-30.0, -20.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                top_face_fillet_body["bbox"]["max"],
                [30.0, 20.0, 12.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            placed_frustum_document = compile_mitcad_ir(
                normalize_shape(
                    Cone(
                        d=18,
                        top_d=10,
                        h=8,
                        anchor=Anchor.BOTTOM,
                    ).at(
                        0,
                        0,
                        18,
                        anchor=Anchor.BOTTOM,
                    )
                ),
                "PlacedFrustum",
            )
            self.assertEqual(
                [
                    row["def"]["type"]
                    for row in placed_frustum_document["commands"]
                    if row["cmd"] == "add_feature"
                ],
                ["construction_plane", "cone"],
            )
            placed_frustum_native = run_document(
                placed_frustum_document,
                save=root / "out/placed-frustum.mitcad",
                export=root / "out/placed-frustum.stl",
                executable=str(executable),
                work_dir=root / "placed-frustum-workspace",
            )
            self.assertEqual(len(placed_frustum_native["bodies"]), 1)
            placed_frustum_body = placed_frustum_native["bodies"][0]
            self.assertEqual(placed_frustum_body["kind"], "solid")
            self.assertAlmostEqual(
                placed_frustum_body["volume"],
                1208.0 * pi / 3.0,
                places=3,
            )
            for actual, expected in zip(
                placed_frustum_body["bbox"]["min"],
                [-9.0, -9.0, 18.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                placed_frustum_body["bbox"]["max"],
                [9.0, 9.0, 26.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            shifted_sphere_csg_document = compile_mitcad_ir(
                normalize_shape(
                    Box(30, 30, 30, anchor=Anchor.BOTTOM)
                    - Sphere(5).move(z=15)
                ),
                "ShiftedSphereCsg",
            )
            shifted_csg_features = [
                row
                for row in shifted_sphere_csg_document["commands"]
                if row["cmd"] == "add_feature"
            ]
            self.assertEqual(
                [row["def"]["type"] for row in shifted_csg_features],
                ["box", "construction_plane", "sphere"],
            )
            self.assertEqual(
                shifted_csg_features[1]["as"],
                "csg_plane_root_tool",
            )
            self.assertEqual(
                shifted_csg_features[2]["def"]["plane"],
                {"ref": "csg_plane_root_tool.uid"},
            )
            self.assertEqual(
                shifted_csg_features[2]["def"]["operation"],
                "cut",
            )

            shifted_sphere_csg_native = run_document(
                shifted_sphere_csg_document,
                save=root / "out/shifted-sphere-csg.mitcad",
                export=root / "out/shifted-sphere-csg.stl",
                executable=str(executable),
                work_dir=root / "shifted-sphere-csg-workspace",
            )
            self.assertEqual(len(shifted_sphere_csg_native["bodies"]), 1)
            shifted_sphere_csg_body = shifted_sphere_csg_native["bodies"][0]
            self.assertEqual(shifted_sphere_csg_body["kind"], "solid")
            self.assertAlmostEqual(
                shifted_sphere_csg_body["volume"],
                27000.0 - 500.0 * pi / 3.0,
                places=3,
            )
            for actual, expected in zip(
                shifted_sphere_csg_body["bbox"]["min"],
                [-15.0, -15.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                shifted_sphere_csg_body["bbox"]["max"],
                [15.0, 15.0, 30.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            offset_cone_csg_document = compile_mitcad_ir(
                normalize_shape(
                    Box(30, 30, 30, anchor=Anchor.BOTTOM)
                    - Cone(
                        d=10,
                        top_d=0,
                        h=20,
                        anchor=Anchor.BOTTOM,
                    ).at(
                        0,
                        0,
                        5,
                        anchor=Anchor.BOTTOM,
                    )
                ),
                "OffsetConeCsg",
            )
            offset_cone_csg_features = [
                row
                for row in offset_cone_csg_document["commands"]
                if row["cmd"] == "add_feature"
            ]
            self.assertEqual(
                [row["def"]["type"] for row in offset_cone_csg_features],
                ["box", "construction_plane", "cone"],
            )
            self.assertEqual(
                offset_cone_csg_features[1]["as"],
                "csg_plane_root_tool",
            )
            self.assertEqual(
                offset_cone_csg_features[1]["def"]["definition"]["distance"],
                5,
            )
            self.assertEqual(
                offset_cone_csg_features[2]["def"]["plane"],
                {"ref": "csg_plane_root_tool.uid"},
            )
            self.assertEqual(
                offset_cone_csg_features[2]["def"]["operation"],
                "cut",
            )

            offset_cone_csg_native = run_document(
                offset_cone_csg_document,
                save=root / "out/offset-cone-csg.mitcad",
                export=root / "out/offset-cone-csg.stl",
                executable=str(executable),
                work_dir=root / "offset-cone-csg-workspace",
            )
            self.assertEqual(len(offset_cone_csg_native["bodies"]), 1)
            offset_cone_csg_body = offset_cone_csg_native["bodies"][0]
            self.assertEqual(offset_cone_csg_body["kind"], "solid")
            self.assertAlmostEqual(
                offset_cone_csg_body["volume"],
                27000.0 - 500.0 * pi / 3.0,
                places=3,
            )
            for actual, expected in zip(
                offset_cone_csg_body["bbox"]["min"],
                [-15.0, -15.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                offset_cone_csg_body["bbox"]["max"],
                [15.0, 15.0, 30.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            sphere_radius = Parameter("sphere_radius", 10)
            sphere_top_z = Parameter("sphere_top_z", 25)
            placed_sphere_document = compile_mitcad_ir(
                normalize_shape(
                    Sphere(sphere_radius).at(
                        3,
                        4,
                        sphere_top_z,
                        anchor=Anchor.TOP,
                    )
                ),
                "PlacedSphere",
            )
            placed_sphere_plane = next(
                row
                for row in placed_sphere_document["commands"]
                if row.get("def", {}).get("type") == "construction_plane"
            )
            placed_sphere_def = placed_sphere_document["commands"][-1]["def"]
            plane_distance = str(
                placed_sphere_plane["def"]["definition"]["distance"]
            )
            self.assertIn("sphere_top_z", plane_distance)
            self.assertIn("sphere_radius", plane_distance)
            self.assertEqual(
                placed_sphere_def["plane"],
                {"ref": "sphere_plane.uid"},
            )
            self.assertEqual(placed_sphere_def["center"], [3, 4])
            self.assertIn(
                "sphere_radius",
                str(placed_sphere_def["diameter"]),
            )

            placed_sphere_native = run_document(
                placed_sphere_document,
                save=root / "out/placed-sphere.mitcad",
                export=root / "out/placed-sphere.stl",
                executable=str(executable),
                work_dir=root / "placed-sphere-workspace",
            )
            self.assertEqual(len(placed_sphere_native["bodies"]), 1)
            placed_sphere_body = placed_sphere_native["bodies"][0]
            self.assertEqual(placed_sphere_body["kind"], "solid")
            self.assertAlmostEqual(
                placed_sphere_body["volume"],
                4000.0 * pi / 3.0,
                places=3,
            )
            for actual, expected in zip(
                placed_sphere_body["bbox"]["min"],
                [-7.0, -6.0, 5.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                placed_sphere_body["bbox"]["max"],
                [13.0, 14.0, 25.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            with Sketch(name="ThreeCircleRegion", plane="XY") as three_circle:
                Circle2D(d=10)
                Circle2D(d=8)
                Circle2D(d=6)
            three_circle_document = compile_mitcad_ir(
                normalize_shape(
                    three_circle.extrude(
                        20,
                        profiles=[(4.5, 0)],
                        exact_regions=True,
                    )
                ),
                "ThreeCircleRegion",
            )
            three_circle_sketch = three_circle_document["commands"][-2]["def"]
            three_circle_extrude = three_circle_document["commands"][-1]["def"]
            self.assertEqual(
                [entity["type"] for entity in three_circle_sketch["entities"]],
                ["point", "circle", "circle", "circle"],
            )
            self.assertEqual(
                [dimension["value"] for dimension in three_circle_sketch["dimensions"]],
                [10, 8, 6],
            )
            self.assertEqual(
                three_circle_extrude["profiles"],
                [{"sketch": {"ref": "sk.uid"}, "point": [4.5, 0.0]}],
            )

            three_circle_native = run_document(
                three_circle_document,
                save=root / "out/three-circle-exact-region.mitcad",
                export=root / "out/three-circle-exact-region.stl",
                executable=str(executable),
                work_dir=root / "three-circle-exact-region-workspace",
            )
            self.assertEqual(len(three_circle_native["bodies"]), 1)
            three_circle_body = three_circle_native["bodies"][0]
            self.assertEqual(three_circle_body["kind"], "solid")
            self.assertAlmostEqual(
                three_circle_body["volume"],
                180.0 * pi,
                places=3,
            )
            for actual, expected in zip(
                three_circle_body["bbox"]["min"],
                [-5.0, -5.0, 0.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                three_circle_body["bbox"]["max"],
                [5.0, 5.0, 20.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            extrude_width = Parameter("extrude_width", 20)
            with Sketch(name="ParametricExtrude", plane="XY") as extrude_profile:
                Polygon2D(
                    [
                        (0, 0),
                        (0, 30),
                        (extrude_width, 30),
                        (extrude_width, 0),
                    ],
                    plane="XY",
                )
            extrude_document = compile_mitcad_ir(
                normalize_shape(extrude_profile.extrude(10, sym=True)),
                "ParametricPolygonExtrude",
            )
            extrude_sketch = extrude_document["commands"][-2]["def"]
            self.assertEqual(
                [constraint["type"] for constraint in extrude_sketch["constraints"]],
                ["vertical", "horizontal", "vertical", "horizontal"],
            )
            self.assertEqual(
                [dimension["type"] for dimension in extrude_sketch["dimensions"]],
                ["length", "length"],
            )
            self.assertIn(
                "extrude_width",
                [dimension["value"] for dimension in extrude_sketch["dimensions"]],
            )

            extrude_native = run_document(
                extrude_document,
                save=root / "out/parameterized-polygon-extrude.mitcad",
                export=root / "out/parameterized-polygon-extrude.stl",
                executable=str(executable),
                work_dir=root / "parameterized-polygon-extrude-workspace",
            )
            self.assertEqual(len(extrude_native["bodies"]), 1)
            extrude_body = extrude_native["bodies"][0]
            self.assertEqual(extrude_body["kind"], "solid")
            self.assertAlmostEqual(extrude_body["volume"], 6000.0, places=4)
            for actual, expected in zip(
                extrude_body["bbox"]["min"],
                [0.0, 0.0, -5.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                extrude_body["bbox"]["max"],
                [20.0, 30.0, 5.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            axis_x = Parameter("axis_x", 8)
            panel = Box(80, 46, 10)
            with Sketch(name="PassThrough", plane="XY") as profile:
                Polygon2D(
                    [
                        (12, -5),
                        (16, -5),
                        (16, 5),
                        (12, 5),
                    ],
                    plane="XY",
                )
            shifted_cut_shape = panel - profile.revolve(
                axis=AxisLine(
                    Axis.Y,
                    origin=(axis_x, 0, 0),
                ),
            )
            shifted_cut_document = compile_mitcad_ir(
                normalize_shape(shifted_cut_shape),
                "ShiftedRevolveCut",
            )

            # The native axis transport is parameter-driven in the compiled
            # document; the current value is not baked into the construction
            # line as the semantic source of truth.
            replay_sketch = shifted_cut_document["replay"][0]["commands"][0]["def"]
            construction = [
                entity
                for entity in replay_sketch["entities"]
                if entity.get("construction") is True
            ]
            self.assertEqual(len(construction), 1)
            self.assertIn(
                "axis_x",
                [
                    dimension["value"]
                    for dimension in replay_sketch["dimensions"]
                ],
            )

            shifted_cut = run_document(
                shifted_cut_document,
                save=root / "out/shifted-revolve-cut.mitcad",
                export=root / "out/shifted-revolve-cut.stl",
                executable=str(executable),
                work_dir=root / "shifted-revolve-cut-workspace",
            )
            self.assertEqual(shifted_cut["completed"], 4)
            self.assertEqual(len(shifted_cut["bodies"]), 1)
            shifted_body = shifted_cut["bodies"][0]
            self.assertEqual(shifted_body["kind"], "solid")
            # Box defaults to Anchor.CENTER, so its Z range clips the
            # radius-8 outer revolve at +/-5 while the radius-4 inner hole
            # remains fully inside that strip.
            outer_strip_area = 2.0 * (
                5.0 * sqrt(39.0)
                + 64.0 * asin(5.0 / 8.0)
            )
            expected_volume = 36800.0 - (
                outer_strip_area - 16.0 * pi
            ) * 10.0
            self.assertAlmostEqual(
                shifted_body["volume"],
                expected_volume,
                places=3,
            )
            for actual, expected in zip(
                shifted_body["bbox"]["min"],
                [-40.0, -23.0, -5.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                shifted_body["bbox"]["max"],
                [40.0, 23.0, 5.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            axis_z = Parameter("axis_z", 3)
            shifted_plane_panel = Box(80, 46, 30)
            with Sketch(
                name="ShiftedPlanePassThrough",
                plane="XY",
                offset=axis_z,
            ) as shifted_plane_profile:
                Polygon2D(
                    [
                        (12, -5),
                        (16, -5),
                        (16, 5),
                        (12, 5),
                    ],
                    plane="XY",
                )
            shifted_plane_shape = shifted_plane_panel - shifted_plane_profile.revolve(
                axis=AxisLine(
                    Axis.Y,
                    origin=(axis_x, 0, axis_z),
                ),
            )
            shifted_plane_document = compile_mitcad_ir(
                normalize_shape(shifted_plane_shape),
                "ShiftedPlaneRevolveCut",
            )

            shifted_plane_replay = shifted_plane_document["replay"][0]["commands"]
            self.assertEqual(
                [row["def"]["type"] for row in shifted_plane_replay],
                ["construction_plane", "sketch", "revolve"],
            )
            self.assertEqual(
                shifted_plane_replay[0]["def"]["definition"],
                {
                    "type": "offset",
                    "plane": "xy",
                    "distance": "axis_z",
                },
            )
            self.assertEqual(
                shifted_plane_replay[1]["def"]["plane"],
                {"ref": "plane.uid"},
            )
            self.assertIn(
                "axis_x",
                [
                    dimension["value"]
                    for dimension in shifted_plane_replay[1]["def"]["dimensions"]
                ],
            )

            shifted_plane = run_document(
                shifted_plane_document,
                save=root / "out/shifted-plane-revolve-cut.mitcad",
                export=root / "out/shifted-plane-revolve-cut.stl",
                executable=str(executable),
                work_dir=root / "shifted-plane-revolve-cut-workspace",
            )
            self.assertEqual(shifted_plane["completed"], 6)
            self.assertEqual(len(shifted_plane["bodies"]), 1)
            shifted_plane_body = shifted_plane["bodies"][0]
            self.assertEqual(shifted_plane_body["kind"], "solid")
            self.assertAlmostEqual(
                shifted_plane_body["volume"],
                80.0 * 46.0 * 30.0 - pi * (8.0 ** 2 - 4.0 ** 2) * 10.0,
                places=3,
            )
            for actual, expected in zip(
                shifted_plane_body["bbox"]["min"],
                [-40.0, -23.0, -15.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                shifted_plane_body["bbox"]["max"],
                [40.0, 23.0, 15.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            configured_document = run_script(
                SHIFTED_AXIS_REVOLVE,
                backend="mitcad",
            )
            configured_path = root / "out/shifted-axis-revolve.mitcad"
            configured_cut_stl = root / "out/shifted-axis-revolve-cut.stl"
            configured_cut = run_document(
                configured_document,
                save=configured_path,
                export=configured_cut_stl,
                executable=str(executable),
                work_dir=root / "shifted-axis-configured-workspace",
            )
            self.assertEqual(len(configured_cut["bodies"]), 1)
            configured_cut_body = configured_cut["bodies"][0]
            self.assertEqual(configured_cut_body["kind"], "solid")
            configured_cut_volume = (
                40.0 * 24.0 * 20.0
                - pi * (
                    6.0 * (2.25 ** 2)
                    + 18.0 * (1.85 ** 2)
                )
            )
            self.assertAlmostEqual(
                configured_cut_body["volume"],
                configured_cut_volume,
                places=3,
            )
            for actual, expected in zip(
                configured_cut_body["bbox"]["min"],
                [-20.0, -12.0, -10.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                configured_cut_body["bbox"]["max"],
                [20.0, 12.0, 10.0],
            ):
                self.assertAlmostEqual(actual, expected, places=5)

            configured_geometry = run_mesh_geometry_verification(
                configured_cut_stl,
                evidence / "verification" / "shifted-axis-revolve",
                load_geometry_contract(
                    ROOT
                    / "models/shifted-axis-revolve/verification/geometry.json"
                ),
                verification_id="mitcad-shifted-axis-revolve-geometry",
            )
            self.assertEqual(
                configured_geometry["status"],
                "pass",
                configured_geometry,
            )

            suppressed_stl = root / "out/shifted-axis-revolve-suppressed.stl"
            suppressed = run_saved_configuration(
                configured_path,
                "Suppressed",
                save=configured_path,
                export=suppressed_stl,
                executable=str(executable),
                work_dir=root / "shifted-axis-suppressed-workspace",
            )
            self.assertEqual(len(suppressed["bodies"]), 1)
            suppressed_body = suppressed["bodies"][0]
            self.assertAlmostEqual(
                suppressed_body["volume"],
                40.0 * 24.0 * 20.0,
                places=4,
            )
            suppressed_saved_evidence = (
                evidence / "shifted-axis-revolve-suppressed.mitcad"
            )
            shutil.copy2(configured_path, suppressed_saved_evidence)

            restored_stl = root / "out/shifted-axis-revolve-restored.stl"
            restored = run_saved_configuration(
                configured_path,
                "Cut",
                save=configured_path,
                export=restored_stl,
                executable=str(executable),
                work_dir=root / "shifted-axis-restored-workspace",
            )
            self.assertEqual(len(restored["bodies"]), 1)
            restored_body = restored["bodies"][0]
            self.assertAlmostEqual(
                restored_body["volume"],
                configured_cut_volume,
                places=3,
            )
            restored_saved_evidence = (
                evidence / "shifted-axis-revolve-restored.mitcad"
            )
            shutil.copy2(configured_path, restored_saved_evidence)

            for artifact in (
                configured_path,
                configured_cut_stl,
                suppressed_stl,
                restored_stl,
                suppressed_saved_evidence,
                restored_saved_evidence,
            ):
                self.assertTrue(artifact.is_file(), str(artifact))
                self.assertGreater(artifact.stat().st_size, 0, str(artifact))

            primitive_document = run_script(
                PRIMITIVE_CSG,
                backend="mitcad",
            )
            primitive_path = root / "out/primitive-csg-configured.mitcad"
            primitive_clipped_stl = root / "out/primitive-csg-clipped.stl"
            primitive_clipped = run_document(
                primitive_document,
                save=primitive_path,
                export=primitive_clipped_stl,
                executable=str(executable),
                work_dir=root / "primitive-csg-configured-workspace",
            )
            self.assertEqual(len(primitive_clipped["bodies"]), 1)
            primitive_clipped_body = primitive_clipped["bodies"][0]
            self.assertEqual(primitive_clipped_body["kind"], "solid")
            primitive_geometry = run_mesh_geometry_verification(
                primitive_clipped_stl,
                evidence / "verification" / "primitive-csg",
                load_geometry_contract(
                    ROOT / "models/primitive-csg/verification/geometry.json"
                ),
                verification_id="mitcad-primitive-csg-geometry",
            )
            self.assertEqual(
                primitive_geometry["status"],
                "pass",
                primitive_geometry,
            )

            primitive_unclipped_stl = root / "out/primitive-csg-unclipped.stl"
            primitive_unclipped = run_saved_configuration(
                primitive_path,
                "Unclipped",
                save=primitive_path,
                export=primitive_unclipped_stl,
                executable=str(executable),
                work_dir=root / "primitive-csg-unclipped-workspace",
            )
            self.assertEqual(len(primitive_unclipped["bodies"]), 1)
            primitive_unclipped_body = primitive_unclipped["bodies"][0]
            self.assertEqual(primitive_unclipped_body["kind"], "solid")
            self.assertLess(
                primitive_unclipped_body["bbox"]["min"][2],
                -19.9,
            )
            self.assertGreater(
                primitive_unclipped_body["volume"],
                primitive_clipped_body["volume"] + 100.0,
            )
            primitive_unclipped_evidence = (
                evidence / "primitive-csg-unclipped.mitcad"
            )
            shutil.copy2(primitive_path, primitive_unclipped_evidence)

            primitive_restored_stl = root / "out/primitive-csg-restored.stl"
            primitive_restored = run_saved_configuration(
                primitive_path,
                "Clipped",
                save=primitive_path,
                export=primitive_restored_stl,
                executable=str(executable),
                work_dir=root / "primitive-csg-restored-workspace",
            )
            self.assertEqual(len(primitive_restored["bodies"]), 1)
            primitive_restored_body = primitive_restored["bodies"][0]
            self.assertAlmostEqual(
                primitive_restored_body["volume"],
                primitive_clipped_body["volume"],
                places=4,
            )
            for actual, expected in zip(
                primitive_restored_body["bbox"]["min"],
                primitive_clipped_body["bbox"]["min"],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            for actual, expected in zip(
                primitive_restored_body["bbox"]["max"],
                primitive_clipped_body["bbox"]["max"],
            ):
                self.assertAlmostEqual(actual, expected, places=5)
            primitive_restored_evidence = (
                evidence / "primitive-csg-restored.mitcad"
            )
            shutil.copy2(primitive_path, primitive_restored_evidence)

            for artifact in (
                primitive_path,
                primitive_clipped_stl,
                primitive_unclipped_stl,
                primitive_restored_stl,
                primitive_unclipped_evidence,
                primitive_restored_evidence,
            ):
                self.assertTrue(artifact.is_file(), str(artifact))
                self.assertGreater(artifact.stat().st_size, 0, str(artifact))

            shifted_plane_stl = root / "out/shifted-plane-revolve-cut.stl"
            retained_shifted_plane_stl = (
                evidence / "shifted-plane-revolve-cut.stl"
            )
            shutil.copy2(shifted_plane_stl, retained_shifted_plane_stl)
            self.assertGreater(retained_shifted_plane_stl.stat().st_size, 0)

            shifted_stl = root / "out/shifted-revolve-cut.stl"
            retained_shifted_stl = evidence / "shifted-revolve-cut.stl"
            shutil.copy2(shifted_stl, retained_shifted_stl)
            self.assertGreater(retained_shifted_stl.stat().st_size, 0)

            for filename in (
                "simple-box.mitcad",
                "simple-box.stl",
                "circle-negative-extrude.mitcad",
                "circle-negative-extrude.stl",
                "topology-face-boundary-box.mitcad",
                "topology-face-boundary-box.stl",
                "parameterized-polygon-revolve.mitcad",
                "parameterized-polygon-revolve.stl",
                "mixed-role-revolve.mitcad",
                "mixed-role-revolve.stl",
                "mixed-role-expression-revolve.mitcad",
                "mixed-role-expression-revolve.stl",
                "asymmetric-chamfer.mitcad",
                "asymmetric-chamfer.stl",
                "fillet-cone-boolean.mitcad",
                "fillet-cone-boolean.stl",
                "top-face-boundary-fillet.mitcad",
                "top-face-boundary-fillet.stl",
                "placed-frustum.mitcad",
                "placed-frustum.stl",
                "shifted-sphere-csg.mitcad",
                "shifted-sphere-csg.stl",
                "offset-cone-csg.mitcad",
                "offset-cone-csg.stl",
                "placed-sphere.mitcad",
                "placed-sphere.stl",
                "three-circle-exact-region.mitcad",
                "three-circle-exact-region.stl",
                "parameterized-polygon-extrude.mitcad",
                "parameterized-polygon-extrude.stl",
                "shifted-revolve-cut.mitcad",
                "shifted-revolve-cut.stl",
                "shifted-plane-revolve-cut.mitcad",
                "shifted-plane-revolve-cut.stl",
            ):
                output = root / "out" / filename
                self.assertTrue(output.is_file(), filename)
                self.assertGreater(output.stat().st_size, 0, filename)

            (evidence / "native-smoke.txt").write_text(
                "\n".join(
                    [
                        f"version={cli_version}",
                        f"appimage_sha256={ASSET_SHA256}",
                        f"source_reference_blob={SOURCE_REFERENCE_BLOB}",
                        f"runtime_reference_blob={RUNTIME_REFERENCE_BLOB}",
                        f"simple_box_volume={box_body['volume']}",
                        f"simple_box_bbox={box_body['bbox']}",
                        f"negative_circle_volume={circle_body['volume']}",
                        f"negative_circle_bbox={circle_body['bbox']}",
                        "simple_box_generic_verification=pass",
                        "negative_circle_generic_verification=pass",
                        f"topology_volume={topology_body['volume']}",
                        f"topology_bbox={topology_body['bbox']}",
                        f"topology_bindings={topology['bindings']}",
                        f"parameterized_polygon_revolve_volume={polygon_body['volume']}",
                        f"parameterized_polygon_revolve_bbox={polygon_body['bbox']}",
                        "parameterized_polygon_coordinate_relations=pass",
                        f"mixed_role_revolve_volume={mixed_body['volume']}",
                        f"mixed_role_revolve_bbox={mixed_body['bbox']}",
                        "mixed_role_parameter_units=pass",
                        f"mixed_role_expression_volume={mixed_expression_body['volume']}",
                        f"mixed_role_expression_bbox={mixed_expression_body['bbox']}",
                        "mixed_role_expression_scalar_ir=pass",
                        f"asymmetric_chamfer_volume={asymmetric_chamfer_body['volume']}",
                        f"asymmetric_chamfer_bbox={asymmetric_chamfer_body['bbox']}",
                        f"asymmetric_chamfer_bindings={asymmetric_chamfer_native['bindings']}",
                        "asymmetric_chamfer_two_distance_ir=pass",
                        f"fillet_cone_boolean_volume={fillet_cone_body['volume']}",
                        f"fillet_cone_boolean_bbox={fillet_cone_body['bbox']}",
                        f"fillet_cone_boolean_bindings={fillet_cone_native['bindings']}",
                        "fillet_parallel_edge_ir=pass",
                        f"top_face_boundary_fillet_volume={top_face_fillet_body['volume']}",
                        f"top_face_boundary_fillet_bbox={top_face_fillet_body['bbox']}",
                        f"top_face_boundary_fillet_bindings={top_face_fillet_native['bindings']}",
                        "fillet_face_boundary_ir=pass",
                        f"placed_frustum_volume={placed_frustum_body['volume']}",
                        f"placed_frustum_bbox={placed_frustum_body['bbox']}",
                        "placed_frustum_cone_ir=pass",
                        f"shifted_sphere_csg_volume={shifted_sphere_csg_body['volume']}",
                        f"shifted_sphere_csg_bbox={shifted_sphere_csg_body['bbox']}",
                        "shifted_sphere_csg_helper_mapping=pass",
                        f"offset_cone_csg_volume={offset_cone_csg_body['volume']}",
                        f"offset_cone_csg_bbox={offset_cone_csg_body['bbox']}",
                        "offset_cone_csg_helper_mapping=pass",
                        f"placed_sphere_volume={placed_sphere_body['volume']}",
                        f"placed_sphere_bbox={placed_sphere_body['bbox']}",
                        "placed_sphere_parameterized_anchor=pass",
                        f"three_circle_exact_region_volume={three_circle_body['volume']}",
                        f"three_circle_exact_region_bbox={three_circle_body['bbox']}",
                        "three_circle_exact_region_membership=pass",
                        f"parameterized_polygon_extrude_volume={extrude_body['volume']}",
                        f"parameterized_polygon_extrude_bbox={extrude_body['bbox']}",
                        "parameterized_polygon_extrude_relations=pass",
                        f"shifted_revolve_cut_volume={shifted_body['volume']}",
                        f"shifted_revolve_cut_bbox={shifted_body['bbox']}",
                        f"shifted_plane_revolve_cut_volume={shifted_plane_body['volume']}",
                        f"shifted_plane_revolve_cut_bbox={shifted_plane_body['bbox']}",
                        f"shifted_revolve_cut_bindings={shifted_cut['bindings']}",
                        f"configured_shifted_axis_cut_volume={configured_cut_body['volume']}",
                        f"configured_shifted_axis_suppressed_volume={suppressed_body['volume']}",
                        f"configured_shifted_axis_restored_volume={restored_body['volume']}",
                        "configured_shifted_axis_geometry=pass",
                        f"primitive_csg_clipped_volume={primitive_clipped_body['volume']}",
                        f"primitive_csg_clipped_bbox={primitive_clipped_body['bbox']}",
                        f"primitive_csg_unclipped_volume={primitive_unclipped_body['volume']}",
                        f"primitive_csg_unclipped_bbox={primitive_unclipped_body['bbox']}",
                        f"primitive_csg_restored_volume={primitive_restored_body['volume']}",
                        f"primitive_csg_restored_bbox={primitive_restored_body['bbox']}",
                        "primitive_csg_geometry=pass",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )


if __name__ == "__main__":
    unittest.main()

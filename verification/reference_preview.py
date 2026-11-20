"""Forge-owned deterministic presentation rendering for verified STL references.

This module produces current site-preview artifacts from an already-verified STL.
It does not verify geometry and does not create a semantic verification status.
CAD rendering/view policy is intentionally consumer-owned.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


PREVIEW_SCHEMA = 1
RENDERER = "forge-trimesh-pillow-v1"
WIDTH = 720
HEIGHT = 540
YAW_DEG = -45.0
PITCH_DEG = -32.0
MARGIN = 1.12
_SHARP_EDGE_DEG = 25.0


def _load_mesh(path: Path):
    """Load one STL as a non-empty triangle mesh without geometry processing."""

    import trimesh

    value = trimesh.load(path, force=None, process=False)
    if isinstance(value, trimesh.Scene):
        geometries = tuple(value.geometry.values())
        if not geometries:
            raise RuntimeError(f"reference preview has no mesh geometry: {path}")
        value = trimesh.util.concatenate(geometries)
    if not isinstance(value, trimesh.Trimesh):
        raise RuntimeError(f"reference preview is not a triangle mesh: {path}")
    if len(value.vertices) == 0 or len(value.faces) == 0:
        raise RuntimeError(f"reference preview mesh is empty: {path}")
    return value


def _camera(mesh, width: int, height: int):
    """Return a stable ISO camera fitted from mesh bounds only."""

    import numpy as np
    from cad_verification import OrthographicCamera

    bounds = np.asarray(mesh.bounds, dtype=float)
    low = bounds[0]
    high = bounds[1]
    target = (low + high) / 2.0
    radius = max(float(np.linalg.norm(high - low)) / 2.0, 1e-6)
    camera = OrthographicCamera(
        target=tuple(float(value) for value in target),
        yaw_deg=YAW_DEG,
        pitch_deg=PITCH_DEG,
        distance=radius * MARGIN,
    )
    return camera, low, high


def _camera_basis(camera):
    """Return image-right, image-up and target-to-camera unit vectors."""

    import numpy as np

    yaw = math.radians(camera.yaw_deg)
    pitch = math.radians(camera.pitch_deg)
    right = np.array((math.cos(yaw), -math.sin(yaw), 0.0), dtype=float)
    up = np.array(
        (
            -math.sin(yaw) * math.sin(pitch),
            -math.cos(yaw) * math.sin(pitch),
            math.cos(pitch),
        ),
        dtype=float,
    )
    view = np.cross(right, up)
    return right, up, view


def _render_mesh(mesh, camera, width: int, height: int):
    """Rasterize one mesh deterministically with a neutral shaded style."""

    import numpy as np
    from PIL import Image, ImageDraw
    from cad_verification import project_points

    vertices = np.asarray(mesh.vertices, dtype=float)
    faces = np.asarray(mesh.faces, dtype=int)
    normals = np.asarray(mesh.face_normals, dtype=float)
    projected = np.asarray(
        project_points(vertices, camera, width, height),
        dtype=float,
    )

    _right, _up, view = _camera_basis(camera)
    target = np.asarray(camera.target, dtype=float)
    relative = vertices - target
    depth = relative @ view
    visible = normals @ view > 1e-9
    face_depth = depth[faces].mean(axis=1)
    order = np.argsort(face_depth, kind="mergesort")

    image = Image.new("RGB", (width, height), (248, 248, 248))
    draw = ImageDraw.Draw(image)

    light = view + np.array((-0.4, 0.2, 0.8), dtype=float)
    light /= np.linalg.norm(light)
    for index in order:
        if not visible[index]:
            continue
        polygon = [
            (float(projected[vertex][0]), float(projected[vertex][1]))
            for vertex in faces[index]
        ]
        normal = normals[index]
        brightness = 0.55 + 0.35 * max(0.0, float(normal @ light))
        value = max(100, min(235, int(215 * brightness + 25)))
        draw.polygon(polygon, fill=(value, value, value))

    adjacency = np.asarray(mesh.face_adjacency, dtype=int)
    adjacency_edges = np.asarray(mesh.face_adjacency_edges, dtype=int)
    adjacency_angles = np.asarray(mesh.face_adjacency_angles, dtype=float)
    sharp = math.radians(_SHARP_EDGE_DEG)
    for (left, right), (first, second), angle in zip(
        adjacency,
        adjacency_edges,
        adjacency_angles,
    ):
        if (
            visible[left] != visible[right]
            or (
                angle > sharp
                and (visible[left] or visible[right])
            )
        ):
            draw.line(
                [
                    tuple(float(value) for value in projected[first]),
                    tuple(float(value) for value in projected[second]),
                ],
                fill=(65, 65, 65),
                width=1,
            )

    edge_counts = np.bincount(
        mesh.edges_unique_inverse,
        minlength=len(mesh.edges_unique),
    )
    for (first, second), count in zip(mesh.edges_unique, edge_counts):
        if count != 1:
            continue
        draw.line(
            [
                tuple(float(value) for value in projected[first]),
                tuple(float(value) for value in projected[second]),
            ],
            fill=(65, 65, 65),
            width=1,
        )

    return image


def render_reference_preview(
    stl_path: Path,
    presentation_dir: Path,
    *,
    source_reference: str = "model.stl",
    width: int = WIDTH,
    height: int = HEIGHT,
) -> dict[str, Any]:
    """Render one verified STL and write presentation preview provenance."""

    stl_path = Path(stl_path)
    presentation_dir = Path(presentation_dir)
    if width <= 0 or height <= 0:
        raise ValueError("preview dimensions must be positive")
    if not stl_path.is_file() or stl_path.stat().st_size == 0:
        raise RuntimeError(f"reference preview STL is missing or empty: {stl_path}")

    mesh = _load_mesh(stl_path)
    camera, low, high = _camera(mesh, width, height)
    image = _render_mesh(mesh, camera, width, height)

    presentation_dir.mkdir(parents=True, exist_ok=True)
    image_path = presentation_dir / "preview-iso.png"
    image.save(
        image_path,
        format="PNG",
        optimize=False,
        compress_level=9,
    )
    if not image_path.is_file() or image_path.stat().st_size == 0:
        raise RuntimeError(f"reference preview PNG is missing: {image_path}")

    metadata = {
        "schema": PREVIEW_SCHEMA,
        "kind": "presentation-preview",
        "renderer": RENDERER,
        "view": "iso",
        "image": image_path.name,
        "source": source_reference,
        "width": width,
        "height": height,
        "camera": {
            "target": [float(value) for value in camera.target],
            "yaw_deg": camera.yaw_deg,
            "pitch_deg": camera.pitch_deg,
            "distance": camera.distance,
        },
        "bounds": {
            "min": [float(value) for value in low],
            "max": [float(value) for value in high],
        },
    }
    (presentation_dir / "preview.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata

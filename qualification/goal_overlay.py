#!/usr/bin/env python3
"""Render independent expected geometry and overlays for qualification views."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qualification.geometry_contracts import geometry_contract


BOX_EDGES = (
    (0, 1), (1, 3), (3, 2), (2, 0),
    (4, 5), (5, 7), (7, 6), (6, 4),
    (0, 4), (1, 5), (2, 6), (3, 7),
)


def _sub(a, b):
    return tuple(float(a[i]) - float(b[i]) for i in range(3))


def _dot(a, b):
    return sum(float(a[i]) * float(b[i]) for i in range(3))


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(v):
    length = math.sqrt(_dot(v, v))
    if length <= 0:
        raise ValueError("zero-length camera vector")
    return tuple(value / length for value in v)


def _camera_basis(camera):
    yaw = float(camera["yaw"])
    pitch = float(camera["pitch"])
    forward = (
        math.sin(yaw) * math.cos(pitch),
        math.cos(yaw) * math.cos(pitch),
        -math.sin(pitch),
    )

    world_up = (0.0, 0.0, 1.0)
    if abs(_dot(_norm(forward), world_up)) > 0.999:
        # For an exact top/bottom camera, world Z cannot also define image-up.
        # Use world +Y so top view remains X-right / Y-up.
        world_up = (0.0, 1.0, 0.0)

    right = _norm(_cross(forward, world_up))
    up = _norm(_cross(right, forward))
    return right, up


def _project(point, camera, width, height):
    target = tuple(float(v) for v in camera["target"])
    right, up = _camera_basis(camera)
    delta = _sub(point, target)

    half_height = 0.4 * float(camera["distance"])
    half_width = half_height * (float(width) / float(height))
    if half_width <= 0 or half_height <= 0:
        raise ValueError("invalid orthographic camera size")

    x = width / 2.0 + _dot(delta, right) / half_width * width / 2.0
    y = height / 2.0 - _dot(delta, up) / half_height * height / 2.0
    return (x, y)


def _corners(bounds):
    lo = bounds["min"]
    hi = bounds["max"]
    return [
        (lo[0], lo[1], lo[2]),
        (hi[0], lo[1], lo[2]),
        (lo[0], hi[1], lo[2]),
        (hi[0], hi[1], lo[2]),
        (lo[0], lo[1], hi[2]),
        (hi[0], lo[1], hi[2]),
        (lo[0], hi[1], hi[2]),
        (hi[0], hi[1], hi[2]),
    ]


def _draw_label(draw, point, label, font):
    x, y = point
    box = draw.textbbox((x + 5, y + 5), label, font=font)
    draw.rectangle(
        (box[0] - 3, box[1] - 2, box[2] + 3, box[3] + 2),
        fill=(255, 255, 255, 220),
    )
    draw.text(
        (x + 5, y + 5),
        label,
        font=font,
        fill=(20, 35, 55, 255),
    )


def _draw_expected_boxes(
    image,
    camera,
    expected,
    *,
    labels=True,
    fill_boxes=False,
):
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    font = ImageFont.load_default()

    for index, body in enumerate(expected):
        points = [
            _project(point, camera, width, height)
            for point in _corners(body)
        ]
        line = (
            (20, 110, 235, 230)
            if index % 2 == 0
            else (0, 155, 110, 230)
        )

        if fill_boxes:
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            fill = (
                (228, 238, 252, 255)
                if index % 2 == 0
                else (226, 246, 239, 255)
            )
            draw.rectangle(
                (min(xs), min(ys), max(xs), max(ys)),
                fill=fill,
            )

        for a, b in BOX_EDGES:
            draw.line((points[a], points[b]), fill=line, width=3)

        if labels:
            center3d = tuple(
                (
                    float(body["min"][axis])
                    + float(body["max"][axis])
                ) / 2.0
                for axis in range(3)
            )
            _draw_label(
                draw,
                _project(center3d, camera, width, height),
                str(body["label"]),
                font,
            )

    return image


def _circle_3d(center, radius, z, segments=48):
    cx, cy = center
    return [
        (
            cx + radius * math.cos(2.0 * math.pi * index / segments),
            cy + radius * math.sin(2.0 * math.pi * index / segments),
            z,
        )
        for index in range(segments)
    ]


def _slot_outline(centerline, width):
    points = [
        (float(point[0]), float(point[1]))
        for point in centerline
    ]
    if len(points) < 2:
        raise ValueError("visual slot centerline needs at least two points")

    radius = float(width) / 2.0
    plus = []
    minus = []
    for index, point in enumerate(points):
        previous = points[max(index - 1, 0)]
        following = points[min(index + 1, len(points) - 1)]
        dx = following[0] - previous[0]
        dy = following[1] - previous[1]
        length = math.hypot(dx, dy)
        if length <= 0:
            raise ValueError("visual slot centerline has duplicate neighbours")
        nx = -dy / length
        ny = dx / length
        plus.append((point[0] + nx * radius, point[1] + ny * radius))
        minus.append((point[0] - nx * radius, point[1] - ny * radius))

    return plus + list(reversed(minus))


def _project_polyline(points, camera, width, height):
    return [
        _project(point, camera, width, height)
        for point in points
    ]


def _draw_through_hole(draw, camera, feature, width, height, line):
    center = feature["center"]
    radius = float(feature["diameter"]) / 2.0
    z_min, z_max = feature["z"]

    for z in (z_min, z_max):
        circle = _project_polyline(
            _circle_3d(center, radius, z),
            camera,
            width,
            height,
        )
        draw.line(circle + [circle[0]], fill=line, width=4)

    for angle in (0.0, math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0):
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        a = _project((x, y, z_min), camera, width, height)
        b = _project((x, y, z_max), camera, width, height)
        draw.line((a, b), fill=line, width=3)


def _draw_through_slot(draw, camera, feature, width, height, line):
    centerline = feature["centerline"]
    slot_width = float(feature["width"])
    radius = slot_width / 2.0
    z_min, z_max = feature["z"]
    outline = _slot_outline(centerline, slot_width)

    for z in (z_min, z_max):
        outline3d = [(x, y, z) for x, y in outline]
        projected = _project_polyline(
            outline3d,
            camera,
            width,
            height,
        )
        draw.line(projected + [projected[0]], fill=line, width=4)

        for endpoint in (centerline[0], centerline[-1]):
            circle = _project_polyline(
                _circle_3d(endpoint, radius, z),
                camera,
                width,
                height,
            )
            draw.line(circle + [circle[0]], fill=line, width=3)

        center3d = [(x, y, z) for x, y in centerline]
        draw.line(
            _project_polyline(center3d, camera, width, height),
            fill=line,
            width=2,
        )

    for x, y in (
        outline[0],
        outline[len(centerline) - 1],
        outline[len(centerline)],
        outline[-1],
    ):
        a = _project((x, y, z_min), camera, width, height)
        b = _project((x, y, z_max), camera, width, height)
        draw.line((a, b), fill=line, width=2)


def _draw_visual_features(
    image,
    camera,
    features,
    *,
    labels=True,
):
    if not features:
        return image

    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    font = ImageFont.load_default()
    line = (190, 45, 45, 245)

    for feature in features:
        kind = feature["type"]
        if kind == "through_hole":
            _draw_through_hole(
                draw,
                camera,
                feature,
                width,
                height,
                line,
            )
            label_point = (
                feature["center"][0],
                feature["center"][1],
                feature["z"][1],
            )
        elif kind == "through_slot":
            _draw_through_slot(
                draw,
                camera,
                feature,
                width,
                height,
                line,
            )
            midpoint = feature["centerline"][
                len(feature["centerline"]) // 2
            ]
            label_point = (
                midpoint[0],
                midpoint[1],
                feature["z"][1],
            )
        else:
            raise ValueError(f"unsupported visual feature type: {kind}")

        if labels:
            _draw_label(
                draw,
                _project(label_point, camera, width, height),
                str(feature["label"]),
                font,
            )

    return image


def render(case, camera_path, actual_path, goal_path, overlay_path):
    contract = geometry_contract(case)
    camera = json.loads(camera_path.read_text(encoding="utf-8"))
    actual = Image.open(actual_path).convert("RGBA")

    goal = Image.new("RGBA", actual.size, (248, 250, 253, 255))
    _draw_expected_boxes(
        goal,
        camera,
        contract["visual_boxes"],
        labels=True,
        fill_boxes=True,
    )
    _draw_visual_features(
        goal,
        camera,
        contract["visual_features"],
        labels=True,
    )
    goal.convert("RGB").save(goal_path)

    overlay = actual.copy()
    _draw_expected_boxes(
        overlay,
        camera,
        contract["visual_boxes"],
        labels=False,
        fill_boxes=False,
    )
    _draw_visual_features(
        overlay,
        camera,
        contract["visual_features"],
        labels=False,
    )
    overlay.convert("RGB").save(overlay_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--camera", type=Path, required=True)
    parser.add_argument("--actual", type=Path, required=True)
    parser.add_argument("--goal", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    args = parser.parse_args()

    render(
        args.case,
        args.camera,
        args.actual,
        args.goal,
        args.overlay,
    )
    print(
        f"Wrote goal and overlay for {args.case}: "
        f"{args.actual.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

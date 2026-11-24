"""Generic visual regression and expected-shape evidence helpers."""

from __future__ import annotations

from base64 import b64decode, b64encode
from dataclasses import dataclass
from io import BytesIO
import math
from numbers import Real
from pathlib import Path
from typing import Any, Iterable, Sequence
import zlib

from PIL import Image, ImageDraw

from .errors import (
    VerificationConfigError,
    VerificationFailure,
    VisualEvidenceError,
)


_RESAMPLE = Image.Resampling.LANCZOS
_OUTLINE = (255, 0, 255)
_FILL = (255, 0, 255, 48)


def _number(value: Any, name: str) -> float:
    """Return one finite real number."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise VerificationConfigError(f"{name} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise VerificationConfigError(f"{name} must be finite")
    return result


def _positive(value: Any, name: str) -> float:
    """Return one finite positive number."""

    result = _number(value, name)
    if result <= 0:
        raise VerificationConfigError(f"{name} must be positive")
    return result


def _positive_int(value: Any, name: str) -> int:
    """Return one positive integer."""

    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise VerificationConfigError(f"{name} must be a positive integer")
    return value


def _xyz(value: Iterable[Any], name: str) -> tuple[float, float, float]:
    """Normalize one finite XYZ vector."""

    try:
        values = tuple(value)
    except TypeError as exc:
        raise VerificationConfigError(
            f"{name} must contain exactly three numbers"
        ) from exc
    if len(values) != 3:
        raise VerificationConfigError(
            f"{name} must contain exactly three numbers"
        )
    return (
        _number(values[0], f"{name}[0]"),
        _number(values[1], f"{name}[1]"),
        _number(values[2], f"{name}[2]"),
    )


def _label(value: Any) -> str | None:
    """Normalize an optional non-empty label."""

    if value is None:
        return None
    if not isinstance(value, str):
        raise VerificationConfigError("label must be a string or None")
    result = value.strip()
    if not result:
        raise VerificationConfigError("label may not be empty")
    return result


def _evidence_reference(value: Any, name: str) -> str | None:
    """Validate one caller-controlled artifact reference."""

    if value is None:
        return None
    if not isinstance(value, str):
        raise VerificationConfigError(
            f"{name} must be a string or None"
        )
    return value


def _normalized_size(value: Any) -> tuple[int, int]:
    """Validate one requested visual comparison size."""

    if (
        isinstance(value, (str, bytes))
        or not isinstance(value, Sequence)
        or len(value) != 2
    ):
        raise VerificationConfigError(
            "normalized_size must contain width and height"
        )
    return (
        _positive_int(value[0], "normalized width"),
        _positive_int(value[1], "normalized height"),
    )


def _load_rgb_image(path: Path) -> Image.Image:
    """Load one detached RGB image with visual evidence error semantics."""

    path = Path(path)
    if not path.is_file():
        raise VisualEvidenceError(f"image file does not exist: {path}")
    try:
        with Image.open(path) as source:
            source.load()
            return source.convert("RGB").copy()
    except VisualEvidenceError:
        raise
    except Exception as exc:
        raise VisualEvidenceError(
            f"could not load image: {path}: {exc}"
        ) from exc


def _write_png(image: Image.Image, output_path: Path) -> Path:
    """Write one deterministic PNG artifact."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(
        output_path,
        format="PNG",
        optimize=False,
        compress_level=9,
    )
    return output_path


def normalize_image(path: Path, width: int, height: int) -> Image.Image:
    """Load, grayscale and deterministically resize one image."""

    width = _positive_int(width, "width")
    height = _positive_int(height, "height")
    path = Path(path)
    if not path.is_file():
        raise VisualEvidenceError(f"image file does not exist: {path}")
    try:
        with Image.open(path) as source:
            source.load()
            return source.convert("RGB").convert("L").resize(
                (width, height),
                _RESAMPLE,
            )
    except VisualEvidenceError:
        raise
    except Exception as exc:
        raise VisualEvidenceError(
            f"could not load image: {path}: {exc}"
        ) from exc


def _grayscale(image: Image.Image) -> Image.Image:
    """Return a detached grayscale image."""

    if not isinstance(image, Image.Image):
        raise VerificationConfigError("image must be a Pillow Image")
    return image.convert("L").copy()


def encode_baseline(
    image: Image.Image,
    *,
    encoding: str = "raw",
) -> dict[str, Any]:
    """Encode one grayscale baseline into a JSON-compatible payload."""

    gray = _grayscale(image)
    width, height = gray.size
    raw = gray.tobytes()
    if encoding == "raw":
        data = raw
    elif encoding == "zlib":
        data = zlib.compress(raw, level=9)
    elif encoding == "png":
        buffer = BytesIO()
        gray.save(buffer, format="PNG", optimize=False, compress_level=9)
        data = buffer.getvalue()
    else:
        raise VerificationConfigError(
            "baseline encoding must be raw, zlib or png"
        )
    return {
        "encoding": encoding,
        "width": width,
        "height": height,
        "data": b64encode(data).decode("ascii"),
    }


def decode_baseline(payload: dict[str, Any]) -> Image.Image:
    """Decode and validate one baseline payload."""

    if not isinstance(payload, dict):
        raise VisualEvidenceError("baseline payload must be an object")
    encoding = payload.get("encoding")
    width = _positive_int(payload.get("width"), "width")
    height = _positive_int(payload.get("height"), "height")
    encoded = payload.get("data")
    if not isinstance(encoded, str):
        raise VisualEvidenceError("baseline data must be base64 text")
    try:
        data = b64decode(encoded, validate=True)
        if encoding == "raw":
            raw = data
        elif encoding == "zlib":
            raw = zlib.decompress(data)
        elif encoding == "png":
            with Image.open(BytesIO(data)) as image:
                image.load()
                gray = image.convert("L")
                if gray.size != (width, height):
                    raise VisualEvidenceError(
                        "baseline PNG dimensions do not match payload"
                    )
                return gray.copy()
        else:
            raise VisualEvidenceError(
                "baseline encoding must be raw, zlib or png"
            )
    except VisualEvidenceError:
        raise
    except Exception as exc:
        raise VisualEvidenceError(
            f"could not decode baseline payload: {exc}"
        ) from exc

    expected_bytes = width * height
    if len(raw) != expected_bytes:
        raise VisualEvidenceError(
            "decoded baseline byte count does not match dimensions"
        )
    return Image.frombytes("L", (width, height), raw)


def compare_images(
    current: Image.Image,
    reference: Image.Image,
    *,
    changed_pixel_threshold: int,
    max_mean_difference: float,
    max_changed_fraction: float,
) -> dict[str, Any]:
    """Compare equal-size grayscale images and return stable evidence."""

    current_gray = _grayscale(current)
    reference_gray = _grayscale(reference)
    if current_gray.size != reference_gray.size:
        raise VerificationConfigError(
            "current and reference images must have equal size"
        )
    threshold = _positive_int(
        changed_pixel_threshold,
        "changed_pixel_threshold",
    )
    if threshold > 255:
        raise VerificationConfigError(
            "changed_pixel_threshold may not exceed 255"
        )
    mean_limit = _number(max_mean_difference, "max_mean_difference")
    fraction_limit = _number(
        max_changed_fraction,
        "max_changed_fraction",
    )
    if mean_limit < 0:
        raise VerificationConfigError(
            "max_mean_difference may not be negative"
        )
    if not 0 <= fraction_limit <= 1:
        raise VerificationConfigError(
            "max_changed_fraction must be between 0 and 1"
        )

    current_bytes = current_gray.tobytes()
    reference_bytes = reference_gray.tobytes()
    deltas = [
        abs(current_value - reference_value)
        for current_value, reference_value in zip(
            current_bytes,
            reference_bytes,
        )
    ]
    count = len(deltas)
    mean_difference = round(sum(deltas) / count, 6)
    changed_fraction = round(
        sum(delta >= threshold for delta in deltas) / count,
        6,
    )
    passed = (
        mean_difference <= mean_limit
        and changed_fraction <= fraction_limit
    )
    evidence = {
        "mean_absolute_difference": mean_difference,
        "changed_pixel_fraction": changed_fraction,
        "changed_pixel_threshold": threshold,
        "max_mean_difference": mean_limit,
        "max_changed_fraction": fraction_limit,
        "pass": bool(passed),
    }
    if not passed:
        raise VerificationFailure(
            "visual regression exceeds configured limits",
            evidence=evidence,
        )
    return evidence


def write_diff_image(
    current: Image.Image,
    reference: Image.Image,
    output_path: Path,
) -> Path:
    """Write a deterministic current/difference comparison image."""

    current_gray = _grayscale(current)
    reference_gray = _grayscale(reference)
    if current_gray.size != reference_gray.size:
        raise VerificationConfigError(
            "current and reference images must have equal size"
        )
    width, height = current_gray.size
    deltas = bytes(
        abs(current_value - reference_value)
        for current_value, reference_value in zip(
            current_gray.tobytes(),
            reference_gray.tobytes(),
        )
    )
    difference = Image.frombytes("L", (width, height), deltas)
    result = Image.new("RGB", (width * 2, height))
    result.paste(current_gray.convert("RGB"), (0, 0))
    result.paste(difference.convert("RGB"), (width, 0))
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path, format="PNG", optimize=False, compress_level=9)
    return output_path


@dataclass(frozen=True)
class OrthographicCamera:
    """Consumer-supplied generic orthographic camera."""

    target: tuple[float, float, float]
    yaw_deg: float
    pitch_deg: float
    distance: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "target", _xyz(self.target, "target"))
        object.__setattr__(
            self,
            "yaw_deg",
            _number(self.yaw_deg, "yaw_deg"),
        )
        object.__setattr__(
            self,
            "pitch_deg",
            _number(self.pitch_deg, "pitch_deg"),
        )
        object.__setattr__(
            self,
            "distance",
            _positive(self.distance, "distance"),
        )


def _camera_basis(
    camera: OrthographicCamera,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Return stable image-right and image-up vectors."""

    yaw = math.radians(camera.yaw_deg)
    pitch = math.radians(camera.pitch_deg)
    right = (math.cos(yaw), -math.sin(yaw), 0.0)
    up = (
        -math.sin(yaw) * math.sin(pitch),
        -math.cos(yaw) * math.sin(pitch),
        math.cos(pitch),
    )
    return right, up


def _dot(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> float:
    return sum(a * b for a, b in zip(left, right))


def project_points(
    points: Iterable[Iterable[Any]],
    camera: OrthographicCamera,
    width: int,
    height: int,
) -> list[tuple[float, float]]:
    """Project 3D points into deterministic image-space coordinates."""

    if not isinstance(camera, OrthographicCamera):
        raise VerificationConfigError(
            "camera must be an OrthographicCamera"
        )
    width = _positive_int(width, "width")
    height = _positive_int(height, "height")
    normalized = tuple(
        _xyz(point, f"point[{index}]")
        for index, point in enumerate(points)
    )
    right, up = _camera_basis(camera)
    half_height = camera.distance
    half_width = half_height * width / height
    result = []
    for point in normalized:
        relative = tuple(
            coordinate - target
            for coordinate, target in zip(point, camera.target)
        )
        horizontal = _dot(relative, right)
        vertical = _dot(relative, up)
        pixel_x = width / 2 + horizontal / half_width * width / 2
        pixel_y = height / 2 - vertical / half_height * height / 2
        result.append((pixel_x, pixel_y))
    return result


@dataclass(frozen=True)
class ExpectedBox:
    """One consumer-supplied expected 3D box."""

    minimum: tuple[float, float, float]
    maximum: tuple[float, float, float]
    label: str | None = None

    def __post_init__(self) -> None:
        minimum = _xyz(self.minimum, "box minimum")
        maximum = _xyz(self.maximum, "box maximum")
        for axis, (low, high) in enumerate(zip(minimum, maximum)):
            if high < low:
                raise VerificationConfigError(
                    f"box maximum[{axis}] may not be below minimum[{axis}]"
                )
        object.__setattr__(self, "minimum", minimum)
        object.__setattr__(self, "maximum", maximum)
        object.__setattr__(self, "label", _label(self.label))


@dataclass(frozen=True)
class ThroughHole:
    """One generic through-hole expected feature."""

    center: tuple[float, float]
    diameter: float
    z_min: float
    z_max: float
    label: str | None = None

    def __post_init__(self) -> None:
        center = tuple(self.center)
        if len(center) != 2:
            raise VerificationConfigError(
                "hole center must contain exactly two numbers"
            )
        center_xy = (
            _number(center[0], "hole center[0]"),
            _number(center[1], "hole center[1]"),
        )
        z_min = _number(self.z_min, "hole z_min")
        z_max = _number(self.z_max, "hole z_max")
        if z_max < z_min:
            raise VerificationConfigError(
                "hole z_max may not be below z_min"
            )
        object.__setattr__(self, "center", center_xy)
        object.__setattr__(
            self,
            "diameter",
            _positive(self.diameter, "hole diameter"),
        )
        object.__setattr__(self, "z_min", z_min)
        object.__setattr__(self, "z_max", z_max)
        object.__setattr__(self, "label", _label(self.label))


@dataclass(frozen=True)
class ThroughSlot:
    """One generic through-slot expected feature."""

    start: tuple[float, float]
    end: tuple[float, float]
    width: float
    z_min: float
    z_max: float
    label: str | None = None

    def __post_init__(self) -> None:
        start = tuple(self.start)
        end = tuple(self.end)
        if len(start) != 2 or len(end) != 2:
            raise VerificationConfigError(
                "slot start/end must contain exactly two numbers"
            )
        start_xy = (
            _number(start[0], "slot start[0]"),
            _number(start[1], "slot start[1]"),
        )
        end_xy = (
            _number(end[0], "slot end[0]"),
            _number(end[1], "slot end[1]"),
        )
        if start_xy == end_xy:
            raise VerificationConfigError(
                "slot start and end may not be identical"
            )
        z_min = _number(self.z_min, "slot z_min")
        z_max = _number(self.z_max, "slot z_max")
        if z_max < z_min:
            raise VerificationConfigError(
                "slot z_max may not be below z_min"
            )
        object.__setattr__(self, "start", start_xy)
        object.__setattr__(self, "end", end_xy)
        object.__setattr__(
            self,
            "width",
            _positive(self.width, "slot width"),
        )
        object.__setattr__(self, "z_min", z_min)
        object.__setattr__(self, "z_max", z_max)
        object.__setattr__(self, "label", _label(self.label))


@dataclass(frozen=True)
class ThroughPathSlot:
    """One generic through-slot following a polyline centerline."""

    centerline: tuple[tuple[float, float], ...]
    width: float
    z_min: float
    z_max: float
    label: str | None = None

    def __post_init__(self) -> None:
        try:
            raw_points = tuple(self.centerline)
        except TypeError as exc:
            raise VerificationConfigError(
                "path-slot centerline must contain XY points"
            ) from exc
        if len(raw_points) < 2:
            raise VerificationConfigError(
                "path-slot centerline must contain at least two points"
            )

        points = []
        for index, point in enumerate(raw_points):
            try:
                values = tuple(point)
            except TypeError as exc:
                raise VerificationConfigError(
                    f"path-slot centerline[{index}] must contain exactly two numbers"
                ) from exc
            if len(values) != 2:
                raise VerificationConfigError(
                    f"path-slot centerline[{index}] must contain exactly two numbers"
                )
            normalized = (
                _number(values[0], f"path-slot centerline[{index}][0]"),
                _number(values[1], f"path-slot centerline[{index}][1]"),
            )
            if points and normalized == points[-1]:
                raise VerificationConfigError(
                    "path-slot centerline may not contain duplicate neighbours"
                )
            points.append(normalized)

        z_min = _number(self.z_min, "path-slot z_min")
        z_max = _number(self.z_max, "path-slot z_max")
        if z_max < z_min:
            raise VerificationConfigError(
                "path-slot z_max may not be below z_min"
            )

        object.__setattr__(self, "centerline", tuple(points))
        object.__setattr__(
            self,
            "width",
            _positive(self.width, "path-slot width"),
        )
        object.__setattr__(self, "z_min", z_min)
        object.__setattr__(self, "z_max", z_max)
        object.__setattr__(self, "label", _label(self.label))


def _box_vertices(box: ExpectedBox) -> list[tuple[float, float, float]]:
    low = box.minimum
    high = box.maximum
    return [
        (x, y, z)
        for x in (low[0], high[0])
        for y in (low[1], high[1])
        for z in (low[2], high[2])
    ]


_BOX_EDGES = (
    (0, 1), (0, 2), (0, 4),
    (1, 3), (1, 5),
    (2, 3), (2, 6),
    (3, 7),
    (4, 5), (4, 6),
    (5, 7),
    (6, 7),
)


def _circle_points(
    center: tuple[float, float],
    radius: float,
    z_value: float,
    count: int = 32,
) -> list[tuple[float, float, float]]:
    return [
        (
            center[0] + radius * math.cos(2 * math.pi * index / count),
            center[1] + radius * math.sin(2 * math.pi * index / count),
            z_value,
        )
        for index in range(count)
    ]


def _slot_outline(
    slot: ThroughSlot,
    z_value: float,
    count: int = 16,
) -> list[tuple[float, float, float]]:
    dx = slot.end[0] - slot.start[0]
    dy = slot.end[1] - slot.start[1]
    length = math.hypot(dx, dy)
    nx = -dy / length
    ny = dx / length
    radius = slot.width / 2
    angle = math.atan2(dy, dx)

    points = []
    for index in range(count + 1):
        theta = angle + math.pi / 2 + math.pi * index / count
        points.append((
            slot.end[0] + radius * math.cos(theta),
            slot.end[1] + radius * math.sin(theta),
            z_value,
        ))
    for index in range(count + 1):
        theta = angle - math.pi / 2 + math.pi * index / count
        points.append((
            slot.start[0] + radius * math.cos(theta),
            slot.start[1] + radius * math.sin(theta),
            z_value,
        ))
    return points


def _path_slot_outline(
    slot: ThroughPathSlot,
    z_value: float,
) -> list[tuple[float, float, float]]:
    """Return the historical tangent-normal outline for a path slot."""

    points = slot.centerline
    radius = slot.width / 2.0
    plus = []
    minus = []
    for index, point in enumerate(points):
        previous = points[max(index - 1, 0)]
        following = points[min(index + 1, len(points) - 1)]
        dx = following[0] - previous[0]
        dy = following[1] - previous[1]
        length = math.hypot(dx, dy)
        if length <= 0:
            raise VerificationConfigError(
                "path-slot centerline may not contain duplicate neighbours"
            )
        nx = -dy / length
        ny = dx / length
        plus.append(
            (point[0] + nx * radius, point[1] + ny * radius, z_value)
        )
        minus.append(
            (point[0] - nx * radius, point[1] - ny * radius, z_value)
        )
    return plus + list(reversed(minus))


def _draw_polyline(
    draw: ImageDraw.ImageDraw,
    points: Sequence[tuple[float, float]],
    *,
    closed: bool = False,
) -> None:
    values = list(points)
    if closed and values:
        values.append(values[0])
    if len(values) >= 2:
        draw.line(values, fill=_OUTLINE, width=1)


def draw_expected_geometry(
    image: Image.Image,
    camera: OrthographicCamera,
    *,
    boxes: Iterable[ExpectedBox] = (),
    features: Iterable[ThroughHole | ThroughSlot | ThroughPathSlot] = (),
    labels: bool = False,
    fill: bool = False,
) -> Image.Image:
    """Draw generic expected geometry over a copy of an image."""

    result = image.convert("RGB").copy()
    width, height = result.size
    draw = ImageDraw.Draw(result, "RGBA")

    for box in tuple(boxes):
        if not isinstance(box, ExpectedBox):
            raise VerificationConfigError(
                "boxes must contain ExpectedBox values"
            )
        vertices = _box_vertices(box)
        projected = project_points(vertices, camera, width, height)
        if fill:
            xs = [point[0] for point in projected]
            ys = [point[1] for point in projected]
            draw.rectangle(
                (min(xs), min(ys), max(xs), max(ys)),
                fill=_FILL,
            )
        for start, end in _BOX_EDGES:
            draw.line(
                (projected[start], projected[end]),
                fill=_OUTLINE,
                width=1,
            )
        if labels and box.label:
            draw.text(projected[0], box.label, fill=_OUTLINE)

    for feature in tuple(features):
        if isinstance(feature, ThroughHole):
            radius = feature.diameter / 2
            lower_3d = _circle_points(
                feature.center,
                radius,
                feature.z_min,
            )
            upper_3d = _circle_points(
                feature.center,
                radius,
                feature.z_max,
            )
            lower = project_points(lower_3d, camera, width, height)
            upper = project_points(upper_3d, camera, width, height)
            _draw_polyline(draw, lower, closed=True)
            _draw_polyline(draw, upper, closed=True)
            for index in (0, 8, 16, 24):
                draw.line(
                    (lower[index], upper[index]),
                    fill=_OUTLINE,
                    width=1,
                )
            if labels and feature.label:
                draw.text(upper[0], feature.label, fill=_OUTLINE)
        elif isinstance(feature, ThroughSlot):
            lower_3d = _slot_outline(feature, feature.z_min)
            upper_3d = _slot_outline(feature, feature.z_max)
            lower = project_points(lower_3d, camera, width, height)
            upper = project_points(upper_3d, camera, width, height)
            _draw_polyline(draw, lower, closed=True)
            _draw_polyline(draw, upper, closed=True)
            for index in (0, len(lower) // 2):
                draw.line(
                    (lower[index], upper[index]),
                    fill=_OUTLINE,
                    width=1,
                )
            if labels and feature.label:
                draw.text(upper[0], feature.label, fill=_OUTLINE)
        elif isinstance(feature, ThroughPathSlot):
            if len(feature.centerline) == 2:
                straight = ThroughSlot(
                    start=feature.centerline[0],
                    end=feature.centerline[1],
                    width=feature.width,
                    z_min=feature.z_min,
                    z_max=feature.z_max,
                    label=feature.label,
                )
                lower_3d = _slot_outline(straight, straight.z_min)
                upper_3d = _slot_outline(straight, straight.z_max)
                lower = project_points(lower_3d, camera, width, height)
                upper = project_points(upper_3d, camera, width, height)
                _draw_polyline(draw, lower, closed=True)
                _draw_polyline(draw, upper, closed=True)
                for index in (0, len(lower) // 2):
                    draw.line(
                        (lower[index], upper[index]),
                        fill=_OUTLINE,
                        width=1,
                    )
                if labels and feature.label:
                    draw.text(upper[0], feature.label, fill=_OUTLINE)
            else:
                lower_3d = _path_slot_outline(feature, feature.z_min)
                upper_3d = _path_slot_outline(feature, feature.z_max)
                lower = project_points(lower_3d, camera, width, height)
                upper = project_points(upper_3d, camera, width, height)
                _draw_polyline(draw, lower, closed=True)
                _draw_polyline(draw, upper, closed=True)

                radius = feature.width / 2.0
                for z_value in (feature.z_min, feature.z_max):
                    for endpoint in (
                        feature.centerline[0],
                        feature.centerline[-1],
                    ):
                        circle_3d = _circle_points(
                            endpoint,
                            radius,
                            z_value,
                        )
                        circle = project_points(
                            circle_3d,
                            camera,
                            width,
                            height,
                        )
                        _draw_polyline(draw, circle, closed=True)
                    centerline_3d = [
                        (x, y, z_value)
                        for x, y in feature.centerline
                    ]
                    _draw_polyline(
                        draw,
                        project_points(
                            centerline_3d,
                            camera,
                            width,
                            height,
                        ),
                    )

                path_count = len(feature.centerline)
                for index in (
                    0,
                    path_count - 1,
                    path_count,
                    len(lower_3d) - 1,
                ):
                    draw.line(
                        (lower[index], upper[index]),
                        fill=_OUTLINE,
                        width=1,
                    )
                if labels and feature.label:
                    draw.text(upper[0], feature.label, fill=_OUTLINE)
        else:
            raise VerificationConfigError(
                "features must contain ThroughHole, ThroughSlot or "
                "ThroughPathSlot values"
            )

    return result


def make_goal_image(
    size: tuple[int, int],
    camera: OrthographicCamera,
    *,
    boxes: Iterable[ExpectedBox] = (),
    features: Iterable[ThroughHole | ThroughSlot | ThroughPathSlot] = (),
    labels: bool = False,
    fill: bool = False,
) -> Image.Image:
    """Create an independent expected-geometry image."""

    width = _positive_int(size[0], "width")
    height = _positive_int(size[1], "height")
    blank = Image.new("RGB", (width, height), (255, 255, 255))
    return draw_expected_geometry(
        blank,
        camera,
        boxes=boxes,
        features=features,
        labels=labels,
        fill=fill,
    )


def make_overlay_image(
    actual: Image.Image,
    camera: OrthographicCamera,
    *,
    boxes: Iterable[ExpectedBox] = (),
    features: Iterable[ThroughHole | ThroughSlot | ThroughPathSlot] = (),
    labels: bool = False,
    fill: bool = False,
) -> Image.Image:
    """Draw expected geometry over an actual render."""

    return draw_expected_geometry(
        actual,
        camera,
        boxes=boxes,
        features=features,
        labels=labels,
        fill=fill,
    )


@dataclass(frozen=True)
class VisualViewEvidence:
    """Structured evidence for one consumer-defined visual view."""

    actual_image: str | None
    baseline_status: str
    regression: dict[str, Any] | None = None
    diff_image: str | None = None
    goal_image: str | None = None
    overlay_image: str | None = None
    expected_shape_status: str = "missing"

    def __post_init__(self) -> None:
        allowed_baseline = {"pass", "fail", "missing", "error"}
        allowed_expected = {"pass", "fail", "missing", "error"}
        if self.baseline_status not in allowed_baseline:
            raise VerificationConfigError(
                "baseline_status must be pass, fail, missing or error"
            )
        if self.expected_shape_status not in allowed_expected:
            raise VerificationConfigError(
                "expected_shape_status must be pass, fail, missing or error"
            )
        if self.regression is not None and not isinstance(
            self.regression,
            dict,
        ):
            raise VerificationConfigError(
                "regression must be an evidence object or None"
            )

    def to_evidence(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible visual evidence."""

        return {
            "actual_image": self.actual_image,
            "baseline_status": self.baseline_status,
            "regression": self.regression,
            "diff_image": self.diff_image,
            "goal_image": self.goal_image,
            "overlay_image": self.overlay_image,
            "expected_shape_status": self.expected_shape_status,
        }


def verify_visual_view(
    actual_path: Path,
    *,
    actual_reference: str | None,
    baseline_path: Path | None = None,
    normalized_size: tuple[int, int],
    changed_pixel_threshold: int,
    max_mean_difference: float,
    max_changed_fraction: float,
    diff_path: Path | None,
    diff_reference: str | None = None,
    camera: OrthographicCamera | None = None,
    boxes: Iterable[ExpectedBox] = (),
    features: Iterable[ThroughHole | ThroughSlot | ThroughPathSlot] = (),
    goal_path: Path | None = None,
    goal_reference: str | None = None,
    overlay_path: Path | None = None,
    overlay_reference: str | None = None,
) -> VisualViewEvidence:
    """Verify one already-rendered consumer visual view.

    The caller owns rendering, view policy, cameras, baselines and expected
    model geometry. This function only composes the generic visual primitives
    already provided by this module.
    """

    actual_reference = _evidence_reference(
        actual_reference,
        "actual_reference",
    )
    diff_reference = _evidence_reference(
        diff_reference,
        "diff_reference",
    )
    goal_reference = _evidence_reference(
        goal_reference,
        "goal_reference",
    )
    overlay_reference = _evidence_reference(
        overlay_reference,
        "overlay_reference",
    )
    width, height = _normalized_size(normalized_size)

    configured_boxes = tuple(boxes)
    configured_features = tuple(features)
    has_expected_geometry = bool(
        configured_boxes or configured_features
    )

    if camera is None:
        if has_expected_geometry:
            raise VerificationConfigError(
                "expected geometry requires a camera"
            )
        if goal_path is not None or overlay_path is not None:
            raise VerificationConfigError(
                "goal/overlay output requires a camera"
            )
    else:
        if not isinstance(camera, OrthographicCamera):
            raise VerificationConfigError(
                "camera must be an OrthographicCamera"
            )
        if not has_expected_geometry:
            raise VerificationConfigError(
                "camera requires expected geometry"
            )
        if goal_path is None or overlay_path is None:
            raise VerificationConfigError(
                "goal_path and overlay_path are required with a camera"
            )

    current = normalize_image(actual_path, width, height)
    baseline_status = "missing"
    regression: dict[str, Any] | None = None
    produced_diff_reference: str | None = None
    regression_failed = False

    baseline = None if baseline_path is None else Path(baseline_path)
    if baseline is not None and baseline.is_file():
        if diff_path is None:
            raise VerificationConfigError(
                "diff_path is required when comparing a baseline"
            )
        reference = normalize_image(baseline, width, height)
        write_diff_image(current, reference, diff_path)
        produced_diff_reference = diff_reference
        try:
            regression = compare_images(
                current,
                reference,
                changed_pixel_threshold=changed_pixel_threshold,
                max_mean_difference=max_mean_difference,
                max_changed_fraction=max_changed_fraction,
            )
            baseline_status = "pass"
        except VerificationFailure as exc:
            baseline_status = "fail"
            regression = dict(exc.evidence)
            regression_failed = True

    expected_shape_status = "missing"
    produced_goal_reference: str | None = None
    produced_overlay_reference: str | None = None

    if camera is not None:
        actual_rgb = _load_rgb_image(actual_path)
        goal = make_goal_image(
            actual_rgb.size,
            camera,
            boxes=configured_boxes,
            features=configured_features,
        )
        overlay = make_overlay_image(
            actual_rgb,
            camera,
            boxes=configured_boxes,
            features=configured_features,
        )
        _write_png(goal, Path(goal_path))
        _write_png(overlay, Path(overlay_path))
        produced_goal_reference = goal_reference
        produced_overlay_reference = overlay_reference
        expected_shape_status = "pass"

    evidence = VisualViewEvidence(
        actual_image=actual_reference,
        baseline_status=baseline_status,
        regression=regression,
        diff_image=produced_diff_reference,
        goal_image=produced_goal_reference,
        overlay_image=produced_overlay_reference,
        expected_shape_status=expected_shape_status,
    )

    if regression_failed:
        raise VerificationFailure(
            "visual view regression exceeds configured limits",
            evidence=evidence.to_evidence(),
        )
    return evidence

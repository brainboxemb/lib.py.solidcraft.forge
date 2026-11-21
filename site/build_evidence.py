"""Load accepted Forge evidence from one materialized generic build/main scope.

This module is deliberately presentation-neutral. It validates the durable
source-path item layout and returns normalized evidence without rendering HTML,
running CAD or reconstructing human engineering explanation.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any, Iterable


IMPLEMENTATIONS = ("pythonscad", "pybosl2", "cadquery", "build123d")


@dataclass(frozen=True)
class ItemEvidence:
    """Generic durable item identity and accepted run status."""

    path: str
    item_id: str
    source_commit: str
    status: str
    final_step: str


@dataclass(frozen=True)
class ReferenceEvidence:
    """One accepted independent reference child item."""

    implementation: str
    item: ItemEvidence
    verification: dict[str, Any]
    stl_path: Path
    preview_path: Path
    preview: dict[str, Any]


@dataclass(frozen=True)
class ExampleBuildEvidence:
    """Accepted durable evidence for one verified Forge example."""

    slug: str
    item: ItemEvidence
    command_path: Path
    verification_path: Path
    verification: dict[str, Any]
    measurements_path: Path
    measurements: dict[str, Any]
    native_model_path: Path
    native_step_path: Path
    native_results_path: Path
    preview_path: Path
    preview: dict[str, Any]
    visual_path: Path | None
    visual: dict[str, Any] | None
    saved_designs: tuple[tuple[str, Path, dict[str, Any]], ...]
    references: tuple[ReferenceEvidence, ...]


@dataclass(frozen=True)
class StableBuildEvidence:
    """One complete accepted build/main input for stable Pages."""

    root: Path
    build_commit: str
    manifest_source_commit: str
    examples: tuple[ExampleBuildEvidence, ...]
    verification_wheel_path: Path
    diagram_provenance_path: Path
    diagram_provenance: dict[str, Any]
    diagram_paths: tuple[Path, ...]

    def relative_path(self, path: Path) -> str:
        """Return one artifact path relative to the durable main scope."""
        return Path(path).resolve().relative_to(self.root).as_posix()

    def raw_url(self, path: Path) -> str:
        """Return one immutable raw.githubusercontent evidence URL."""
        relative = self.relative_path(path)
        return (
            "https://raw.githubusercontent.com/"
            "brainboxemb/lib.py.solidcraft.forge/"
            f"{self.build_commit}/main/{relative}"
        )

    def blob_url(self, path: Path) -> str:
        """Return one immutable GitHub blob evidence URL."""
        relative = self.relative_path(path)
        return (
            "https://github.com/brainboxemb/lib.py.solidcraft.forge/blob/"
            f"{self.build_commit}/main/{relative}"
        )


def _json_object(path: Path, label: str) -> dict[str, Any]:
    """Load one JSON object with a concise evidence error."""

    path = Path(path)
    if not path.is_file():
        raise ValueError(f"{label} is missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{label} is invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain one JSON object: {path}")
    return value


def _nonempty_file(path: Path, label: str) -> Path:
    """Require one existing non-empty durable artifact."""

    path = Path(path)
    if not path.is_file() or path.stat().st_size <= 0:
        raise ValueError(f"{label} is missing or empty: {path}")
    return path


def _relative_artifact(root: Path, value: str, label: str) -> Path:
    """Resolve one safe item-relative artifact path."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty relative path")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"{label} escapes its item root: {value}")
    return _nonempty_file(root / relative, label)


def _item(
    root: Path,
    manifest_items: dict[str, Any],
    source_path: str,
) -> ItemEvidence:
    """Load one generic build manifest row plus its public item evidence."""

    row = manifest_items.get(source_path)
    if not isinstance(row, dict):
        raise ValueError(f"build/main is missing item: {source_path}")
    source_commit = row.get("source_commit")
    item_id = row.get("item_id")
    final_step = row.get("final_step")
    for label, value in (
        ("source_commit", source_commit),
        ("item_id", item_id),
        ("final_step", final_step),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{source_path}: invalid {label}")

    item_json = _json_object(
        root / source_path / ".cad-ci" / "item.json",
        f"{source_path} item evidence",
    )
    status = item_json.get("status")
    if status not in {"pass", "fail", "error", "skipped"}:
        raise ValueError(f"{source_path}: invalid item status: {status!r}")
    return ItemEvidence(
        path=source_path,
        item_id=item_id,
        source_commit=source_commit,
        status=status,
        final_step=final_step,
    )


def _presentation(
    evidence_root: Path,
    presentation_root: Path,
    label: str,
) -> tuple[Path, dict[str, Any]]:
    """Load one current durable presentation preview and its provenance."""

    metadata_path = presentation_root / "preview.json"
    metadata = _json_object(metadata_path, f"{label} preview metadata")
    if metadata.get("schema") != 1:
        raise ValueError(f"{label}: unsupported preview schema")
    if metadata.get("kind") != "presentation-preview":
        raise ValueError(f"{label}: invalid preview kind")
    if metadata.get("view") != "iso":
        raise ValueError(f"{label}: presentation preview must be iso")
    image = metadata.get("image")
    preview_path = _relative_artifact(
        presentation_root,
        image,
        f"{label} preview image",
    )
    source = metadata.get("source")
    _relative_artifact(evidence_root, source, f"{label} preview source")
    return preview_path, metadata


def _reference(
    root: Path,
    manifest_items: dict[str, Any],
    slug: str,
    implementation: str,
) -> ReferenceEvidence:
    """Load one accepted reference child from its canonical source-path item."""

    source_path = f"examples/{slug}/{implementation}"
    item = _item(root, manifest_items, source_path)
    if item.status != "pass":
        raise ValueError(
            f"{slug}/{implementation}: durable reference item is not pass"
        )
    item_root = root / source_path
    result_root = (
        item_root / "references" / slug / implementation
    )
    verification = _json_object(
        result_root / "verification.json",
        f"{slug}/{implementation} reference verification",
    )
    if verification.get("implementation") != implementation:
        raise ValueError(
            f"{slug}/{implementation}: verification implementation mismatch"
        )
    if verification.get("status") != "pass":
        raise ValueError(
            f"{slug}/{implementation}: reference is not accepted/pass"
        )
    presentation = verification.get("presentation")
    if not isinstance(presentation, dict) or presentation.get("status") != "pass":
        raise ValueError(
            f"{slug}/{implementation}: durable presentation preview did not pass"
        )

    stl_path = _nonempty_file(
        result_root / "model.stl",
        f"{slug}/{implementation} STL",
    )
    preview_path, preview = _presentation(
        result_root,
        result_root / "presentation",
        f"{slug}/{implementation}",
    )
    return ReferenceEvidence(
        implementation=implementation,
        item=item,
        verification=verification,
        stl_path=stl_path,
        preview_path=preview_path,
        preview=preview,
    )


def _saved_designs(
    model_verify: Path,
) -> tuple[tuple[str, Path, dict[str, Any]], ...]:
    """Load all durable saved-design measurement records in stable order."""

    root = model_verify / "saved_designs"
    if not root.is_dir():
        return ()
    rows = []
    for path in sorted(root.glob("*/measurements.json")):
        rows.append(
            (
                path.parent.name,
                path,
                _json_object(path, f"{path.parent.name} saved-design measurements"),
            )
        )
    return tuple(rows)


def _example(
    root: Path,
    manifest_items: dict[str, Any],
    slug: str,
) -> ExampleBuildEvidence:
    """Load one accepted model item and all four independent references."""

    source_path = f"examples/{slug}"
    item = _item(root, manifest_items, source_path)
    if item.status != "pass":
        raise ValueError(f"{slug}: durable model item is not pass")

    item_root = root / source_path
    command_path = _nonempty_file(
        item_root / "solidcraft.json",
        f"{slug} SolidCraft command document",
    )
    model_verify = item_root / "model_verify"
    verification_path = model_verify / "verification.json"
    verification = _json_object(
        verification_path,
        f"{slug} model verification",
    )
    if verification.get("status") != "pass":
        raise ValueError(f"{slug}: model verification is not pass")

    measurements_path = model_verify / "baseline" / "measurements.json"
    measurements = _json_object(
        measurements_path,
        f"{slug} baseline measurements",
    )
    preview_path, preview = _presentation(
        model_verify,
        model_verify / "presentation",
        slug,
    )

    native_model_path = _nonempty_file(
        model_verify / "native" / "model.sc",
        f"{slug} native SolidCraft model",
    )
    native_step_path = _nonempty_file(
        model_verify / "native" / "model.step",
        f"{slug} native STEP",
    )
    native_results_path = _nonempty_file(
        model_verify / "native" / "results.json",
        f"{slug} native results",
    )

    visual_path = model_verify / "visual.json"
    if not visual_path.is_file():
        raise ValueError(f"{slug}: visual verification is missing")
    visual = _json_object(visual_path, f"{slug} visual verification")
    if visual.get("status") != "pass":
        raise ValueError(f"{slug}: visual verification is not pass")
    views = visual.get("views")
    if not isinstance(views, list) or not views:
        raise ValueError(f"{slug}: visual verification has no views")
    regression_views = 0
    expected_shape_views = 0
    for row in views:
        if not isinstance(row, dict):
            raise ValueError(f"{slug}: visual view must be an object")
        view_evidence = row.get("evidence")
        if not isinstance(view_evidence, dict):
            raise ValueError(f"{slug}: visual view has no evidence object")

        regression_required = row.get("regression_required", True)
        expected_shape_required = row.get("expected_shape_required", True)
        if not isinstance(regression_required, bool):
            raise ValueError(
                f"{slug}: visual regression_required must be boolean"
            )
        if not isinstance(expected_shape_required, bool):
            raise ValueError(
                f"{slug}: visual expected_shape_required must be boolean"
            )
        if not regression_required and not expected_shape_required:
            raise ValueError(
                f"{slug}: visual view has no verification role"
            )

        _relative_artifact(
            model_verify,
            view_evidence.get("actual_image"),
            f"{slug} visual {row.get('view')} actual_image",
        )
        if regression_required:
            regression_views += 1
            _relative_artifact(
                model_verify,
                view_evidence.get("diff_image"),
                f"{slug} visual {row.get('view')} diff_image",
            )
        if expected_shape_required:
            expected_shape_views += 1
            for key in ("goal_image", "overlay_image"):
                _relative_artifact(
                    model_verify,
                    view_evidence.get(key),
                    f"{slug} visual {row.get('view')} {key}",
                )

    if regression_views <= 0:
        raise ValueError(f"{slug}: visual verification has no regression views")
    if expected_shape_views <= 0:
        raise ValueError(
            f"{slug}: visual verification has no expected-shape views"
        )

    references = tuple(
        _reference(root, manifest_items, slug, implementation)
        for implementation in IMPLEMENTATIONS
    )

    return ExampleBuildEvidence(
        slug=slug,
        item=item,
        command_path=command_path,
        verification_path=verification_path,
        verification=verification,
        measurements_path=measurements_path,
        measurements=measurements,
        native_model_path=native_model_path,
        native_step_path=native_step_path,
        native_results_path=native_results_path,
        preview_path=preview_path,
        preview=preview,
        visual_path=visual_path,
        visual=visual,
        saved_designs=_saved_designs(model_verify),
        references=references,
    )


def load_stable_build_evidence(
    root: Path,
    build_commit: str,
    slugs: Iterable[str],
) -> StableBuildEvidence:
    """Load the complete stable-Pages evidence set from one build/main tree."""

    root = Path(root).resolve()
    if (
        not isinstance(build_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", build_commit.strip()) is None
    ):
        raise ValueError("build_commit must be one full immutable Git SHA")

    manifest = _json_object(root / "build.json", "build/main manifest")
    if manifest.get("schema") != 1 or manifest.get("scope") != "main":
        raise ValueError("stable Pages requires build schema 1 scope main")
    manifest_source_commit = manifest.get("source_commit")
    if (
        not isinstance(manifest_source_commit, str)
        or not manifest_source_commit.strip()
    ):
        raise ValueError("build/main manifest has no source_commit")
    manifest_items = manifest.get("items")
    if not isinstance(manifest_items, dict):
        raise ValueError("build/main manifest has no item map")

    normalized_slugs = tuple(sorted(set(slugs)))
    if not normalized_slugs:
        raise ValueError("stable Pages requires at least one verified example")
    examples = tuple(
        _example(root, manifest_items, slug)
        for slug in normalized_slugs
    )

    wheels = tuple(
        sorted(
            (
                root
                / "ci"
                / "cad-verification-package"
                / "dist"
            ).glob("brainboxemb_cad_verification_lib-*.whl")
        )
    )
    if len(wheels) != 1:
        raise ValueError(
            "stable Pages requires exactly one durable CAD verification wheel"
        )
    verification_wheel_path = _nonempty_file(
        wheels[0],
        "durable CAD verification wheel",
    )

    diagram_base = root / "ci" / "verification-diagrams" / "diagrams"
    diagram_provenance_path = diagram_base / "provenance.json"
    diagram_provenance = _json_object(
        diagram_provenance_path,
        "CADCraft diagram provenance",
    )
    if diagram_provenance.get("status") != "pass":
        raise ValueError("stable Pages requires accepted CADCraft diagrams")

    diagram_root = diagram_base / "rendered"
    diagram_paths = tuple(
        path
        for path in sorted(diagram_root.glob("*.svg"))
        if path.is_file() and path.stat().st_size > 0
    )
    if not diagram_paths:
        raise ValueError("stable Pages requires durable CADCraft diagrams")

    return StableBuildEvidence(
        root=root,
        build_commit=build_commit.strip(),
        manifest_source_commit=manifest_source_commit,
        examples=examples,
        verification_wheel_path=verification_wheel_path,
        diagram_provenance_path=diagram_provenance_path,
        diagram_provenance=diagram_provenance,
        diagram_paths=diagram_paths,
    )

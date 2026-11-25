"""Project public model metadata and link durable build artifacts without copying them."""
import json
from pathlib import Path
import re
import tomllib
import yaml

from .presentation import expected_setup, setup_svg, implementation_evidence


_ID = re.compile(r"[a-z0-9][a-z0-9_-]*")


def _purposes(meta):
    raw = meta.get("purpose", [])
    return [raw] if isinstance(raw, str) else raw


def _repository(source_root):
    path = source_root / "site/config/_default/hugo.toml"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    value = data.get("params", {}).get("cadSourceRepository")
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing params.cadSourceRepository: {path}")
    return value


def _verification_sections(source_root: Path) -> tuple[dict[str, dict], list[dict]]:
    path = source_root / "docs/verification/sections.yml"
    if not path.is_file():
        raise ValueError(f"missing verification sections: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sections = data.get("sections")
    if data.get("schema") != 1 or not isinstance(sections, dict) or not sections:
        raise ValueError(f"invalid verification sections: {path}")

    rows = []
    normalized = {}
    for section_id, section in sections.items():
        if (
            not isinstance(section_id, str)
            or not _ID.fullmatch(section_id)
            or not isinstance(section, dict)
            or not isinstance(section.get("priority"), int)
            or not isinstance(section.get("label"), str)
            or not section["label"]
            or not isinstance(section.get("description"), str)
            or not section["description"]
        ):
            raise ValueError(f"invalid verification section: {section_id!r}")
        row = {
            "id": section_id,
            "priority": section["priority"],
            "label": section["label"],
            "description": section["description"],
            "models": [],
        }
        rows.append(row)
        normalized[section_id] = row

    rows.sort(key=lambda row: (row["priority"], row["id"]))
    return normalized, rows


def _stage_lines(*, evidence, blob_base, impl_path, stages):
    if stages is None:
        return []
    if not isinstance(stages, dict):
        raise ValueError("verification_stages must be a mapping")

    lines = []
    for stage_id, state in sorted(stages.items()):
        if (
            not isinstance(stage_id, str)
            or not _ID.fullmatch(stage_id)
            or not isinstance(state, dict)
        ):
            raise ValueError("invalid verification stage evidence")
        details = [f"status={state.get('status')}"]
        if state.get("adapter"):
            details.append(f"adapter={state['adapter']}")
        if state.get("runtime"):
            details.append(f"runtime={state['runtime']}")
        report = (
            evidence
            / "verification"
            / stage_id
            / "verification.json"
        )
        suffix = ""
        if report.is_file():
            url = (
                f"{blob_base}{impl_path}/verification/"
                f"{stage_id}/verification.json"
            )
            suffix = f" · [verification]({url})"
        lines.append(
            f"  - `{stage_id}`: " + ", ".join(details) + suffix
        )
    return lines


def prepare_models(source_root: Path, site: Path, build_scope: Path | None):
    owners = source_root / "models"
    if not owners.is_dir():
        return

    repository = _repository(source_root)
    verification_sections, verification_section_rows = _verification_sections(source_root)
    namespace = build_scope.name if build_scope else None
    blob_base = (
        f"https://github.com/{repository}/blob/build/{namespace}/"
        if namespace else None
    )
    raw_base = (
        f"https://raw.githubusercontent.com/{repository}/build/{namespace}/"
        if namespace else None
    )

    seen = set()
    for model_yml in sorted(owners.rglob("model.yml")):
        owner = model_yml.parent
        ci_path = owner / "ci.yml"
        if not ci_path.is_file():
            continue
        meta = yaml.safe_load(model_yml.read_text()) or {}
        purposes = _purposes(meta)
        if not purposes:
            continue
        if not isinstance(purposes, list) or set(purposes) - {"example", "verification"}:
            raise ValueError(f"invalid model purposes: {model_yml}")
        ci = yaml.safe_load(ci_path.read_text()) or {}
        item = ci.get("id")
        if not isinstance(item, str) or not _ID.fullmatch(item) or item in seen:
            raise ValueError(f"invalid model id: {ci_path}")

        seen.add(item)
        if "verification" in purposes:
            verification_section = meta.get("section")
            if verification_section not in verification_sections:
                raise ValueError(
                    f"unknown verification section {verification_section!r}: {model_yml}"
                )
        else:
            verification_section = None

        title = str(meta.get("title", item))
        if verification_section is not None:
            verification_sections[verification_section]["models"].append({
                "id": item,
                "priority": meta.get("priority", 100),
                "title": title,
            })
        implementations = ci.get("implementations", [])
        featured = meta.get("presentation_primary", ci.get("primary", ""))
        if implementations and featured not in {i["id"] for i in implementations}:
            raise ValueError(f"invalid presentation_primary: {model_yml}")
        params = {
            "model": meta,
            "primary": featured,
            "buildprimary": ci.get("primary", ""),
            "status": "unavailable",
            "previewurl": "",
            "files": [],
            "sources": [],
        }
        for implementation in ci.get("implementations", []):
            source = owner / implementation["source"]
            if not source.resolve().is_relative_to(owner.resolve()) or not source.is_file():
                raise ValueError(f"missing or unsafe model source: {source}")
            params["sources"].append({
                "id": implementation["id"],
                "builder": implementation.get("builder", ""),
                "native": implementation.get("builder") in ("builder-solidcraft", "builder-scpf") and implementation.get("preview") is False,
                "path": implementation["source"],
                "lang": {".py": "python", ".json": "json", ".scad": "openscad"}.get(source.suffix, "text"),
                "content": source.read_text(encoding="utf-8"),
            })
        background = owner / "page.md"
        if background.is_file():
            params["background"] = background.read_text(encoding="utf-8")
        lines = []

        evidence = build_scope / "models" / item if build_scope else None
        if evidence and (evidence / "result.json").is_file():
            result = json.loads((evidence / "result.json").read_text())
            if result.get("status") != "pass" or result.get("id") != item:
                raise ValueError(f"invalid published model evidence: {item}")
            revision = json.loads((evidence / "source.json").read_text())["source_sha"]
            primary = result.get("primary")
            params.update(status="pass", buildprimary=primary)
            owner_path = f"models/{item}"
            lines += [
                f"- Primary implementation: `{primary}`",
                f"- Build source: `{revision}`",
                f"- Durable scope: `{namespace}`",
                "",
            ]
            # The owner-level image may belong to a different build primary.
            # Never use it as a fallback for the featured implementation.
            for name, label in (
                ("model.stl", "STL"), ("model.step", "STEP"),
                ("model.sc", "SolidCraft .sc"), ("solidcraft.json", "Commands"),
                ("result.json", "Build result"), ("source.json", "Build provenance"),
            ):
                if (evidence / name).is_file():
                    params["files"].append({"label": label, "url": f"{blob_base}{owner_path}/{name}"})
            lines += ["### Implementations", ""]
            for source in params["sources"]:
                impl_id = source["id"]
                source.update(implementation_evidence(
                    evidence / impl_id, f"{blob_base}{owner_path}/{impl_id}",
                    f"{raw_base}{owner_path}/{impl_id}",
                    result.get("implementations", {}).get(impl_id, {}),
                ))
                if impl_id == featured:
                    params["previewurl"] = source["previewurl"]
            for impl_id, state in sorted(result.get("implementations", {}).items()):
                if not isinstance(state, dict):
                    raise ValueError(f"invalid implementation evidence: {impl_id}")
                impl_path = f"{owner_path}/{impl_id}"
                impl_evidence = evidence / impl_id
                links = []
                for name, label in (
                    ("model.stl", "STL"),
                    ("model.sc", "SC"),
                    ("model.step", "STEP"),
                    ("model.png", "Preview"),
                    ("solidcraft.json", "commands"),
                    ("verification/verification.json", "verification"),
                    ("result.json", "result"),
                ):
                    if (impl_evidence / name).is_file():
                        links.append(f"[{label}]({blob_base}{impl_path}/{name})")
                suffix = " · " + " · ".join(links) if links else ""
                lines.append(
                    f"- **{impl_id}** — {state.get('builder')}: "
                    f"build={state.get('build_status')}, "
                    f"verification={state.get('verification_status')}{suffix}"
                )
                lines.extend(
                    _stage_lines(
                        evidence=impl_evidence,
                        blob_base=blob_base,
                        impl_path=impl_path,
                        stages=state.get("verification_stages"),
                    )
                )
        else:
            lines.append("No published build evidence is available for this source scope.")

        bodies, expectation_source = expected_setup(owner, ci, evidence)
        diagram = setup_svg(bodies)
        params["expectationsource"] = expectation_source
        for purpose in dict.fromkeys(purposes):
            section = "examples" if purpose == "example" else "verification"
            page = site / "content" / section / item / "index.md"
            page.parent.mkdir(parents=True, exist_ok=True)
            if diagram:
                (page.parent / "setup.svg").write_text(diagram, encoding="utf-8")
            page_params = dict(params)
            if purpose == "verification":
                page_params["verificationsection"] = verification_section
            data = {"title": title, "type": "models", "weight": meta.get("priority", 100),
                    "params": page_params}
            if purpose == ("example" if "example" in purposes else "verification"):
                data["aliases"] = [f"/models/{item}/"]
            page.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n\n"
                + "\n".join(lines).rstrip() + "\n", encoding="utf-8"
            )

    for section in verification_section_rows:
        section["models"].sort(key=lambda model: (model["priority"], model["id"]))
    target = site / "data/cad/verification_sections.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {"schema": 1, "sections": verification_section_rows},
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

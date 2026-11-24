"""Project public model metadata and link durable build artifacts without copying them."""
import json
from pathlib import Path
import re
import tomllib
import yaml


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


def prepare_models(source_root: Path, site: Path, build_scope: Path | None):
    owners = source_root / "models"
    if not owners.is_dir():
        return

    repository = _repository(source_root)
    namespace = build_scope.name if build_scope else None
    blob_base = (
        f"https://github.com/{repository}/blob/build/{namespace}/"
        if namespace else None
    )
    raw_base = (
        f"https://raw.githubusercontent.com/{repository}/build/{namespace}/"
        if namespace else None
    )

    for model_yml in sorted(owners.rglob("model.yml")):
        owner = model_yml.parent
        ci_path = owner / "ci.yml"
        if not ci_path.is_file():
            continue
        meta = yaml.safe_load(model_yml.read_text()) or {}
        if "example" not in _purposes(meta):
            continue
        ci = yaml.safe_load(ci_path.read_text()) or {}
        item = ci.get("id")
        if not isinstance(item, str) or not _ID.fullmatch(item):
            raise ValueError(f"invalid model id: {ci_path}")

        title = str(meta.get("title", item))
        page = site / "content" / "models" / item / "index.md"
        page.parent.mkdir(parents=True, exist_ok=True)
        description = str(meta.get("description", "")).strip()
        lines = [
            "---",
            "title: " + json.dumps(title),
            "---",
            "",
            description,
            "",
            "## Build evidence",
            "",
        ]

        evidence = build_scope / "models" / item if build_scope else None
        if evidence and (evidence / "result.json").is_file():
            result = json.loads((evidence / "result.json").read_text())
            if result.get("status") != "pass" or result.get("id") != item:
                raise ValueError(f"invalid published model evidence: {item}")
            revision = json.loads((evidence / "source.json").read_text())["source_sha"]
            primary = result.get("primary")
            owner_path = f"models/{item}"
            lines += [
                f"- Primary implementation: `{primary}`",
                f"- Build source: `{revision}`",
                f"- Durable scope: `{namespace}`",
                "",
            ]
            if (evidence / "model.png").is_file():
                lines += [
                    f"![{title} preview]({raw_base}{owner_path}/model.png)",
                    "",
                ]
            if (evidence / "model.stl").is_file():
                lines += [
                    f"[View primary STL on GitHub]({blob_base}{owner_path}/model.stl)",
                    "",
                ]
            lines += ["### Implementations", ""]
            for impl_id, state in sorted(result.get("implementations", {}).items()):
                impl_path = f"{owner_path}/{impl_id}"
                links = []
                for name, label in (
                    ("model.stl", "STL"),
                    ("model.sc", "SC"),
                    ("solidcraft.json", "commands"),
                    ("verification/verification.json", "verification"),
                    ("result.json", "result"),
                ):
                    if (evidence / impl_id / name).is_file():
                        links.append(f"[{label}]({blob_base}{impl_path}/{name})")
                suffix = " · " + " · ".join(links) if links else ""
                lines.append(
                    f"- **{impl_id}** — {state.get('builder')}: "
                    f"build={state.get('build_status')}, "
                    f"verification={state.get('verification_status')}{suffix}"
                )
        else:
            lines.append("No published build evidence is available for this source scope.")

        page.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

"""Project published successful example evidence into a temporary Hugo site."""
import json
from pathlib import Path
import re
import shutil
import yaml


def prepare_examples(source_root: Path, site: Path, build_scope: Path | None):
    owners = source_root / "examples"
    if not owners.is_dir():
        return
    for owner in sorted(owners.iterdir()):
        if not (owner / "model.yml").is_file():
            continue
        meta = yaml.safe_load((owner / "model.yml").read_text())
        purpose = meta.get("purpose", [])
        if "example" not in ([purpose] if isinstance(purpose, str) else purpose):
            continue
        item = yaml.safe_load((owner / "ci.yml").read_text())["id"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", item):
            raise ValueError(f"invalid example id: {item}")
        title = str(meta.get("title", item))
        page = site / "content" / "examples" / item / "index.md"
        page.parent.mkdir(parents=True, exist_ok=True)
        lines = ["---", "title: " + json.dumps(title), "---", "", "## Build evidence", ""]
        evidence = build_scope / "examples" / item if build_scope else None
        if evidence and (evidence / "result.json").is_file():
            result = json.loads((evidence / "result.json").read_text())
            if result.get("status") != "pass" or result.get("id") != item:
                raise ValueError(f"invalid published evidence: {item}")
            revision = json.loads((evidence / "source.json").read_text())["source_sha"]
            lines += [f"- Builder: `{result['builder']}`", f"- Verification: **{result['verification_status']}**", f"- Build source: `{revision}`", ""]
            static = site / "static" / "examples" / item
            for rel, label in (("model.stl", "STL model"), ("result.json", "Build result"), ("verification/verification.json", "Verification report")):
                target = static / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(evidence / rel, target)
                lines.append(f"- [{label}](./{rel})")
        else:
            lines.append("No published build evidence is available for this source scope.")
        page.write_text("\n".join(lines) + "\n", encoding="utf-8")

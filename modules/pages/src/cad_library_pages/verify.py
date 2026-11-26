"""Check generated purpose views and durable evidence links."""
import argparse
from html import unescape
import json
import re
from pathlib import Path
import yaml

from .homepage import homepage_manifest
from .landing import landing_metadata


def verify(source_root: Path, site: Path, build_scope: Path | None):
    warning_marker = "data-forge-development-warning"

    def read(route):
        path = site / route / "index.html"
        if not path.is_file():
            raise RuntimeError(f"missing generated route: {path}")
        return unescape(path.read_text(encoding="utf-8"))

    home = read("")
    forge = landing_metadata(source_root)
    homepage = homepage_manifest(source_root, context=forge)
    if "data-generated-homepage" not in home:
        raise RuntimeError("Forge homepage was not rendered from generated Pages data")

    homepage_markers = []
    external_urls = []
    for block in homepage["blocks"]:
        homepage_markers.append(block["title"])
        if block["type"] == "hero":
            homepage_markers.append(block["eyebrow"])
            homepage_markers.extend(block["badges"])
            homepage_markers.extend(action["label"] for action in block["actions"])
            external_urls.extend(
                action["url"] for action in block["actions"] if action["external"]
            )
        elif block["type"] == "flow":
            homepage_markers.extend(step["title"] for step in block["steps"])
        elif block["type"] == "links":
            homepage_markers.extend(item["label"] for item in block["items"])
            external_urls.extend(
                item["url"] for item in block["items"] if item["external"]
            )

    for marker in homepage_markers:
        if marker not in home:
            raise RuntimeError(f"generated Forge homepage content missing: {marker}")
    for url in external_urls:
        if url not in home:
            raise RuntimeError(f"generated Forge homepage destination missing: {url}")

    for route, marker in (("", "cad-home"), ("docs", "Documentation"), ("docs/model-pages", "Understand verification"),
                          ("examples", "cad-model-grid"), ("verification", "cad-model-grid")):
        html = read(route)
        if marker not in html:
            raise RuntimeError(f"missing layout marker for {route}: {marker}")
        if warning_marker not in html:
            raise RuntimeError(f"missing Forge development warning for {route or '/'}")

    sections_path = source_root / "docs/verification/sections.yml"
    sections_data = yaml.safe_load(sections_path.read_text(encoding="utf-8")) or {}
    section_defs = sections_data.get("sections", {})
    verification_models = {}
    for model in sorted((source_root / "models").rglob("model.yml")):
        if not (model.parent / "ci.yml").is_file():
            continue
        meta = yaml.safe_load(model.read_text()) or {}
        purposes = meta.get("purpose", [])
        if isinstance(purposes, str):
            purposes = [purposes]
        if "verification" not in purposes:
            continue
        ci = yaml.safe_load((model.parent / "ci.yml").read_text()) or {}
        verification_models.setdefault(meta.get("section"), []).append(
            (meta.get("priority", 100), ci["id"], str(meta.get("title", ci["id"])))
        )

    verification_html = read("verification")
    if "data-verification-catalog-layout" not in verification_html:
        raise RuntimeError("verification custom catalogue layout was not selected")
    section_rows = sorted(
        section_defs.items(),
        key=lambda item: (item[1]["priority"], item[0]),
    )
    section_positions = []
    for section_id, _definition in section_rows:
        models = sorted(verification_models.get(section_id, []))
        if not models:
            continue
        marker = re.search(
            rf'data-verification-section=(?:"{re.escape(section_id)}"|{re.escape(section_id)})(?=[\s>])',
            verification_html,
        )
        if marker is None:
            discovered = [
                next(value for value in match.groups() if value is not None)
                for match in re.finditer(
                    r'data-verification-section=(?:"([^"]+)"|([^\s>]+))',
                    verification_html,
                )
            ]
            raise RuntimeError(
                f"verification section missing: {section_id}; "
                f"discovered={discovered}; "
                f"catalog_shell={'cad-page-shell cad-catalog-page' in verification_html}"
            )
        position = marker.start()
        section_positions.append(position)
        next_marker = re.search(
            r'data-verification-section=',
            verification_html[marker.end():],
        )
        end = marker.end() + next_marker.start() if next_marker else None
        section_html = verification_html[position:end]
        model_positions = [section_html.find(title) for _priority, _item, title in models]
        if -1 in model_positions or model_positions != sorted(model_positions):
            raise RuntimeError(
                f"verification model ordering is incorrect in section {section_id}"
            )
    if section_positions != sorted(section_positions):
        raise RuntimeError("verification section ordering is incorrect")

    for route in (
        "guide",
        "reference",
        "cheatsheet",
        "verification/coverage",
        "verification/results",
        "verification/joint-anatomy",
    ):
        if (site / route / "index.html").is_file():
            if warning_marker not in read(route):
                raise RuntimeError(f"missing Forge development warning for {route}")

    for model in sorted((source_root / "models").rglob("model.yml")):
        if not (model.parent / "ci.yml").is_file():
            continue
        meta = yaml.safe_load(model.read_text()) or {}
        ci = yaml.safe_load((model.parent / "ci.yml").read_text()) or {}
        purposes = meta.get("purpose", [])
        if isinstance(purposes, str):
            purposes = [purposes]
        item = ci["id"]
        for purpose, section in (("example", "examples"), ("verification", "verification")):
            route = f"{section}/{item}"
            if purpose not in purposes:
                if (site / route / "index.html").exists():
                    raise RuntimeError(f"unexpected purpose view: {route}")
                continue
            html = read(route)
            if warning_marker not in html:
                raise RuntimeError(f"{route}: missing Forge development warning")
            expected = ["cad-model-detail", str(meta.get("title", item)), "Build and verification"]
            featured = meta.get("presentation_primary", ci.get("primary"))
            order = ["expected-setup", "featured-result", "primary-source", "reference-code", "image-overview", "check-overview", "build-verification"]
            if not ci.get("implementations"):
                order.remove("primary-source")
            positions = [html.find(marker) for marker in order]
            if -1 in positions or positions != sorted(positions):
                raise RuntimeError(f"{route}: model reading order is incorrect: {order}")
            featured_source = next(
                (
                    implementation.get("source")
                    for implementation in ci.get("implementations", [])
                    if implementation["id"] == featured
                ),
                None,
            )
            for implementation in ci.get("implementations", []):
                shared_source = (
                    implementation["id"] != featured
                    and implementation.get("source") == featured_source
                )
                label = "result" if shared_source else "source"
                expected.append(f'{implementation["id"]} {label}')
            evidence = build_scope / "models" / item if build_scope else None
            if evidence and (evidence / "result.json").is_file():
                result = json.loads((evidence / "result.json").read_text())
                expected.append(json.loads((evidence / "source.json").read_text())["source_sha"])
                featured_path = f"/build/{build_scope.name}/models/{item}/{featured}/model.png"
                if (evidence / str(featured) / "model.png").is_file():
                    expected.append(featured_path)
                    overview = html[html.find("featured-result"):html.find("primary-source")]
                    if featured_path not in overview or f"/build/{build_scope.name}/models/{item}/model.png" in overview:
                        raise RuntimeError(f"{route}: featured result must use its own implementation image")
                    native = next((i for i in ci.get("implementations", []) if i["id"] == featured), {})
                    if native.get("builder") in ("builder-solidcraft", "builder-scpf") and native.get("preview") is False:
                        expected.append("SolidCraft native snapshot")
                if (evidence / "model.stl").is_file():
                    expected.append(f"/blob/build/{build_scope.name}/models/{item}/model.stl")
                for impl, state in result.get("implementations", {}).items():
                    impl_root = evidence / impl
                    command_file = next(
                        (
                            name
                            for name in ("solidcraft.json", "mitcad.json")
                            if (impl_root / name).is_file()
                        ),
                        None,
                    )
                    if command_file and any(i["id"] == impl for i in ci.get("implementations", [])):
                        expected.append(f"Generated command sequence — {impl}")
                        expected.append(
                            f"/blob/build/{build_scope.name}/models/{item}/{impl}/{command_file}"
                        )
                        if not html.find("primary-source") < html.find("cad-command-section") < html.find("reference-code"):
                            raise RuntimeError(f"{route}: generated commands must follow source and precede references")
                        details = re.findall(r"<details\b[^>]*cad-command-section[^>]*>", html)
                        if not details or any(re.search(r"\sopen(?:[\s=>]|$)", tag) for tag in details):
                            raise RuntimeError(f"{route}: generated commands must be collapsed")
                    if (impl_root / "model.mitcad").is_file():
                        expected.append(
                            f"/blob/build/{build_scope.name}/models/{item}/{impl}/model.mitcad"
                        )
                    drawings_root = impl_root / "drawings"
                    if drawings_root.is_dir():
                        pdfs = sorted(drawings_root.glob("*.pdf"))
                        for pdf in pdfs:
                            expected.append(
                                f"/build/{build_scope.name}/models/{item}/{impl}/drawings/{pdf.name}"
                            )
                            png = pdf.with_suffix(".png")
                            if png.is_file():
                                expected.append(
                                    f"/build/{build_scope.name}/models/{item}/{impl}/drawings/{png.name}"
                                )
                        if featured == impl and pdfs:
                            if "drawing-sheet" not in html:
                                raise RuntimeError(
                                    f"{route}: missing drawing sheet presentation"
                                )
                            if "<iframe" in html or "<object" in html or "<embed" in html:
                                raise RuntimeError(
                                    f"{route}: drawing PDF must not auto-embed"
                                )

                    if (impl_root / "model.png").is_file() and any(i["id"] == impl for i in ci.get("implementations", [])):
                        preview = f"/build/{build_scope.name}/models/{item}/{impl}/model.png"
                        expected.append(preview)
                        gallery = html[html.find("image-overview"):html.find("check-overview")]
                        if preview not in gallery:
                            raise RuntimeError(f"{route}: missing implementation image in gallery: {impl}")
                    for stage in state.get("verification_stages", {}):
                        report = f"{impl}/verification/{stage}/verification.json"
                        if (evidence / report).is_file():
                            expected.append(f"/blob/build/{build_scope.name}/models/{item}/{report}")
            explanation = html.find("engineering-explanation")
            if explanation != -1 and explanation < html.find("check-overview"):
                raise RuntimeError(f"{route}: engineering explanation must follow image/check overview")
            stages = html.find("model-stages")
            if stages != -1 and stages < html.find("check-overview"):
                raise RuntimeError(f"{route}: model stages must follow image/check overview")
            if "setup.svg" in html:
                gallery = html[html.find("image-overview"):html.find("check-overview")]
                if "setup.svg" not in gallery:
                    raise RuntimeError(f"{route}: expected setup missing from image overview")
            for marker in expected:
                if marker not in html:
                    raise RuntimeError(f"{route}: missing rendered content: {marker}")
            for artifact in (
                "model.png",
                "model.stl",
                "model.sc",
                "model.mitcad",
                "solidcraft.json",
                "mitcad.json",
                "result.json",
            ):
                if (site / route / artifact).exists():
                    raise RuntimeError(f"generated CAD artifact copied into Pages: {route}/{artifact}")
            if list((site / route).rglob("*.pdf")):
                raise RuntimeError(
                    f"generated drawing PDF copied into Pages: {route}"
                )
            if list((site / route).rglob("*.png")):
                copied = [
                    path for path in (site / route).rglob("*.png")
                    if "setup" not in path.name
                ]
                if copied:
                    raise RuntimeError(
                        f"generated drawing/model PNG copied into Pages: {route}"
                    )

    parity_path = source_root / "docs" / "pages-parity.json"
    if parity_path.is_file():
        parity = json.loads(parity_path.read_text(encoding="utf-8"))
        if parity.get("schema") != 1 or not isinstance(parity.get("routes"), list):
            raise RuntimeError(f"invalid Pages parity manifest: {parity_path}")
        for row in parity["routes"]:
            route = row.get("path")
            if not isinstance(route, str) or not route or route.startswith("/") or ".." in route:
                raise RuntimeError(f"invalid Pages parity route: {route!r}")
            target = site / route if route.endswith(".html") else site / route / "index.html"
            if not target.is_file():
                raise RuntimeError(f"historical Pages route missing: {route}")
            html = unescape(target.read_text(encoding="utf-8"))
            for expected in row.get("contains", []):
                if expected not in html:
                    raise RuntimeError(f"historical Pages content missing at {route}: {expected}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--build-scope", type=Path)
    args = parser.parse_args()
    verify(args.source_root, args.site, args.build_scope)


if __name__ == "__main__":
    main()

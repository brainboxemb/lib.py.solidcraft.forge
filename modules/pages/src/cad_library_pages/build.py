"""Build the library site without executing CAD or library code."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

from .api_reference import prepare_api_reference
from .cheatsheet import prepare_cheatsheet
from .documentation import prepare_documentation
from .guides import prepare_guides
from .homepage import prepare_homepage
from .landing import prepare_landing
from .models import prepare_models
from .verification_special import prepare_verification_special


def build(*, source_root: Path, destination: Path, base_url: str, build_scope: Path | None = None):
    source_root = source_root.resolve()
    destination = destination.resolve()
    if build_scope is not None:
        build_scope = build_scope.resolve()
    with tempfile.TemporaryDirectory(prefix="cad-hugo-") as tmp:
        source = Path(tmp) / "site"
        shutil.copytree(source_root / "site", source)
        landing = prepare_landing(source_root, source)
        prepare_homepage(source_root, source, context=landing)
        prepare_documentation(source_root, source)
        prepare_api_reference(source_root, source)
        prepare_guides(source_root, source)
        prepare_cheatsheet(source_root, source)
        prepare_models(source_root, source, build_scope)
        prepare_verification_special(source_root, source, build_scope)
        subprocess.run(
            [
                "hugo",
                "--source", str(source),
                "--destination", str(destination),
                "--baseURL", base_url,
                "--minify",
            ],
            check=True,
        )
    if not (destination / "index.html").is_file():
        raise RuntimeError(f"Hugo did not produce index.html: {destination}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--build-scope", type=Path)
    args = parser.parse_args()
    build(
        source_root=args.source_root,
        destination=args.destination,
        base_url=args.base_url,
        build_scope=args.build_scope,
    )


if __name__ == "__main__":
    main()

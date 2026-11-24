"""Build the library site without executing CAD or library code."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
from .examples import prepare_examples


def build(*, source_root: Path, destination: Path, base_url: str, build_scope: Path | None = None):
    source_root = source_root.resolve()
    destination = destination.resolve()
    if build_scope is not None:
        build_scope = build_scope.resolve()
    with tempfile.TemporaryDirectory(prefix="cad-hugo-") as tmp:
        source = Path(tmp) / "site"
        shutil.copytree(source_root / "site", source)
        prepare_examples(source_root, source, build_scope)
        subprocess.run(["hugo", "--source", str(source), "--destination", str(destination), "--baseURL", base_url, "--minify"], check=True)
    if not (destination / "index.html").is_file():
        raise RuntimeError(f"Hugo did not produce index.html: {destination}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--build-scope", type=Path)
    args = parser.parse_args()
    build(source_root=args.source_root, destination=args.destination, base_url=args.base_url, build_scope=args.build_scope)


if __name__ == "__main__":
    main()

"""Capture actual generated pages using the existing headless Chrome approach."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading


def capture(site: Path, base_path: str, output: Path):
    site, output = site.resolve(), output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    chrome = next((p for n in ("google-chrome", "google-chrome-stable", "chromium") if (p := shutil.which(n))), None)
    if not chrome:
        raise RuntimeError("Chrome/Chromium is required")
    routes = [("home", ""), ("documentation", "docs/"), ("documentation-model-pages", "docs/model-pages/"), ("examples", "examples/"), ("verification", "verification/")]
    for section in ("examples", "verification"):
        routes.extend((f"{section}-{p.parent.name}", f"{section}/{p.parent.name}/")
                      for p in sorted((site / section).glob("*/index.html"))[:1])
    failures = []
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            if len(args) > 1 and str(args[1]) == "404":
                failures.append(str(args[0]))
    with tempfile.TemporaryDirectory(prefix="cad-layout-") as tmp:
        root = Path(tmp)
        web_root = root / "www"
        target = web_root / base_path.strip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(site, target)
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(web_root)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            for name, route in routes:
                if not (site / route / "index.html").is_file():
                    raise RuntimeError(f"missing generated route: {route}")
                views = [("desktop", "1440,1200"), ("mobile", "420,1000")]
                if name.startswith(("examples-", "verification-")):
                    views += [("desktop-full", "1440,5200"), ("mobile-full", "420,6500")]
                for label, dimensions in views:
                    with tempfile.TemporaryDirectory(prefix="chrome-") as profile:
                        screenshot = output / f"{name}-{label}.png"
                        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                                        f"--user-data-dir={profile}", f"--window-size={dimensions}", "--hide-scrollbars",
                                        "--virtual-time-budget=3500", f"--screenshot={screenshot}",
                                        origin + base_path + route], check=True, timeout=45)
                        if not screenshot.is_file() or not screenshot.stat().st_size:
                            raise RuntimeError(f"missing screenshot: {screenshot}")
            (output / "missing-assets.txt").write_text("\n".join(failures), encoding="utf-8")
            if failures:
                raise RuntimeError(f"missing local assets: {failures}")
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--base-path", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    capture(args.site, args.base_path, args.output)


if __name__ == "__main__":
    main()

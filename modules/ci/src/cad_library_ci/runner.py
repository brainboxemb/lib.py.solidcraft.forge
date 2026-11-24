"""Execute internal module tests directly from source."""
import os
import subprocess
import sys
import tomllib


def selected_dependencies(modules):
    dependencies = []
    for module in modules:
        with (module.root / "pyproject.toml").open("rb") as stream:
            project = tomllib.load(stream)["project"]
        dependencies.extend(project.get("dependencies", []))
    return tuple(dict.fromkeys(dependencies))


def execute(modules):
    dependencies = selected_dependencies(modules)
    if dependencies:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *dependencies],
            check=True,
        )

    for module in modules:
        env = dict(os.environ)
        source = str((module.root / "src").resolve())
        previous = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = source + (os.pathsep + previous if previous else "")
        subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(module.root / "tests"), "-v"], env=env, check=True)

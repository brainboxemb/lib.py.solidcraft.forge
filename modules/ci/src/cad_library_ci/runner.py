"""Execute internal module and selected model-owner tests directly from source."""
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


def install_dependencies(dependencies):
    if dependencies:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                *dependencies,
            ],
            check=True,
        )


def execute(modules):
    install_dependencies(selected_dependencies(modules))

    for module in modules:
        env = dict(os.environ)
        source = str((module.root / "src").resolve())
        previous = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = source + (
            os.pathsep + previous if previous else ""
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                str(module.root / "tests"),
                "-v",
            ],
            env=env,
            check=True,
        )


def execute_model_tests(repo, models, library, *, dependencies_installed=False):
    """Run optional owner-local tests for exactly the selected models."""
    tested = tuple(
        (model, model.root / "tests")
        for model in models
        if (model.root / "tests").is_dir()
    )
    if not tested:
        return
    if not dependencies_installed:
        install_dependencies(selected_dependencies((library,)))

    library_source = str((library.root / "src").resolve())
    for model, tests in tested:
        env = dict(os.environ)
        previous = env.get("PYTHONPATH", "")
        entries = [library_source, str(model.root.resolve())]
        if previous:
            entries.append(previous)
        env["PYTHONPATH"] = os.pathsep.join(entries)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                str(tests),
                "-v",
            ],
            cwd=repo,
            env=env,
            check=True,
        )

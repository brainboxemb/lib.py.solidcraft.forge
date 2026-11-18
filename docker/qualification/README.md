# Forge qualification image

This image contains the slow-changing qualification toolchain only.

Tool versions are not configured in this Dockerfile. The qualification
environment has explicit version owners:

- SolidCraft: `scpf/scpf/version.py`;
- Python base image: `qualification/toolchain.json`;
- CADCraft version/checksum: `qualification/toolchain.json`;
- reference-library versions: `qualification/toolchain.json`.

The Python base image is pinned by OCI digest so rebuilding the same toolchain
does not silently move to a different base image.

It contains:

- Python 3.12;
- the pinned SolidCraft CLI;
- the pinned CADCraft CLI;
- PythonSCAD;
- pyBOSL2;
- CadQuery;
- build123d in an isolated virtual environment;
- trimesh, matplotlib, Pillow and PyYAML.

It deliberately does **not** contain Forge source, examples, qualification
contracts or site source. CI mounts the current repository checkout at
`/workspace`.

## Identity

`scripts/qualification_image.py` hashes:

- this Dockerfile;
- `qualification/toolchain.json`.

CI uses the resulting immutable `toolchain-<sha256>` tag. Human-readable
version aliases may be published, but qualification workflows must use the
immutable tag.

## Smoke test

The image build is not publishable until the shared staged case runner passes:

```text
python qualification/case_runner.py simple-box --out <output>
```

The workflow then reruns only the mutation stage against the same output:

```text
python qualification/case_runner.py simple-box --out <output> --stage mutate
```

This proves both the complete vertical case and independent stage reruns without
maintaining a second Docker-specific qualification implementation.


## Compatibility trigger

The image identity changes only when the Dockerfile or toolchain changes.
However, the same isolated workflow reruns the one-case compatibility gate when
the relevant Forge or qualification runner changes. On `main`, if the
immutable GHCR tag already exists, the workflow pulls and tests that exact image
instead of rebuilding or overwriting it.


## Staged consumer smoke

Normal Forge/case-runner changes do not build the container. The
`qualification-smoke.yml` workflow pulls the immutable toolchain image and
executes the shared case runner.

It first runs the complete `simple-box` case, then reruns only `mutate` on
the same output directory. CI asserts that the replay-stage state is unchanged
while the mutation-stage state is renewed.

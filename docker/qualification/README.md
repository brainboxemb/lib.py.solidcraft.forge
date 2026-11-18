# Forge qualification image

This image contains the slow-changing qualification toolchain only.

The Python base image is pinned by OCI digest so rebuilding the same toolchain does not silently move to a different base image.

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

The image build is not publishable until
`qualification/integration/simple_box.py` passes against the current checkout:

`Forge compile -> native SolidCraft replay -> eval -> saved-design parameter
mutation -> native Q4/Q5 validation`.

This intentionally tests one vertical integration path before the full
qualification suite is allowed to consume the image.


## One-case real gate

After the fast vertical smoke passes, the image workflow also executes the
repository's real gate:

```text
verification_gate.py --gate affected-q1-q6 --cases simple-box
```

That deliberately exercises the same Q1-Q6 orchestration later used by PR CI,
but for exactly one qualification case. The complete case set is not used while
developing the container.


## Compatibility trigger

The image identity changes only when the Dockerfile or toolchain changes.
However, the same isolated workflow reruns the one-case compatibility gate when
the relevant Forge or qualification runner changes. On `main`, if the
immutable GHCR tag already exists, the workflow pulls and tests that exact image
instead of rebuilding or overwriting it.

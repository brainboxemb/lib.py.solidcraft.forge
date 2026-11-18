# Forge qualification image

This image contains the slow-changing qualification toolchain only.

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

# Forge qualification image

This image contains only the slow-changing qualification toolchain. Forge
source, examples and qualification contracts are mounted from the current
checkout at runtime.

Version ownership is explicit:

- SolidCraft: `scpf/scpf/version.py`;
- Python base image: `qualification/toolchain.json`;
- CADCraft version/checksum: `qualification/toolchain.json`;
- reference-library versions: `qualification/toolchain.json`.

The Dockerfile contains no tool-version literals. The Python base image is
pinned by OCI digest.

## Identity

`scripts/qualification_image.py` hashes:

- `docker/qualification/Dockerfile`;
- `qualification/toolchain.json`;
- `scpf/scpf/version.py`.

The immutable image tag is:

```text
ghcr.io/brainboxemb/lib.py.solidcraft.forge/qualification:toolchain-<sha256>
```

CI consumers must use the immutable tag, never `latest`.

## Build workflow

`.github/workflows/qualification-image.yml` is the only workflow that builds
the image. It runs when Docker/toolchain inputs change.

On a source branch it:

1. validates image metadata;
2. builds the image;
3. runs one `simple-box` end-to-end integration smoke.

On `main` it additionally publishes the immutable image to GHCR after the
smoke passes.

## Integration smoke

`qualification/integration/simple_box.py` proves one vertical path:

```text
Forge compile
  -> SolidCraft replay
  -> native save/export
  -> measurement eval
  -> saved-design parameter mutation
  -> native Q4/Q5 validation
```

The purpose is to prove the environment with one example before the full
qualification suite consumes the image.

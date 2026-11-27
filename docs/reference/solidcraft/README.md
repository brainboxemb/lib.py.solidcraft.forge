# SolidCraft version references

Forge keeps immutable, version-pinned SolidCraft engineering evidence under:

```text
docs/reference/solidcraft/
  0.42.0/
  0.45.0/
  0.48.1/
  0.49.0/
  0.50.0/
  <future-version>/
```

The historical [0.42.0](0.42.0/SOURCE.md) tree remains accepted historical
qualification evidence.

The hand-authored 0.43.0 migration tree was removed during the 2026-11-21
audit because it was not a canonical command snapshot. Do not reconstruct it or
use it as an input for newer versions.

## Canonical capture rule

For current and future SolidCraft targets, the command reference is captured
from the exact qualified runtime:

```text
qualified immutable solidcraft-cli
        |
        +--> solidcraft-cli commands
                |
                +--> commands.json   canonical machine evidence
                |
                +--> commands.md     generated human catalog
```

Use the Forge-owned reference module to create the version tree:

```sh
PYTHONPATH=modules/solidcraft-reference/src \
python -m cad_library_solidcraft_reference capture \
  --image ghcr.io/brainboxemb/cad-solidcraft:vX.Y.Z \
  --version A.B.C \
  --upstream-commit <40-char-upstream-sha> \
  --runtime-release vX.Y.Z \
  --out docs/reference/solidcraft/A.B.C
```

Verify the checked reference against the root immutable runtime pin with:

```sh
PYTHONPATH=modules/solidcraft-reference/src \
python -m cad_library_solidcraft_reference verify --repo-root .
```

A versioned command reference must never be a manually selected subset. The raw
registry is retained so completeness and later diffs can be checked directly.

## Adding a new SolidCraft version

1. qualify the current stable SolidCraft release in the runtime owner
   repository;
2. release an immutable runtime image from the exact green commit;
3. run the `solidcraft-reference` capture module against that exact immutable runtime;
4. record the exact upstream commit, runtime release and runtime image in
   `SOURCE.md`;
5. review the generated registry diff before adapting Forge compatibility code;
6. update Forge's tested SolidCraft version/runtime pin through the appropriate
   lane;
7. run Forge API/compiler qualification against that evidence.

An accepted canonical version directory is immutable. A noncanonical migration
note is not promoted to canonical status merely because it already exists in
Git history.

The repository-level development procedure is documented in
[../../development.md](../../development.md).

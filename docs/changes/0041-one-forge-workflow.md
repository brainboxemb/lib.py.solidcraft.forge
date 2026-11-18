# 0041 — One user-facing Forge workflow

**Tracks:** issue #346

## Problem

Normal Forge operation was spread across many visible GitHub Actions workflows:
preflight, preview, affected qualification, full safety, site publication,
reconcile, contract snapshot, qualify-main and release.

For one operator this made CI state difficult to understand and required
knowledge of internal pipeline phases.

## Decision

Expose one normal workflow:

```text
.github/workflows/forge.yml
name: Forge
```

The only separate workflow is:

```text
.github/workflows/qualification-image.yml
name: Forge · qualification image
```

It remains separate solely because building and caching the immutable
SolidCraft/reference toolchain image is a performance optimization.

Forge owns:

- PR risk classification and verification;
- PR technical/Pages previews;
- full technical main qualification;
- presentation-only main site reuse;
- stable `build/main` and Pages publication;
- closed-PR cleanup;
- scheduled full safety qualification;
- generated-output reconcile;
- pinned SolidCraft contract checks;
- explicit release publication after full qualification.

Manual Forge runs and `scripts/ci/forge.trigger` on main both request full
recovery:

```text
main -> qualification -> build/main -> Pages
```

The operator never chooses Q1/Q2/Q6/full.

## Performance

PRs remain risk-based. A change to the Forge pipeline itself runs one
`simple-box` affected Q1-Q6 smoke so the end-to-end image -> gate -> build ->
preview path is proven without rebuilding the full catalog.

Technical main changes deliberately run one full Q1-Q6 gate. Presentation-only
main changes may reuse the complete passing `build/main` baseline.

## Verification

Tests require exactly two workflow files, verify planning/gate behavior and
ensure the image worker is the only extra workflow.

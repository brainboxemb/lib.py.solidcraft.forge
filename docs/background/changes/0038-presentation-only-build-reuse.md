# 0038 — Presentation-only build reuse

**Tracks:** issue #320  
**Scope:** site-only publication, generated technical baseline reuse and CI contract tests.  
**SolidCraft target:** unchanged; this change does not alter SolidCraft commands or qualification geometry.

## Problem

Presentation-only changes such as `AGENTS.md`, normal documentation and site
templates were correctly classified as non-technical, but the site publication
workflow then recalculated every qualification case input hash before reusing
`build/main`.

That couples simple presentation publication to technical case-hash machinery.
It also caused a documentation-only main push to fail even though the existing
`build/main` baseline was complete and every technical case had already passed.

## Decision

Keep the publication states simple:

`source -> qualified build -> site`

For a presentation-only source change:

1. classify the changed source as presentation-only;
2. require a structurally valid, complete passing `build/main` baseline;
3. reuse that technical baseline unchanged;
4. rebuild and test only the site;
5. publish the site with the current source commit and immutable build commit
   recorded separately.

Do not recalculate every case input hash merely to publish presentation-only
content.

Per-case hashes remain part of technical selection and promotion. They are not
the decision boundary for presentation-only publication.

## Technical changes

If any changed path is technical, the presentation-only path refuses reuse.
The normal technical qualification and promotion flow remains authoritative.

Release/full-qualification reuse after a squash merge is a separate change
tracked by issue #340.

## Implementation

The site workflow uses:

`python scripts/generated_output.py verify-build --root generated-build/main --require-complete`

It no longer calls `verify-current-hashes` for presentation-only publication.

The existing `scripts/reusable_qualification.py` classifier remains the source
for deciding whether the source change is presentation-only.

## Qualification

Regression tests prove that:

- a complete passing main baseline is accepted without calling
  `case_input_hash()`;
- an incomplete main baseline is rejected;
- presentation-only paths are accepted by the reuse classifier;
- technical compiler paths are rejected;
- the workflow uses the complete-build verifier and not current-hash
  recalculation.

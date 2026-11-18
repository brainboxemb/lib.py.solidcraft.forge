# 0042 — Reliable qualification-image cache resolution

**Tracks:** issue #261  
**Scope:** Forge qualification-image reuse and CI cache-miss detection.

## Problem

The Forge workflow used a 30-second `docker pull` timeout as both the image
lookup and the image download.

That made a slow pull indistinguishable from a missing immutable image. Main
Forge run #1590 reproduced the problem: the same image had been reused by the
preceding PR run, but the main pull reached the timeout and Forge rebuilt the
qualification image unnecessarily.

## Decision

Qualification-image cache resolution belongs in
`scripts/qualification_image.py`.

The resolver:

- pulls the immutable image without an arbitrary short timeout;
- returns `exists=true` when the pull succeeds;
- returns `exists=false` only when the registry explicitly reports that the
  image or manifest does not exist;
- fails on other registry or network errors instead of treating them as a cache
  miss.

The GitHub workflow consumes only the resolver outputs and remains a thin
orchestration wrapper.

## Verification

Regression tests cover:

- an existing immutable image is reused;
- an explicit missing manifest selects the local build tag;
- a transient registry failure does not start a rebuild;
- the workflow contains no inline timed `docker pull` cache decision.

This change fixes one concrete reuse failure. Issue #261 remains open for the
broader full-qualification performance targets.

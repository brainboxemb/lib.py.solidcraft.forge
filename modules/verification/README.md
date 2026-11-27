# Verification module

The CAD verification implementation is local to this repository. Its Python import name remains cad_verification. It owns shared assertions, comparisons, geometry, visual evidence, reports and SolidCraft verification adapters. Example-specific expectations remain with the example.

Source baseline: brainboxemb/lib.py.cad.verification v0.16.0, commit c7c145b7be0c602724e8cca874ef29990baaad1e (the existing Forge pin). Functional source and tests are imported; the standalone release-policy test is not applicable to this internal module. No external verification Git dependency remains. Only ordinary third-party Python dependencies are declared.

Tests use normal module discovery and run directly from source. Actual CAD verification will use the two existing CAD runtime roles, not a separate verification image.

SolidCraft visual policies may verify either the built baseline model or one
explicit native saved-design state. A policy-level `state` selects a
model-local SolidCraft command document; the adapter applies that document with
`solidcraft-cli run --in ... --save ...`, evaluates the resulting saved
`.sc`, and snapshots that same file. State evidence therefore remains native
SolidCraft presentation/geometry. `expected_views: []` is valid for
baseline-only presentation evidence such as color or exploded state; geometry
policies retain expected-shape views and envelopes.

Visual regression remains grayscale by default for backwards-compatible geometry evidence. Policies that verify display appearance may set `regression.mode: rgb`; encoded baseline payloads then retain RGB channels and color differences participate in the same deterministic mean/changed-pixel thresholds.


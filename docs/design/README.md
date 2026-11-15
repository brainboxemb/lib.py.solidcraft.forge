# Forge CAD design

Normative design changes are recorded chronologically in
[`docs/changes/`](../changes/README.md).

The numbered change records contain the use case, public API decision, native
SolidCraft command contract, lowering rules and required qualification evidence.
A later design change must add a new numbered record instead of rewriting an
older decision.

General cross-cutting public API rules remain in
[`docs/05-cad-api-design.md`](../05-cad-api-design.md).

For the SCPF 0.3.0 occurrence-placement redesign, use
[`0001-position-api-design.md`](../changes/0001-position-api-design.md).


## Foundational audit

The current compiler/object-model audit is recorded in
[the 2026-11 foundational audit](audit-2026-11.md).

The target compiler boundaries and invariants are defined in
[Forge compiler architecture and invariants](forge-architecture.md).

The audit is intentionally performed against `main`; exploratory PRs are
evidence only and are not implementation sources.

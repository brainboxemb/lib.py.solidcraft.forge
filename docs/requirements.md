# Forge requirements

These are durable repository/product invariants. Feature-specific signatures,
limits and examples belong in `api.md`, `design-api/`, implementation
docstrings and executable tests.

## Public API

1. Preserve the public Python package/import contract `scpf`.
2. Public API expresses CAD semantics, not backend command ids, replay ids,
   transport details or browser labels.
3. Preserve native associativity/editability when the backend exposes a stable
   native relationship.
4. Unsupported semantics fail explicitly rather than being approximated by a
   different public meaning.
5. Reusable components do not acquire application-level policy merely because a
   standalone catalogue/document wants particular presentation or
   configuration controls.

## Ownership

1. `models/<id>/` is one physical owner; engine implementations remain local
   implementations of that owner.
2. Generic CI/build/verification/Pages mechanics remain in their owning
   modules.
3. Generated CAD evidence belongs to `build/<scope>/`; Pages links/projects
   it but does not rebuild or duplicate it.
4. API probes are opt-in executable design evidence, separate from physical
   model owners.

## Compiler/backend boundary

1. Forge compiler state must retain every semantic dependency required by the
   authored operation, including dependencies used only by configuration or
   other non-geometry presentation intent.
2. Backend-specific limitations may constrain a lowering, but must not silently
   redefine the public semantic model.
3. A semantic slice is IR-ready independently of any one optional backend when
   it has a backend-neutral contract, typed normalization, pure IR boundary
   tests and stable typed SolidCraft compatibility; unsupported backends must
   fail closed on that typed node.
4. Backend coverage is tracked independently from IR coverage. Mitcad lowering
   and native Mitcad qualification may lag IR completion and must not become a
   per-capability gate for permanent `exp` IR migration.
5. Saved-design/native qualification is required where a backend contract
   claims editability, state switching, history identity, topology identity or
   other native persistence.
6. `docs/ir-coverage.md` is the canonical compiler migration ledger and must
   distinguish complete, partial, legacy and out-of-scope semantic families
   from backend lowering/native-qualification status.

## Verification

1. Evidence must be capable of catching the failure the owner claims to guard
   against; successful command generation alone is insufficient for visible or
   structural contracts.
2. Model-specific expectations stay with the physical owner.
3. Pages projects retained verification evidence only.

## Development and release

1. `main` is stable; `dev` is normal integration; `exp` is isolated
   experimentation and not a release source.
2. Integrations use the repository merge policy; agents do not choose merge
   methods manually.
3. Releases are prepared from qualified `main` and publication is explicit.
4. Runtime/version pins come from machine-readable repository configuration,
   not copied prose.

## Documentation

1. `main:docs/plan.md` is the canonical source of unfinished work.
2. `docs/handoff.md` is a session entrypoint, not a competing plan.
3. Active documentation must have a clear reader/owner; historical material
   belongs under `docs/legacy/`.
4. Public site content belongs under `site/`; machine-readable CI/Pages
   contracts belong with their owning capability rather than in `docs/`.
5. New user documentation should use the Hugo/Markdown direction; do not extend
   the parked legacy HTML Guide format.

# Forge development

## Normal work

Start normal product work from `dev` on a short-lived issue/fix/feature/docs
or chore branch. Experimental work may target permanent `exp`; `exp` is
never a release source.

Use `build.yml` only as a temporary branch-local selection override. Permanent
repository branch/runtime/root configuration belongs in `ci.yml`.

Integrate through the repository merge policy. The exact mandatory `/merge`
and conflict-recovery rules live in `AGENTS.md`.

## Tests and evidence

- `cadlib/tests/` contains package-owner tests.
- module tests stay with their module.
- model-specific tests/evidence stay with the physical model owner.
- real SolidCraft behavior is qualified in the configured immutable runtime.
- do not resurrect historical fixture coupling merely because an old migration
  test once used it.

## API design probes

Use `api-probes/<id>/probe.yml` for small executable API/backend experiments.

During development a branch may select probes through
`build.yml.api_probes`. Existing `main`, `dev` or `exp` can be tested
without source changes through the **API Probe** workflow.

Probe publication updates only selected probe owners and preserves physical
model output. A probe that becomes a permanent regression requirement should
graduate to the appropriate package/module/model test rather than remain an
always-on probe.

## Documentation changes

Read `docs/README.md` before adding documentation.

Do not add new material to `docs/legacy/`. Do not extend
`site/source/guide/*.html`; the HTML -> Markdown/Hugo conversion is separate
parked work.

When changing public API semantics, update the relevant active API/design
document and executable tests/probes in the same logical change.

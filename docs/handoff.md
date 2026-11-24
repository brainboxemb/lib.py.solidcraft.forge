# Handoff

Continue in `brainboxemb/lib.py.solidcraft.forge.NEW`.

Read `AGENTS.md`, `docs/requirements.md`, `docs/design.md` and `docs/plan.md` first.

## Accepted baseline

The twenty-owner gate is accepted and promoted on `main@87ba6e3b535f4b93f65d519e7694688473bc8b96`.

All 20 native SCPF stages and all 80 applicable geometry stages pass. Historical saved-design/inspection behavior is retained, and the historical public `Sketch.revolve()` API was restored in `cadlib/scpf`.

A/B evidence is recorded in:
- `docs/acceptance/five-owner-gate.md`;
- `docs/acceptance/ten-owner-gate.md`;
- `docs/acceptance/twenty-owner-gate.md`.

Stable generated output:
- `build/main/models` contains all twenty accepted owners;
- stable Examples currently contains `simple-box`, `anchored-holes` and `corner-anchor`;
- stable Verification contains all twenty owners.

Issue #29 is complete and closed.

## Active work — #31 Pages/documentation parity

The historical Forge site is the public-content A/B authority.

Historical stable route inventory:
- 4 Examples;
- 48 Verification routes total;
- 9 Guide chapters;
- 44 API Reference routes;
- Cheatsheet;
- API design contract.

The first #31 slice is already squash-merged to `dev` as `c6b9c9a55f35c8cc739be48b310ce0003dc40487`:
- `docs/reference/solidcraft` is restored for 0.42.0, 0.45.0 and 0.48.1;
- Pages projects `docs/reference/**` into Hugo rather than owning duplicate documentation.

Current branch/PR work:
- `issue/31-guide-cheatsheet`;
- draft PR #34;
- restores all 9 authored Guide chapters plus the Cheatsheet under source-owned `docs/`;
- projects them to `/guide/**` and `/cheatsheet/`.

Still required under #31:
- generated public API Reference parity (44 historical routes);
- migrate `components` with `purpose: [example, verification]` so Examples returns to the historical four;
- special Verification routes `coverage`, `joint-anatomy`, `results`;
- final route/content acceptance against OLD Pages.

Do not copy the retired OLD site generator wholesale. Re-home authored information under normal documentation owners and let Hugo/Pages project it. Generated CAD evidence stays on `build`.

## Handoff message

> Continue `brainboxemb/lib.py.solidcraft.forge.NEW` from issue #31. The twenty-owner model baseline is stable on `main@87ba6e3b535f4b93f65d519e7694688473bc8b96`; issue #29 is closed. The first Pages/reference slice is on dev at `c6b9c9a55f35c8cc739be48b310ce0003dc40487`. Continue draft PR #34 for the 9 Guide chapters and Cheatsheet, then restore the 44-route SCPF API Reference, migrate the historical `components` example/verification owner, and restore the special Verification routes. Use OLD stable Pages as the A/B authority.

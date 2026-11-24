# Handoff

Continue in `brainboxemb/lib.py.solidcraft.forge.NEW`.

Read `AGENTS.md`, `docs/requirements.md`, `docs/design.md` and `docs/plan.md` first.

## Stable baseline

`main`: `a556e0c20420ac59e0efecd3e9455eb6bd43ffbb`

Bootstrap is accepted:
- full main CI `45422240513`: success;
- Pages `45422613383`: success;
- real SCPF 0.15.0 source lives under `cadlib/src/scpf`;
- generic template modules/builders/verification/preview/build/Pages are installed;
- historical Forge remains unchanged as A/B reference.

Normal merge policy is now active from the default branch. Use a short-lived branch from `dev`, then `/merge` to squash into `dev`; promote `dev -> main` with a merge commit after full qualification.

## Active work

Issue #6 / draft PR #7 is the first real example migration: historical Forge `simple-box`.

The intended product path is:

```text
examples/simple-box/scpf/model.py
        ↓ local scpf compiler
SolidCraft command JSON
        ↓ generic builder-solidcraft
model.sc + model.stl + model.png
        ↓ reference runtime
geometry verification
```

Do not teach the generic SolidCraft builder Forge/SCPF semantics.

Before #6 can merge, recover the example-owned native command contract and old saved-design parameter/timeline verification, and record an explicit OLD vs NEW comparison. Do not start the five-example expansion first.

## Handoff message

> Continue `brainboxemb/lib.py.solidcraft.forge.NEW` from `docs/plan.md`. Bootstrap is stable on main at `a556e0c20420ac59e0efecd3e9455eb6bd43ffbb`. The active slice is issue #6 / draft PR #7: migrate the historical Forge simple-box end-to-end. Keep `scpf` as the public package and keep the old Forge repo read-only as the A/B baseline. Finish command-contract, saved-design/timeline verification, OLD-vs-NEW evidence, durable build and Hugo projection before expanding 1 -> 5 -> 10.

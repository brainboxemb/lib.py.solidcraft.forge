# Agent reference: SolidCraft

Purpose: answer normal Forge/SolidCraft command questions without external
documentation lookup.

## Version

Forge qualification target: **SolidCraft 0.42.0**

Pinned upstream release/tag:

```text
v0.42.0
commit 1b1e940cc48e4d1d5d01971a4be20e2e55647066
```

Full local command catalog:

```text
docs/vendor/solidcraft/0.42.0/commands.md
```

Version-pinned occurrence/joint evidence:

```text
docs/vendor/solidcraft/0.42.0/occurrence-identity.md
docs/vendor/solidcraft/0.42.0/joint-occurrence-references.md
```

Read the full catalog only when the command is not listed below.

## Commands currently emitted by Forge

```text
component.activate
component.create

file.new

joint.as_built
joint.create
joint.origin

material.assign
material.create

occurrence.copy
occurrence.move

parameters.add

sketch.circle.center
sketch.create
sketch.finish
sketch.line
sketch.rectangle.rounded
sketch.rectangle.two_point
sketch.text

solid.box
solid.chamfer
solid.cylinder
solid.extrude
solid.fillet
solid.hole
solid.loft
solid.shell
solid.sphere
```

This list is a quick routing index, not a second command specification. The
exact runtime contract belongs to SolidCraft 0.42.0.

## Local-data requirement

The version-pinned local data must be sufficient for ordinary command lookup,
not just command discovery. For Forge-relevant commands it should preserve the
parameter names, alternatives, defaults and placement semantics needed to answer
normal modelling questions without opening upstream source or a website.

For example, SolidCraft 0.42 `solid.box` accepts `length`, `width` and
`height`, plus either `corner:[x,y,z]` or `center:[x,y,z]`. A box authored
with `center` remains centre-placed when its dimensions change; `corner`
keeps the corner datum instead. This is native SolidCraft placement semantics,
not a Forge translation convention.

## Minimal lookup order

1. Need to know whether a command exists or its common Forge-relevant semantics?
   Check this file first.
2. Need another SolidCraft command?
   Search `docs/vendor/solidcraft/0.42.0/commands.md` locally.
3. Need exact parameters or JSON schema not cached locally yet?
   Query the pinned local CLI:
   `solidcraft-cli exec engine.describe '{"command":"<id>"}'`.
   When that information is useful for repeated Forge work, add it to the
   version-pinned local cache so the next lookup does not require introspection.
4. Only use upstream/web documentation when the pinned local snapshot/runtime
   cannot answer the question.

Do not fetch the SolidCraft website for ordinary compiler/qualification work.

## Runtime introspection

SolidCraft 0.42 exposes the registry directly:

```text
solidcraft-cli commands
```

It also exposes one command's typed input/output schema through:

```text
solidcraft-cli exec engine.describe '{"command":"joint.create"}'
```

Use the second form whenever only one command is relevant; it is much smaller
than loading the complete catalog.

## Qualification rule

During a SolidCraft-version qualification, existing Forge behaviour is tested
against the pinned runtime first. Do not adopt newly discovered commands merely
because they exist in the new catalog. New capability adoption is a separate
API/design change after compatibility has been established.

If the runtime behaviour differs from this local snapshot, verify the runtime
version first. A version mismatch is not a Forge API decision.

# Agent reference: SolidCraft

Purpose: answer Forge/SolidCraft command questions from the exact SolidCraft
version Forge targets, without rediscovering the command API upstream.

## Version

Forge qualification target: **SolidCraft 0.42.0**

Pinned upstream release/tag:

```text
v0.42.0
commit 1b1e940cc48e4d1d5d01971a4be20e2e55647066
```

## Primary command reference

For commands Forge emits, the primary local reference is generated from the
official pinned SolidCraft runtime:

```text
docs/vendor/solidcraft/0.42.0/runtime/manifest.json
docs/vendor/solidcraft/0.42.0/runtime/contracts/<command-id>.json
```

Each contract file is the raw result of:

```text
solidcraft-cli exec engine.describe '{"command":"<command-id>"}'
```

The complete runtime command catalog used to discover those commands is kept as:

```text
docs/vendor/solidcraft/0.42.0/runtime/commands.json
```

Do not maintain a second handwritten list of commands Forge emits. The generated
`manifest.json` is derived from the current Forge runtime source and CI fails
when Forge starts using another command without refreshing the snapshot.

The older human-readable command catalog remains useful for browsing:

```text
docs/vendor/solidcraft/0.42.0/commands.md
```

Version-pinned occurrence/joint evidence remains available at:

```text
docs/vendor/solidcraft/0.42.0/occurrence-identity.md
docs/vendor/solidcraft/0.42.0/joint-occurrence-references.md
```

## SolidCraft 0.42 typed-contract gaps

SolidCraft 0.42 itself does not publish typed input/output JSON Schemas through
`engine.describe` for four commands Forge currently uses:

```text
solid.hole
solid.loft
solid.pattern.rectangular
solid.shell
```

Their pinned contract files deliberately retain `input: null` and
`output: null`. The same files still preserve SolidCraft's runtime `params`
documentation, including the accepted parameter names and forms.

Do not pretend these four commands have a complete typed contract. When work
depends on a detail not present in their pinned `params` text, use
version-pinned supplemental evidence and native qualification, and record the
missing contract information explicitly.

## Lookup order

1. For a SolidCraft command Forge emits, read
   `runtime/contracts/<command-id>.json`.
2. To see exactly which commands Forge currently references and which contracts
   are incomplete, read `runtime/manifest.json`.
3. For another SolidCraft command, search `runtime/commands.json`.
4. If the pinned runtime contract is one of the explicit gaps and its `params`
   text does not answer the question, use pinned supplemental evidence.
5. Only then inspect upstream source/runtime for the same pinned release.
6. Do not use a website or a newer SolidCraft version to fill a 0.42 contract
   gap silently.

The local snapshot is intended to make ordinary compiler work possible without
repeating SolidCraft API research.

## Refreshing the snapshot

The snapshot is produced by:

```text
python scripts/solidcraft_snapshot.py \
  --out docs/vendor/solidcraft/0.42.0/runtime \
  --version 0.42.0 \
  --source-ref v0.42.0
```

CI regenerates it with the checksum-verified official release and compares the
result byte-for-byte with the checked-in snapshot.

A local source-only audit does not require SolidCraft:

```text
python scripts/solidcraft_snapshot.py \
  --check-pinned docs/vendor/solidcraft/0.42.0/runtime
```

## Qualification rule

During a SolidCraft-version qualification, first capture the candidate runtime
contract snapshot. Existing Forge behaviour is then tested against that pinned
contract. Do not adopt new commands merely because the new release contains
them; capability adoption is a separate design change.

If runtime behaviour differs from the checked-in snapshot, verify the runtime
version first. A version mismatch is not a Forge API decision.

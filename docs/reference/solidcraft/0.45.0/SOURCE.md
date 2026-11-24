# SolidCraft 0.45.0 canonical reference snapshot

This directory is generated from the command registry emitted by the qualified
immutable SolidCraft runtime. It is not a hand-authored Forge migration note.

- SolidCraft release: `v0.45.0`
- Upstream commit: `e8ce12ef78fe76281a04b7242a9ce059ff7d5067`
- Qualified runtime release: `v0.3.4`
- Qualified runtime image: `ghcr.io/brainboxemb/cad-solidcraft:v0.3.4`
- Captured CLI version: `solidcraft-cli 0.45.0`
- Registered commands: `819`

## Canonical evidence

- `commands.json` is the exact normalized JSON registry captured from
  `solidcraft-cli commands` in the immutable runtime.
- `commands.md` is generated from `commands.json` for human review.
- `changes-from-0.42.md` compares command identifiers with the retained
  historical 0.42.0 catalog.

Forge compatibility conclusions must be traceable to this captured registry,
the exact runtime behavior, or separately recorded upstream source evidence.
Do not replace this directory with a manually selected command subset.

# Live protocol plate fixture

> Documentation provenance: pre-Qualification sample originating in issue #7; retained by #559 because the current live-protocol unit suite executes this exact source.

## Purpose

This is a focused Forge protocol fixture, not a full model Verification case.

`scpf/tests/test_live.py` compiles `scpf/model.py` to exercise:

- one strict atomic live command batch;
- CLI `--connect --new` behavior before replaying a model;
- ordinary Forge model compilation through the same source used by those protocol tests.

The fixture remains intentionally small. Product geometry and full native/reference
Verification belong to the current model Verification catalog.

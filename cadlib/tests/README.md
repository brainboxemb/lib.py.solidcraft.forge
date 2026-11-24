# SCPF package-owner tests

This directory contains tests that can execute with the `cadlib` owner and its direct source dependencies present.

Historical Forge tests that reach into `examples/.../scpf` are intentionally not kept here during bootstrap. Those assertions migrate with their example owner so the package test suite does not depend on a partially migrated example graph.

Deferred files are tracked in `docs/migration-tests.md`.

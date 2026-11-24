# Deferred historical test ownership

Some historical Forge tests were intentionally not retained in `cadlib/tests` because they directly load repository model/source fixtures that are not yet migrated.

Deferred files include:
- `scpf/tests/test_assembly_attachments.py`;
- `scpf/tests/test_assembly_placement.py`;
- `scpf/tests/test_component_definitions.py`;
- `scpf/tests/test_geometry_features.py`;
- `scpf/tests/test_live.py`;
- `scpf/tests/test_model_authoring.py`;
- `scpf/tests/test_native_slots.py`;
- `scpf/tests/test_sketch_attachment.py`.

This is an ownership decision, not discarded coverage.

When a referenced historical fixture becomes a physical owner under `models/`, recover the relevant assertions with that model or with the smallest reusable package test that no longer depends on repository fixtures.

Known historical fixture names include `corner-anchor`, `parametric-attach`, `components`, `xz-anchor`, `anchored-holes`, `plate`, `bracket`, `model_authoring`, `slot-family` and `attached-through-all`.

Do not bulk-import these to make CI green. The rollout remains 1 -> 5 -> 10 -> remaining graph.

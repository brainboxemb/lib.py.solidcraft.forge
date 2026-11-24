# Deferred historical test ownership

The following historical Forge test files were copied during the first bootstrap attempt and then removed from `cadlib/tests` because they directly load example/source fixtures that are not yet migrated:

- `scpf/tests/test_assembly_attachments.py`
- `scpf/tests/test_assembly_placement.py`
- `scpf/tests/test_component_definitions.py`
- `scpf/tests/test_geometry_features.py`
- `scpf/tests/test_live.py`
- `scpf/tests/test_model_authoring.py`
- `scpf/tests/test_native_slots.py`
- `scpf/tests/test_sketch_attachment.py`

This is a migration ownership decision, not dropped coverage.

When the referenced example is migrated, recover the relevant assertions with that example or with the smallest reusable package test that no longer depends on repository fixtures.

Known referenced old Forge examples/source fixtures include:

- `corner-anchor`
- `parametric-attach`
- `components`
- `xz-anchor`
- `anchored-holes`
- `plate`
- `bracket`
- `model_authoring`
- `slot-family`
- `attached-through-all`

Do not bulk-import these merely to make bootstrap green. The agreed rollout remains 1 -> 5 -> 10 -> remaining graph.

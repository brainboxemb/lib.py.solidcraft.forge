# SCPF unit-test structure

The unit-test layer is the cheapest place to prove Forge API behaviour. Keep
general geometry rules here instead of waiting for qualification or a CAD
project to expose a missing combination.

## Geometry contracts

`geometry_contracts.py` contains the shared test data.

### Adding a primitive

Add one `BodyCase` to `PRIMITIVE_BODY_CASES`.

The shared tests then automatically cover:

- registry completeness against the compiler's supported primitive kinds;
- standalone native creation;
- parameter preservation;
- join, cut and intersection against every other primitive;
- generated derived bodies after join, cut and intersection;
- every registered general feature that declares compatibility with that body.

A new compiler primitive therefore makes the registry-completeness test fail
until its contract case exists.

### Adding a general feature

Add one `FeatureCase` to `FEATURE_CASES` and give body cases the matching
capability.

The feature is then run against every direct and generated derived body with
that capability. Do not add one test per body type.

Feature-specific tests are still appropriate for behaviour that is unique to
that feature, such as countersink validation or a special parameter rule.

### Unsupported combinations

Do not omit a body silently. If an operation is intentionally unsupported,
represent that through the body's capabilities and keep a focused negative test
for the public error when useful.

## Test files

Keep files grouped by API contract:

- `test_geometry_contracts.py`: generated body × operation matrices;
- `test_geometry_primitives.py`: primitive-specific details not covered by the matrix;
- `test_geometry_features.py`: feature-specific rules;
- `test_geometry_edge_features.py`: fillet/chamfer/taper and edge selection;
- `test_sketch_profiles.py`, `test_sketch_extrusion.py`,
  `test_sketch_attachment.py`, `test_sketch_patterns.py`: Sketch and 2D profile behaviour;
- `test_core_semantics.py`: shared value/direction helpers;
- `test_model_authoring.py`: root model and parameter authoring rules;
- `test_assembly_placement.py`: occurrence placement, grouping and replay;
- `test_component_definitions.py`: component identity, inputs and parameter scope;
- `test_assembly_attachments.py`: attachment and joint contracts.

Runtime, live-connection, snapshot and version tests remain in their dedicated
files.

## Rule of thumb

If the sentence describing a test contains "for every supported body", "for
all primitives" or "every compatible feature", it probably belongs in a shared
contract matrix rather than a hand-written regression.

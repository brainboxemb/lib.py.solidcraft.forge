# SCPF Forge qualification

- Forge: $forge_version
- SolidCraft: $solidcraft_version
- Commit: $source_commit
- Qualified at: $qualified_at
- Result schema: $schema_version

## Qualification cases

| Case | Overall | Tool verify | Model verify | Geometry | Saved design | Visual |
| --- | --- | --- | --- | --- | --- | --- |
$case_rows

## Model verification visual evidence

$image_sections

## Result data

The machine-readable source is results.json. Each model verification directory also
contains qualification-result.json plus the measurements, saved models, exports
and renders used as evidence.

## Qualification model

- **Tool verify:** the example-owned tests pass and Forge compiles a replayable
  SolidCraft command document.
- **Model verify:** SolidCraft replays that document and saves the expected
  editable SolidCraft design.
- **Geometry:** measured geometry and SolidCraft history match the declared proof
  contract.
- **Saved design:** cases that claim associativity still pass after editing the
  saved SolidCraft model. Cases without such a claim report NOT-REQUIRED.
- **Visual:** fixed-camera renders satisfy both expected-shape and regression
  checks.

The report structure comes from qualification/templates/report.md; CI only
supplies result data.

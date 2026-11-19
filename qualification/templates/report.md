# SCPF Forge qualification

- Forge: $forge_version
- SolidCraft: $solidcraft_version
- Commit: $source_commit
- Qualified at: $qualified_at
- Result schema: $schema_version

## Qualification cases

| Case | Overall | Integration | Native model | Geometry | Saved design | Visual |
| --- | --- | --- | --- | --- | --- | --- |
$case_rows

## Native visual evidence

$image_sections

## Result data

The machine-readable source is results.json. Each native case directory also
contains qualification-result.json plus the measurements, saved models, exports
and renders used as evidence.

## Qualification model

- **Integration:** the example-owned tests pass and Forge compiles a replayable
  SolidCraft command document.
- **Native model:** SolidCraft replays that document and saves the expected
  editable native design.
- **Geometry:** measured geometry and native history match the declared proof
  contract.
- **Saved design:** cases that claim associativity still pass after editing the
  saved SolidCraft model. Cases without such a claim report NOT-REQUIRED.
- **Visual:** fixed-camera renders satisfy both expected-shape and regression
  checks.

The report structure comes from qualification/templates/report.md; CI only
supplies result data.

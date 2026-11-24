# Forge NEW plan

This file contains unfinished work only.

## Stable baseline

The corrected repository architecture is already qualified on `dev`; promotion to `main` is the next integration step.

Accepted 1-owner migration:
- `simple-box` is one physical owner;
- SCPF is primary;
- historical CadQuery/build123d/PythonSCAD/pyBOSL2 references are local implementations;
- OLD and NEW SCPF command documents match semantically;
- historical native baseline and `length=50` saved-design mutation match retained OLD machine evidence;
- all five implementations pass their geometry contract;
- durable `build/dev/models/simple-box` is published;
- Pages exposes both `native` and `geometry` stages with durable report links.

Issues #6 and #14 are closed.

The historical Forge repository remains the known-good A/B source.

## Now — #16 five-owner gate

Qualify **five total physical model owners** before expanding further.

Already accepted:
1. `simple-box` — fundamentals / editable parameters / native Box.

Add:
2. `primitive-csg` — primitives and Boolean composition;
3. `anchored-holes` — face-relative Hole plus native rectangular pattern;
4. `assembly-decorator` — component definition, imported assembly and occurrences;
5. `parametric-attach` — symbolic attachment gap and saved-design mutation.

For every new owner:
- keep one `models/<id>/` owner;
- preserve historical `model.yml.purpose` exactly;
- use SCPF as the Forge implementation and migrate historical reference implementations that existed;
- reuse generic template builders, staged verification and two runtime roles;
- migrate owner-local native/geometry/saved-design expectations;
- compare NEW evidence directly against retained OLD build artifacts;
- qualify candidate before permanent integration.

Do not expand to the 10-owner gate until all five owners are accepted, durably published and correctly projected by Pages.

## After the five-owner gate

1. migrate to ten representative physical owners;
2. classify and migrate the remaining graph;
3. migrate API/guides/reference documentation;
4. qualify NEW release/version mechanics;
5. retire duplicated historical orchestration only after parity.

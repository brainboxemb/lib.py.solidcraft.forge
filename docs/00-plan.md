# Forge 0.42 plan and status

## Objective

Keep Forge a readable Python modelling layer that emits native SolidCraft
commands and editable native history. SolidCraft remains the geometry kernel,
feature-history owner and assembly/joint solver; Forge must not grow a second
geometry engine.

## Completed for the 0.42 qualification

### One API source of truth

Public Forge API facts come from the Python implementation and public
docstrings. The generated human API reference, guide-side API facts and compact
agent index all use those same objects.

CI requires every name in `scpf.__all__` to resolve to a generated direct
reference, grouped reference member or generated alias. Enum aliases are read
from `Enum.__members__`, so values such as `Anchor.UP` and
`Anchor.DOWN` cannot silently disappear from documentation.

### Understandable documentation flow

The guide explains modelling intent first and generated API details afterwards.
The complete API reference is grouped by task rather than presented as one
large flat dump.

The assembly guide uses the physical-part boundary:

1. geometry/features that are manufactured as one item stay in one component;
2. separately manufactured or installed items are separate components;
3. `move()` / `rotate()` express deliberate placement;
4. `attach()` expresses a relationship between separate occurrences;
5. `Anchor`, `AnchorFrame` and `AnchorTopology` select the appropriate
   relationship reference;
6. `group()` changes browser/subassembly organisation and is not a mate.

A component may therefore contain a plate, boss, holes, fillets and other
features. It does not mean one primitive.

### Local, version-pinned knowledge

Forge targets SolidCraft 0.42.0. Routine implementation questions should be
answerable from the local version snapshot and agent references before any
website/upstream lookup.

- Forge API: `docs/agent/forge-api.json`
- SolidCraft 0.42 routing/semantics: `docs/agent/solidcraft.md`
- SolidCraft 0.42 command catalog: `docs/vendor/solidcraft/0.42.0/commands.md`
- PythonSCAD / pyBOSL2 working cache:
  `docs/agent/reference-libraries.md`

When runtime introspection fills a reusable gap, the useful result belongs in
the pinned local cache rather than being rediscovered on every agent run.

### Qualification loop

Q1-Q6 remain the release/version gate:

| Level | Evidence |
| --- | --- |
| Q1 | Python API/compiler invariants |
| Q2 | generated command contract |
| Q3 | native SolidCraft build and saved editable design |
| Q4 | native semantic/measurement validation |
| Q5 | saved-design parametric mutation where required |
| Q6 | fixed-camera visual regression |

For iteration, `qualification/run_affected.py` always runs Q1/Q2 and then
runs Q3-Q6 only for selected case slugs or `group:<name>`. It records
SolidCraft startup and per-case compile/build/eval/snapshot/mutation timings.
The full gate remains mandatory for version qualification and release.

### Executable comparison references

Every qualification case has both:

```text
examples/<case>/pythonscad/model.py
examples/<case>/pybosl2/model.py
```

Each file is executable Python, has a module explanation and exposes its final
geometry as `model`.

The qualification runner executes each implementation, exports its own STL,
checks its overall bounds against the independent case expectation and creates
front/right/isometric renders. The final case sheet can therefore show Forge /
SolidCraft evidence alongside separately generated PythonSCAD and pyBOSL2
reference evidence.

PythonSCAD is primarily the neutral Python geometry comparison. pyBOSL2 uses
its own anchors/attachment concepts when they are relevant. Neither comparison
is allowed to masquerade as proof of SolidCraft-native joints, feature history,
topology persistence or saved-design parameter associativity.

## Next API work after this plan

### Native primitive origin selection

SolidCraft 0.42 natively supports two `solid.box` placement modes:
`corner:[x,y,z]` and `center:[x,y,z]`; centre-placed boxes retain that
centred datum when their dimensions change.

Forge should expose primitive-origin intent directly instead of emulating it
with corrective translations. The existing default Box behaviour and the CSG
Box lowering must first be made semantically consistent, then qualified against
the native SolidCraft behaviour.

This follow-up API/design change is implemented and qualified by
[change 0022](changes/0022-native-box-origin.md). It remains separate from the
completed remediation phases above.

# Foundational component/occurrence contract closeout

Status: **complete on the qualification branch; final Q1-Q6 gate required before merge**  
Foundation issue: **#164**  
Repeated-parent defect: **#162**  
Forge: **0.6.0 development line**  
SolidCraft target: **0.42.0**

## Why this document exists

Forge v0.2.0 was released before the reusable-component foundation was defined
as one coherent compiler and qualification contract. That release is explicitly
marked **WITHDRAWN** in `CHANGELOG.md` and must not be used as a downstream CAD
baseline.

The architecture has since been rebuilt around Forge-owned definition and
occurrence identity, replay-bound native occurrence ids, declarative Placement,
explicit attachments and saved-design qualification.

This page closes the original ten foundation scenarios from #164 against the
current implementation. It is an index to the actual normative design records
and executable qualification; it does not introduce a second API specification.

## Foundation use-case matrix

| # | Required use case | Current evidence | Saved-design evidence |
| ---: | --- | --- | --- |
| 1 | Create one reusable component | `components`: one native Block definition is created and reused. Semantic component construction is covered in `scpf/tests/test_assembly.py`. | Native Q3/Q4 verifies the reusable definition/occurrence structure. |
| 2 | Create two independent components | `parent-derived-child-size`: ParentBlock and DerivedChild are separate reusable definitions; definition-identity unit tests also reject accidental sharing of different build inputs. | Q5 changes parent dimensions while the separate child definition keeps its declared dependency. |
| 3 | Create a second occurrence of one shared definition | `components`: `left.copy(...)` creates a distinct occurrence sharing the same Block definition. | Native Q3/Q4 verifies one shared definition with two placements. |
| 4 | Place an occurrence numerically | `components`: the second occurrence lowers directly to `occurrence.copy(..., translate=[40,0,0])`. | Q3/Q4 verifies the resulting two placements. |
| 5 | Place an occurrence parametrically and mutate it in the saved design | `four-corner-l`: symbolic occurrence positions lower through replay-bound `occurrence.move`. | Q5 resizes the frame and proves all four placed copies follow without rerunning Python. |
| 6 | Combine rotation and placement | `eight-flightcase-corners`: copied protectors use assembly-owned XYZ Placement plus rotation through replay-bound native moves. | Q5 changes case width/depth/height and proves all rotated copies follow. |
| 7 | Explicitly attach one occurrence to another | `parametric-attach` and `attach-angle`: authored attachments lower to native joints rather than Placement joints. | `parametric-attach` Q5 changes the saved joint gap and the child follows. |
| 8 | Repeat a parent definition and attach children to both occurrences | `repeated-parent-attachments`: two Parent occurrences share one definition, two Marker occurrences share one definition, and exactly two authored rigid joints target the real replay-bound occurrences. | Q5 changes `parent_height` 40→60 mm and proves **both** disconnected parent/child graphs move their Marker from Z=40..50 to Z=60..70. |
| 9 | Save/reopen/mutate without rerunning Python | Every case marked `q5_required=True` mutates the saved native `.sc` design. `simple-box`, `four-corner-l`, `parametric-attach` and `repeated-parent-attachments` cover the foundation paths directly. | Q5 is a release-gated qualification level, not a Python recompile. |
| 10 | Prove generated display names are not identity | Changes 0008/0013 plus replay-selector tests require Forge occurrence ids and replay-bound native ids. Qualification rejects predicted `Component:N` selectors. | Repeated copied Placement and copied attachment endpoints work through ids returned by the current replay, independent of browser numbering. |

## Compiler contracts

The public semantics are defined in `docs/05-cad-api-design.md`. The compiler
boundary and invariants are in `docs/design/forge-architecture.md`.

The implementation follows these rules:

- **Definition is reusable geometry.** Definition identity contains every
  build-affecting input.
- **Occurrence is physical placement.** Every `.copy()` gets a new
  Forge-owned occurrence id while it may share the same definition.
- **Placement is occurrence pose.** Placement never becomes a joint merely as a
  lowering workaround.
- **Attachment is a relationship.** One authored attachment lowers to the
  required native joint relationship; generated Placement joints are forbidden.
- **Names are labels.** Forge never predicts SolidCraft-generated names such as
  `Board:2` to address a later occurrence.
- **Replay binds runtime ids.** `component.create` and `occurrence.copy`
  bind their returned native occurrence id to deterministic replay variables.
  Later `occurrence.move` and qualified `joint.create` commands use those
  variables.
- **Native geometry selection uses the right coordinate frame.**
  `joint.create` receives the explicit occurrence id plus a world-coordinate
  geometry pick.
- **Normal attachments may need a seed pose.** SolidCraft 0.42 does not place a
  second disconnected floating rigid graph at an arbitrary intended pose.
  Forge therefore applies the already-computed child Placement before
  `joint.create`. The seed is not a second relationship and retains symbolic
  parent-size, gap and offset dependencies.
- **No silent fallback.** Unsupported combinations, including unqualified
  rotated normal-attachment references, fail before native command generation.

## Native capability matrix

| SolidCraft 0.42 command | Qualified Forge use | Identity / parameter rule |
| --- | --- | --- |
| `component.create` | Create reusable definition and first occurrence. | Returns native occurrence id; replay binds it. |
| `occurrence.copy` | Create another occurrence; numeric unrotated translation is applied directly where possible. | Returns new native occurrence id; replay binds it. `translate` itself is numeric-only. |
| `occurrence.move` | Symbolic/rotated occurrence Placement and normal-attachment seed pose. | Target is replay-bound id. Translation may contain native parameter expressions and remains associative. |
| `joint.create` | Qualified normal rigid/planar attachment paths, including copied parent/child occurrences. | Both sides carry replay-bound occurrence identity plus current world geometry picks. |
| `parameters.change` | Q5 saved-design mutation. | Rebuild must occur in the saved SolidCraft design without rerunning Forge. |

This matrix is deliberately narrower than “SolidCraft supports the command”.
Each Forge use is enabled only where the exact selector/parameter behaviour has
been qualified.

## Identity and Placement decision records

The chronological design records remain the authoritative history:

- change 0008 — stable Forge occurrence id;
- change 0009 — replay-first Placement and removal of guessed browser names;
- change 0010 — native joint-reference investigation and explicit rejection of
  unsafe copied-endpoint guessing;
- change 0013 — replay variables bind the actual occurrence ids returned by
  create/copy and restore replay-safe Placement/copied attachment addressing;
- change 0029 — correct world picks plus symbolic seed Placement for repeated
  parent attachments and disconnected floating joint graphs.

Change 0013 supersedes the temporary capability removal recorded during change
0010; the research conclusion that generated `Component:N` names are not an
identity mechanism remains valid.

## Release gate

`docs/10-release-process.md` requires the complete Q1-Q6 qualification on the
exact release-PR head, with no active entries in
`docs/design/release-blockers.txt`.

The qualification layers are:

- Q1 — public Python/API semantics;
- Q2 — exact emitted SolidCraft command contract;
- Q3 — native build/save;
- Q4 — native geometry/relationship semantics;
- Q5 — saved-design mutation where required;
- Q6 — expected-shape evidence plus approved render regression.

The repeated-parent case closes the only missing foundational scenario from
#164. Its first native probe intentionally failed and exposed two separate
facts: copied-parent geometry picks needed the occurrence Placement, and a
second floating rigid graph needed the child seed pose. The corrected case now
passes Q4 and Q5; Q6 is approved from the same source-matched native renders
before the final merge gate.

## Downstream status

v0.2.0 remains withdrawn permanently.

A downstream CAD project may pin a later Forge release only after the release
workflow has passed the exact-head Q1-Q6 gate described above. A feature branch
or a historical qualification artifact is not a release baseline.

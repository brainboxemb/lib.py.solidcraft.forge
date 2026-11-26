# Verification evidence audit

Issue: #163

This audit classifies every model owner in the v0.21.0 `dev` baseline whose
`model.yml.purpose` contains `verification`. It records whether the evidence
can catch the failure the owner is intended to guard against. A native replay
PASS by itself is not treated as sufficient for visibly geometric behavior.

## Minimum evidence contract

Choose evidence from the contract being proved; do not add screenshots blindly.

- **Visible geometry:** deterministic review views, geometry checks where
  meaningful, and an approved visual expectation.
- **Native feature/history:** saved-design mutation or inspection proving the
  native feature/history survives and remains editable.
- **Topology/relationship:** native/topology inspection plus geometry evidence;
  add visual evidence when wrong topology would produce a visibly wrong result.
- **Configuration/state:** inspect the stored native table/state and the
  resulting state. Add visual evidence when the selected state is itself a
  user-visible contract.
- **Manufacturing-only geometry:** qualify the authoritative manufacturing
  representation, not a fabricated display B-rep. Retain native export plus
  deterministic Actual/Goal/Overlay evidence.
- **Drawing:** structural native inspection plus approved sheet-image baseline.
- **Negative/runtime behavior:** require the explicit expected failure or
  cross-runtime result; a missing artifact is not evidence.

Pages is a projection of retained durable evidence only. It does not execute CAD
or manufacture missing verification.

## Audit

| owner | intended contract | native/history | geometry | visual expectation | Pages expected/actual | status | follow-up |
|---|---|---:|---:|---:|---:|---|---|
| anchor-topology-mutation | topology pick follows resize | yes | yes | yes | yes | complete/current | — |
| anchored-holes | face hole + native pattern | yes | yes | yes | yes | complete/current | — |
| appearance-color | stored display-only appearance | yes | n/a | no | no | missing visible-state expectation | #256 |
| as-built-attach | as-built rigid pose | yes | yes | yes | yes | complete/current | — |
| assembly-decorator | reusable imported assembly occurrences | yes | yes | yes | yes | complete/current | — |
| assembly-owned-anchor | assembly datum follows resize | yes | yes | yes | yes | complete/current | — |
| attach-angle | native joint clocking | yes | yes | yes | yes | complete/current | — |
| attached-through-all | face-attached Polygon through-cut | build only | no explicit contract | no | no | missing structural/visual expectation | #255 |
| bracket | minimal XZ L-profile | yes | yes | yes | yes | complete/current | — |
| circle-negative-extrude | signed negative extrusion | yes | yes | yes | yes | complete/current | — |
| circular-feature-pattern | native circular history pattern | yes | yes | yes | yes | complete/current | — |
| components | shared definition + occurrences | yes | yes | yes | yes | complete/current | — |
| cone-boolean | native Cone join after feature history | build only | no explicit contract | no | no | missing structural/visual expectation | #255 |
| configuration-installed-state | Free / Installed native table | yes | state inspection | no | no | missing visible-state expectation | #256 |
| configuration-position | occurrence positions by configuration | yes | state inspection | no | no | missing visible-state expectation | #256 |
| configuration-symbolic-math | native symbolic math recomputation | yes | state/result inspection | intentionally no | n/a | intentionally non-visual | — |
| configuration-table | native parameter/suppression table | yes | state/result inspection | intentionally no | n/a | intentionally non-visual | — |
| corner-anchor | topology-backed corner follows resize | yes | yes | yes | yes | complete/current | — |
| eight-corner-brackets | eight reusable corner placements | yes | yes | yes | yes | complete/current | — |
| eight-flightcase-corners | eight oriented protector placements | yes | yes | yes | yes | complete/current | — |
| exploded-views | stored exploded presentations | yes | state inspection | no | no | missing visible-state expectation | #256 |
| four-corner-l | four rotated reusable profiles | yes | yes | yes | yes | complete/current | — |
| group-hierarchy | native nested component hierarchy | yes | yes | yes | yes | complete/current | — |
| hole-family | native simple/counterbore/countersink/threaded holes | yes | yes | yes | yes | complete/current | — |
| native-revolve | editable native revolve + mutation | yes | change geometry | no | no | missing visual expectation | #255 |
| parameter-scope | local/shared parameter dependencies | yes | yes | yes | yes | complete/current | — |
| parametric-anchor | face anchor follows width | yes | yes | yes | yes | complete/current | — |
| parametric-attach | editable attachment distance | yes | yes | yes | yes | complete/current | — |
| parametric-move | editable occurrence placement | yes | yes | yes | yes | complete/current | — |
| parametric-offset | local attachment-plane offset | yes | yes | yes | yes | complete/current | — |
| parametric-placement-pair | symmetric shared placement | yes | yes | yes | yes | complete/current | — |
| parent-derived-child-size | child dimensions derive from parent | yes | yes | yes | yes | complete/current | — |
| primitive-csg | primitive boolean result | yes | yes | yes | yes | complete/current | — |
| rectangular-pattern | two-direction native feature pattern | yes | yes | yes | yes | complete/current | — |
| repeated-parent-attachments | repeated parent joint graphs | yes | yes | yes | yes | complete/current | — |
| revolute-joint | stored bounded native revolute + driven pose | yes | driven-state inspection | no | no | missing visible-motion expectation | #256 |
| rotated-copy-placement | translated + rotated occurrence placement | yes | yes | yes | yes | complete/current | — |
| rotated-sketch-cutter | non-axis-aligned sketch cutters | build only | no explicit contract | no | no | missing structural/visual expectation | #255 |
| round-top-sketch | TOP face on circular body | yes | yes | yes | yes | complete/current | — |
| rounded-rectangle-sketch | attached pad + standalone cut | yes | yes | yes | yes | complete/current | — |
| sample-plate-drawing | native full + compact technical drawings | yes | drawing inspection | yes, two sheet baselines | yes | complete/current | — |
| selective-profile-extrude | selected sketch regions only | yes | yes | yes | yes | complete/current | — |
| sheet-contour-flange | native contour-flange history | yes | flat-pattern inspection | no | no | missing folded-geometry expectation | #257 |
| sheet-contour-flange-recess | broad-face recess + live/headless parity | runtime fixture | no explicit visual contract | no | no | blocked by live runtime defect; visual gap | #73, #255 |
| sheet-edge-flange | native editable edge flange | yes | flat-pattern inspection | no | no | missing folded-geometry expectation | #257 |
| sheet-fold | native fold + associative fold line | yes | yes | yes | yes | complete/current | — |
| sheet-hem | native editable hem | yes | flat-pattern inspection | no | no | missing folded-geometry expectation | #257 |
| sheet-path-flange | path-driven flange | yes | flat-pattern inspection | no | no | missing folded-geometry expectation | #257 |
| sheet-perforate | manufacturing perforation semantics | yes | authoritative DXF/flat pattern | yes, manufacturing | yes | complete/current | — |
| shifted-axis-revolve | shifted native revolve + suppression state | yes | state inspection | no | no | missing visible-state expectation | #256 |
| simple-box | editable native Box baseline | yes | yes | yes | yes | complete/current | — |
| sketch-pattern-mirror | associative sketch pattern/mirror | yes | yes | yes | yes | complete/current | — |
| slot-family | native Slot family + mutation | yes | yes | yes | yes | complete/current | — |
| top-sketch-after-chamfer | post-chamfer face attachment | yes | yes | yes | yes | complete/current | — |
| topology-face-boundary-box | replay-bound TOP perimeter topology | topology commands | no explicit contract | no | no | missing structural/visual expectation | #255 |
| topology-face-boundary-xz | replay-bound FRONT/BACK perimeter topology | topology commands | no explicit contract | no | no | missing structural/visual expectation | #255 |
| xz-anchor | standard anchors on XZ extrusion | yes | yes | yes | yes | complete/current | — |

## Findings

The current `dev` catalogue contains 57 verification owners.

- 38 owners are complete/current for their intended contract. This includes
  `sheet-perforate`, whose explicit visual expectation is the authoritative
  manufacturing representation rather than the display B-rep.
- 2 owners are intentionally non-visual because their contract is native
  table/expression state rather than a presentation result:
  `configuration-table` and `configuration-symbolic-math`.
- 7 visibly geometric/topology owners need explicit geometry/visual evidence:
  #255.
- 6 user-visible state/motion owners need visual state evidence in addition to
  their existing native inspections: #256.
- 4 folded sheet-metal owners need normal folded-geometry visual baselines in
  addition to their existing native/flat-pattern checks: #257.
- `sheet-contour-flange-recess` is one of the seven #255 owners and also
  remains tied to the separate live-vs-headless runtime defect tracked by #73.

The three evidence follow-ups cover 17 distinct owners; they do not create new
model owners and they do not turn #163 into a bulk verification-fix PR.

## Future owner rule

A new verification owner must state the contract it proves and include the
minimum evidence needed to catch a meaningful regression in that contract.
Reviewers should reject an owner that merely demonstrates command acceptance
when visibly or structurally wrong output could still pass.

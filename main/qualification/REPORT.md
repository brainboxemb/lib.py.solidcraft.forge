# SCPF Forge qualification

- Forge: `0.10.0`
- SolidCraft: `0.42.0`
- Commit: `8f8aea1b1326b424380cc9b04eb53ac979138783`
- Qualified at: `2026-11-18T15:51:23Z`
- Result schema: `4`

## Qualification cases

| Case | Overall | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple-box` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `anchored-holes` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |
| `hole-family` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |
| `sheet-fold` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |
| `top-sketch-after-chamfer` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |
| `parameter-scope` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `parent-derived-child-size` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `components` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |
| `repeated-parent-attachments` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `assembly-decorator` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |
| `group-hierarchy` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |
| `attach-angle` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |
| `parametric-attach` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `parametric-offset` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `parametric-anchor` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `corner-anchor` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `anchor-topology-mutation` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `assembly-owned-anchor` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `four-corner-l` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `eight-corner-brackets` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `eight-flightcase-corners` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `xz-anchor` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `round-top-sketch` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |
| `circle-negative-extrude` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |
| `sketch-pattern-mirror` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `selective-profile-extrude` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `circular-feature-pattern` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `rectangular-pattern` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `slot-family` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |
| `rounded-rectangle-sketch` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |
| `primitive-csg` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |
| `bracket` | PASS | PASS | PASS | PASS | PASS | N/R | PASS |

## Native visual evidence

### Parameterized Box (`simple-box`)

- `../native/simple-box/model.png`
- `../native/simple-box/goal-front.png`
- `../native/simple-box/goal-iso.png`
- `../native/simple-box/goal-right.png`
- `../native/simple-box/model-front.png`
- `../native/simple-box/model-iso.png`
- `../native/simple-box/model-right.png`
- `../native/simple-box/overlay-front.png`
- `../native/simple-box/overlay-iso.png`
- `../native/simple-box/overlay-right.png`
- `../native/simple-box/visual-diff-front.png`
- `../native/simple-box/visual-diff-iso.png`
- `../native/simple-box/visual-diff-right.png`

### Face-relative hole with native pattern (`anchored-holes`)

- `../native/anchored-holes/model.png`
- `../native/anchored-holes/goal-front.png`
- `../native/anchored-holes/goal-iso.png`
- `../native/anchored-holes/goal-right.png`
- `../native/anchored-holes/goal-top.png`
- `../native/anchored-holes/model-front.png`
- `../native/anchored-holes/model-iso.png`
- `../native/anchored-holes/model-right.png`
- `../native/anchored-holes/model-top.png`
- `../native/anchored-holes/overlay-front.png`
- `../native/anchored-holes/overlay-iso.png`
- `../native/anchored-holes/overlay-right.png`
- `../native/anchored-holes/overlay-top.png`
- `../native/anchored-holes/visual-diff-front.png`
- `../native/anchored-holes/visual-diff-iso.png`
- `../native/anchored-holes/visual-diff-right.png`

### Native Hole family (`hole-family`)

- `../native/hole-family/model.png`
- `../native/hole-family/goal-front.png`
- `../native/hole-family/goal-iso.png`
- `../native/hole-family/goal-right.png`
- `../native/hole-family/goal-top.png`
- `../native/hole-family/model-front.png`
- `../native/hole-family/model-iso.png`
- `../native/hole-family/model-right.png`
- `../native/hole-family/model-top.png`
- `../native/hole-family/overlay-front.png`
- `../native/hole-family/overlay-iso.png`
- `../native/hole-family/overlay-right.png`
- `../native/hole-family/overlay-top.png`
- `../native/hole-family/visual-diff-front.png`
- `../native/hole-family/visual-diff-iso.png`
- `../native/hole-family/visual-diff-right.png`

### Flat sheet, through hole and 90° fold (`sheet-fold`)

- `../native/sheet-fold/model.png`
- `../native/sheet-fold/goal-front.png`
- `../native/sheet-fold/goal-iso.png`
- `../native/sheet-fold/goal-right.png`
- `../native/sheet-fold/goal-top.png`
- `../native/sheet-fold/model-front.png`
- `../native/sheet-fold/model-iso.png`
- `../native/sheet-fold/model-right.png`
- `../native/sheet-fold/model-top.png`
- `../native/sheet-fold/overlay-front.png`
- `../native/sheet-fold/overlay-iso.png`
- `../native/sheet-fold/overlay-right.png`
- `../native/sheet-fold/overlay-top.png`
- `../native/sheet-fold/visual-diff-front.png`
- `../native/sheet-fold/visual-diff-iso.png`
- `../native/sheet-fold/visual-diff-right.png`

### TOP Sketch after chamfer (`top-sketch-after-chamfer`)

- `../native/top-sketch-after-chamfer/model.png`
- `../native/top-sketch-after-chamfer/goal-front.png`
- `../native/top-sketch-after-chamfer/goal-iso.png`
- `../native/top-sketch-after-chamfer/goal-right.png`
- `../native/top-sketch-after-chamfer/goal-top.png`
- `../native/top-sketch-after-chamfer/model-front.png`
- `../native/top-sketch-after-chamfer/model-iso.png`
- `../native/top-sketch-after-chamfer/model-right.png`
- `../native/top-sketch-after-chamfer/model-top.png`
- `../native/top-sketch-after-chamfer/overlay-front.png`
- `../native/top-sketch-after-chamfer/overlay-iso.png`
- `../native/top-sketch-after-chamfer/overlay-right.png`
- `../native/top-sketch-after-chamfer/overlay-top.png`
- `../native/top-sketch-after-chamfer/visual-diff-front.png`
- `../native/top-sketch-after-chamfer/visual-diff-iso.png`
- `../native/top-sketch-after-chamfer/visual-diff-right.png`

### Explicit component parameters and shared dependencies (`parameter-scope`)

- `../native/parameter-scope/model.png`
- `../native/parameter-scope/goal-front.png`
- `../native/parameter-scope/goal-iso.png`
- `../native/parameter-scope/goal-right.png`
- `../native/parameter-scope/model-front.png`
- `../native/parameter-scope/model-iso.png`
- `../native/parameter-scope/model-right.png`
- `../native/parameter-scope/overlay-front.png`
- `../native/parameter-scope/overlay-iso.png`
- `../native/parameter-scope/overlay-right.png`
- `../native/parameter-scope/visual-diff-front.png`
- `../native/parameter-scope/visual-diff-iso.png`
- `../native/parameter-scope/visual-diff-right.png`

### Child dimensions derived from parent parameters (`parent-derived-child-size`)

- `../native/parent-derived-child-size/model.png`
- `../native/parent-derived-child-size/goal-front.png`
- `../native/parent-derived-child-size/goal-iso.png`
- `../native/parent-derived-child-size/goal-right.png`
- `../native/parent-derived-child-size/model-front.png`
- `../native/parent-derived-child-size/model-iso.png`
- `../native/parent-derived-child-size/model-right.png`
- `../native/parent-derived-child-size/overlay-front.png`
- `../native/parent-derived-child-size/overlay-iso.png`
- `../native/parent-derived-child-size/overlay-right.png`
- `../native/parent-derived-child-size/visual-diff-front.png`
- `../native/parent-derived-child-size/visual-diff-iso.png`
- `../native/parent-derived-child-size/visual-diff-right.png`

### Reuse one component definition in two placements (`components`)

- `../native/components/model.png`
- `../native/components/goal-front.png`
- `../native/components/goal-iso.png`
- `../native/components/goal-right.png`
- `../native/components/model-front.png`
- `../native/components/model-iso.png`
- `../native/components/model-right.png`
- `../native/components/overlay-front.png`
- `../native/components/overlay-iso.png`
- `../native/components/overlay-right.png`
- `../native/components/visual-diff-front.png`
- `../native/components/visual-diff-iso.png`
- `../native/components/visual-diff-right.png`

### Attachments on repeated parent occurrences (`repeated-parent-attachments`)

- `../native/repeated-parent-attachments/model.png`
- `../native/repeated-parent-attachments/goal-front.png`
- `../native/repeated-parent-attachments/goal-iso.png`
- `../native/repeated-parent-attachments/goal-right.png`
- `../native/repeated-parent-attachments/model-front.png`
- `../native/repeated-parent-attachments/model-iso.png`
- `../native/repeated-parent-attachments/model-right.png`
- `../native/repeated-parent-attachments/overlay-front.png`
- `../native/repeated-parent-attachments/overlay-iso.png`
- `../native/repeated-parent-attachments/overlay-right.png`
- `../native/repeated-parent-attachments/visual-diff-front.png`
- `../native/repeated-parent-attachments/visual-diff-iso.png`
- `../native/repeated-parent-attachments/visual-diff-right.png`

### Imported @assembly subassembly (`assembly-decorator`)

- `../native/assembly-decorator/model.png`
- `../native/assembly-decorator/goal-front.png`
- `../native/assembly-decorator/goal-iso.png`
- `../native/assembly-decorator/goal-right.png`
- `../native/assembly-decorator/model-front.png`
- `../native/assembly-decorator/model-iso.png`
- `../native/assembly-decorator/model-right.png`
- `../native/assembly-decorator/overlay-front.png`
- `../native/assembly-decorator/overlay-iso.png`
- `../native/assembly-decorator/overlay-right.png`
- `../native/assembly-decorator/visual-diff-front.png`
- `../native/assembly-decorator/visual-diff-iso.png`
- `../native/assembly-decorator/visual-diff-right.png`

### Named native subassembly group (`group-hierarchy`)

- `../native/group-hierarchy/model.png`
- `../native/group-hierarchy/goal-front.png`
- `../native/group-hierarchy/goal-iso.png`
- `../native/group-hierarchy/goal-right.png`
- `../native/group-hierarchy/model-front.png`
- `../native/group-hierarchy/model-iso.png`
- `../native/group-hierarchy/model-right.png`
- `../native/group-hierarchy/overlay-front.png`
- `../native/group-hierarchy/overlay-iso.png`
- `../native/group-hierarchy/overlay-right.png`
- `../native/group-hierarchy/visual-diff-front.png`
- `../native/group-hierarchy/visual-diff-iso.png`
- `../native/group-hierarchy/visual-diff-right.png`

### Native attachment clocking angle (`attach-angle`)

- `../native/attach-angle/model.png`
- `../native/attach-angle/goal-front.png`
- `../native/attach-angle/goal-iso.png`
- `../native/attach-angle/goal-right.png`
- `../native/attach-angle/model-front.png`
- `../native/attach-angle/model-iso.png`
- `../native/attach-angle/model-right.png`
- `../native/attach-angle/overlay-front.png`
- `../native/attach-angle/overlay-iso.png`
- `../native/attach-angle/overlay-right.png`
- `../native/attach-angle/visual-diff-front.png`
- `../native/attach-angle/visual-diff-iso.png`
- `../native/attach-angle/visual-diff-right.png`

### Editable distance between attached components (`parametric-attach`)

- `../native/parametric-attach/model.png`
- `../native/parametric-attach/goal-front.png`
- `../native/parametric-attach/goal-iso.png`
- `../native/parametric-attach/goal-right.png`
- `../native/parametric-attach/model-front.png`
- `../native/parametric-attach/model-iso.png`
- `../native/parametric-attach/model-right.png`
- `../native/parametric-attach/overlay-front.png`
- `../native/parametric-attach/overlay-iso.png`
- `../native/parametric-attach/overlay-right.png`
- `../native/parametric-attach/visual-diff-front.png`
- `../native/parametric-attach/visual-diff-iso.png`
- `../native/parametric-attach/visual-diff-right.png`

### Editable local offset at an attachment (`parametric-offset`)

- `../native/parametric-offset/model.png`
- `../native/parametric-offset/goal-front.png`
- `../native/parametric-offset/goal-iso.png`
- `../native/parametric-offset/goal-right.png`
- `../native/parametric-offset/model-front.png`
- `../native/parametric-offset/model-iso.png`
- `../native/parametric-offset/model-right.png`
- `../native/parametric-offset/overlay-front.png`
- `../native/parametric-offset/overlay-iso.png`
- `../native/parametric-offset/overlay-right.png`
- `../native/parametric-offset/visual-diff-front.png`
- `../native/parametric-offset/visual-diff-iso.png`
- `../native/parametric-offset/visual-diff-right.png`

### Face anchor follows parent geometry (`parametric-anchor`)

- `../native/parametric-anchor/model.png`
- `../native/parametric-anchor/goal-front.png`
- `../native/parametric-anchor/goal-iso.png`
- `../native/parametric-anchor/goal-right.png`
- `../native/parametric-anchor/model-front.png`
- `../native/parametric-anchor/model-iso.png`
- `../native/parametric-anchor/model-right.png`
- `../native/parametric-anchor/overlay-front.png`
- `../native/parametric-anchor/overlay-iso.png`
- `../native/parametric-anchor/overlay-right.png`
- `../native/parametric-anchor/visual-diff-front.png`
- `../native/parametric-anchor/visual-diff-iso.png`
- `../native/parametric-anchor/visual-diff-right.png`

### Topology-backed corner anchor (`corner-anchor`)

- `../native/corner-anchor/model.png`
- `../native/corner-anchor/goal-front.png`
- `../native/corner-anchor/goal-iso.png`
- `../native/corner-anchor/goal-right.png`
- `../native/corner-anchor/model-front.png`
- `../native/corner-anchor/model-iso.png`
- `../native/corner-anchor/model-right.png`
- `../native/corner-anchor/overlay-front.png`
- `../native/corner-anchor/overlay-iso.png`
- `../native/corner-anchor/overlay-right.png`
- `../native/corner-anchor/visual-diff-front.png`
- `../native/corner-anchor/visual-diff-iso.png`
- `../native/corner-anchor/visual-diff-right.png`

### Explicit topology pick follows parent resize (`anchor-topology-mutation`)

- `../native/anchor-topology-mutation/model.png`
- `../native/anchor-topology-mutation/goal-front.png`
- `../native/anchor-topology-mutation/goal-iso.png`
- `../native/anchor-topology-mutation/goal-right.png`
- `../native/anchor-topology-mutation/model-front.png`
- `../native/anchor-topology-mutation/model-iso.png`
- `../native/anchor-topology-mutation/model-right.png`
- `../native/anchor-topology-mutation/overlay-front.png`
- `../native/anchor-topology-mutation/overlay-iso.png`
- `../native/anchor-topology-mutation/overlay-right.png`
- `../native/anchor-topology-mutation/visual-diff-front.png`
- `../native/anchor-topology-mutation/visual-diff-iso.png`
- `../native/anchor-topology-mutation/visual-diff-right.png`

### Assembly-owned named anchor (`assembly-owned-anchor`)

- `../native/assembly-owned-anchor/model.png`
- `../native/assembly-owned-anchor/goal-front.png`
- `../native/assembly-owned-anchor/goal-iso.png`
- `../native/assembly-owned-anchor/goal-right.png`
- `../native/assembly-owned-anchor/model-front.png`
- `../native/assembly-owned-anchor/model-iso.png`
- `../native/assembly-owned-anchor/model-right.png`
- `../native/assembly-owned-anchor/overlay-front.png`
- `../native/assembly-owned-anchor/overlay-iso.png`
- `../native/assembly-owned-anchor/overlay-right.png`
- `../native/assembly-owned-anchor/visual-diff-front.png`
- `../native/assembly-owned-anchor/visual-diff-iso.png`
- `../native/assembly-owned-anchor/visual-diff-right.png`

### Four centred vertical L-profiles (`four-corner-l`)

- `../native/four-corner-l/model.png`
- `../native/four-corner-l/goal-front.png`
- `../native/four-corner-l/goal-iso.png`
- `../native/four-corner-l/goal-right.png`
- `../native/four-corner-l/model-front.png`
- `../native/four-corner-l/model-iso.png`
- `../native/four-corner-l/model-right.png`
- `../native/four-corner-l/overlay-front.png`
- `../native/four-corner-l/overlay-iso.png`
- `../native/four-corner-l/overlay-right.png`
- `../native/four-corner-l/visual-diff-front.png`
- `../native/four-corner-l/visual-diff-iso.png`
- `../native/four-corner-l/visual-diff-right.png`

### Eight vertical L-profiles: two per side corner (`eight-corner-brackets`)

- `../native/eight-corner-brackets/model.png`
- `../native/eight-corner-brackets/goal-front.png`
- `../native/eight-corner-brackets/goal-iso.png`
- `../native/eight-corner-brackets/goal-right.png`
- `../native/eight-corner-brackets/model-front.png`
- `../native/eight-corner-brackets/model-iso.png`
- `../native/eight-corner-brackets/model-right.png`
- `../native/eight-corner-brackets/overlay-front.png`
- `../native/eight-corner-brackets/overlay-iso.png`
- `../native/eight-corner-brackets/overlay-right.png`
- `../native/eight-corner-brackets/visual-diff-front.png`
- `../native/eight-corner-brackets/visual-diff-iso.png`
- `../native/eight-corner-brackets/visual-diff-right.png`

### Eight flightcase corner protectors (`eight-flightcase-corners`)

- `../native/eight-flightcase-corners/model.png`
- `../native/eight-flightcase-corners/goal-front.png`
- `../native/eight-flightcase-corners/goal-iso.png`
- `../native/eight-flightcase-corners/goal-right.png`
- `../native/eight-flightcase-corners/model-front.png`
- `../native/eight-flightcase-corners/model-iso.png`
- `../native/eight-flightcase-corners/model-right.png`
- `../native/eight-flightcase-corners/overlay-front.png`
- `../native/eight-flightcase-corners/overlay-iso.png`
- `../native/eight-flightcase-corners/overlay-right.png`
- `../native/eight-flightcase-corners/visual-diff-front.png`
- `../native/eight-flightcase-corners/visual-diff-iso.png`
- `../native/eight-flightcase-corners/visual-diff-right.png`

### Anchors on XZ-profile extrusion (`xz-anchor`)

- `../native/xz-anchor/model.png`
- `../native/xz-anchor/goal-front.png`
- `../native/xz-anchor/goal-iso.png`
- `../native/xz-anchor/goal-right.png`
- `../native/xz-anchor/model-front.png`
- `../native/xz-anchor/model-iso.png`
- `../native/xz-anchor/model-right.png`
- `../native/xz-anchor/overlay-front.png`
- `../native/xz-anchor/overlay-iso.png`
- `../native/xz-anchor/overlay-right.png`
- `../native/xz-anchor/visual-diff-front.png`
- `../native/xz-anchor/visual-diff-iso.png`
- `../native/xz-anchor/visual-diff-right.png`

### TOP Sketch on circular body (`round-top-sketch`)

- `../native/round-top-sketch/model.png`
- `../native/round-top-sketch/goal-front.png`
- `../native/round-top-sketch/goal-iso.png`
- `../native/round-top-sketch/goal-right.png`
- `../native/round-top-sketch/model-front.png`
- `../native/round-top-sketch/model-iso.png`
- `../native/round-top-sketch/model-right.png`
- `../native/round-top-sketch/overlay-front.png`
- `../native/round-top-sketch/overlay-iso.png`
- `../native/round-top-sketch/overlay-right.png`
- `../native/round-top-sketch/visual-diff-front.png`
- `../native/round-top-sketch/visual-diff-iso.png`
- `../native/round-top-sketch/visual-diff-right.png`

### Negative circle profile extrusion (`circle-negative-extrude`)

- `../native/circle-negative-extrude/model.png`
- `../native/circle-negative-extrude/goal-front.png`
- `../native/circle-negative-extrude/goal-iso.png`
- `../native/circle-negative-extrude/goal-right.png`
- `../native/circle-negative-extrude/model-front.png`
- `../native/circle-negative-extrude/model-iso.png`
- `../native/circle-negative-extrude/model-right.png`
- `../native/circle-negative-extrude/overlay-front.png`
- `../native/circle-negative-extrude/overlay-iso.png`
- `../native/circle-negative-extrude/overlay-right.png`
- `../native/circle-negative-extrude/visual-diff-front.png`
- `../native/circle-negative-extrude/visual-diff-iso.png`
- `../native/circle-negative-extrude/visual-diff-right.png`

### Associative sketch pattern and mirror (`sketch-pattern-mirror`)

- `../native/sketch-pattern-mirror/model.png`
- `../native/sketch-pattern-mirror/goal-front.png`
- `../native/sketch-pattern-mirror/goal-iso.png`
- `../native/sketch-pattern-mirror/goal-right.png`
- `../native/sketch-pattern-mirror/goal-top.png`
- `../native/sketch-pattern-mirror/model-front.png`
- `../native/sketch-pattern-mirror/model-iso.png`
- `../native/sketch-pattern-mirror/model-right.png`
- `../native/sketch-pattern-mirror/model-top.png`
- `../native/sketch-pattern-mirror/overlay-front.png`
- `../native/sketch-pattern-mirror/overlay-iso.png`
- `../native/sketch-pattern-mirror/overlay-right.png`
- `../native/sketch-pattern-mirror/overlay-top.png`
- `../native/sketch-pattern-mirror/visual-diff-front.png`
- `../native/sketch-pattern-mirror/visual-diff-iso.png`
- `../native/sketch-pattern-mirror/visual-diff-right.png`

### Selective Sketch profile extrusion (`selective-profile-extrude`)

- `../native/selective-profile-extrude/model.png`
- `../native/selective-profile-extrude/goal-front.png`
- `../native/selective-profile-extrude/goal-iso.png`
- `../native/selective-profile-extrude/goal-right.png`
- `../native/selective-profile-extrude/goal-top.png`
- `../native/selective-profile-extrude/model-front.png`
- `../native/selective-profile-extrude/model-iso.png`
- `../native/selective-profile-extrude/model-right.png`
- `../native/selective-profile-extrude/model-top.png`
- `../native/selective-profile-extrude/overlay-front.png`
- `../native/selective-profile-extrude/overlay-iso.png`
- `../native/selective-profile-extrude/overlay-right.png`
- `../native/selective-profile-extrude/overlay-top.png`
- `../native/selective-profile-extrude/visual-diff-front.png`
- `../native/selective-profile-extrude/visual-diff-iso.png`
- `../native/selective-profile-extrude/visual-diff-right.png`

### Native circular feature pattern (`circular-feature-pattern`)

- `../native/circular-feature-pattern/model.png`
- `../native/circular-feature-pattern/goal-front.png`
- `../native/circular-feature-pattern/goal-iso.png`
- `../native/circular-feature-pattern/goal-right.png`
- `../native/circular-feature-pattern/goal-top.png`
- `../native/circular-feature-pattern/model-front.png`
- `../native/circular-feature-pattern/model-iso.png`
- `../native/circular-feature-pattern/model-right.png`
- `../native/circular-feature-pattern/model-top.png`
- `../native/circular-feature-pattern/overlay-front.png`
- `../native/circular-feature-pattern/overlay-iso.png`
- `../native/circular-feature-pattern/overlay-right.png`
- `../native/circular-feature-pattern/overlay-top.png`
- `../native/circular-feature-pattern/visual-diff-front.png`
- `../native/circular-feature-pattern/visual-diff-iso.png`
- `../native/circular-feature-pattern/visual-diff-right.png`

### Native rectangular feature pattern (`rectangular-pattern`)

- `../native/rectangular-pattern/model.png`
- `../native/rectangular-pattern/goal-front.png`
- `../native/rectangular-pattern/goal-iso.png`
- `../native/rectangular-pattern/goal-right.png`
- `../native/rectangular-pattern/goal-top.png`
- `../native/rectangular-pattern/model-front.png`
- `../native/rectangular-pattern/model-iso.png`
- `../native/rectangular-pattern/model-right.png`
- `../native/rectangular-pattern/model-top.png`
- `../native/rectangular-pattern/overlay-front.png`
- `../native/rectangular-pattern/overlay-iso.png`
- `../native/rectangular-pattern/overlay-right.png`
- `../native/rectangular-pattern/overlay-top.png`
- `../native/rectangular-pattern/visual-diff-front.png`
- `../native/rectangular-pattern/visual-diff-iso.png`
- `../native/rectangular-pattern/visual-diff-right.png`

### Native sketch Slot family (`slot-family`)

- `../native/slot-family/model.png`
- `../native/slot-family/goal-front.png`
- `../native/slot-family/goal-iso.png`
- `../native/slot-family/goal-right.png`
- `../native/slot-family/goal-top.png`
- `../native/slot-family/model-front.png`
- `../native/slot-family/model-iso.png`
- `../native/slot-family/model-right.png`
- `../native/slot-family/model-top.png`
- `../native/slot-family/overlay-front.png`
- `../native/slot-family/overlay-iso.png`
- `../native/slot-family/overlay-right.png`
- `../native/slot-family/overlay-top.png`
- `../native/slot-family/visual-diff-front.png`
- `../native/slot-family/visual-diff-iso.png`
- `../native/slot-family/visual-diff-right.png`

### Explicit rounded-rectangle sketch pad (`rounded-rectangle-sketch`)

- `../native/rounded-rectangle-sketch/model.png`
- `../native/rounded-rectangle-sketch/goal-front.png`
- `../native/rounded-rectangle-sketch/goal-iso.png`
- `../native/rounded-rectangle-sketch/goal-right.png`
- `../native/rounded-rectangle-sketch/goal-top.png`
- `../native/rounded-rectangle-sketch/model-front.png`
- `../native/rounded-rectangle-sketch/model-iso.png`
- `../native/rounded-rectangle-sketch/model-right.png`
- `../native/rounded-rectangle-sketch/model-top.png`
- `../native/rounded-rectangle-sketch/overlay-front.png`
- `../native/rounded-rectangle-sketch/overlay-iso.png`
- `../native/rounded-rectangle-sketch/overlay-right.png`
- `../native/rounded-rectangle-sketch/overlay-top.png`
- `../native/rounded-rectangle-sketch/visual-diff-front.png`
- `../native/rounded-rectangle-sketch/visual-diff-iso.png`
- `../native/rounded-rectangle-sketch/visual-diff-right.png`

### Primitive CSG (`primitive-csg`)

- `../native/primitive-csg/model.png`
- `../native/primitive-csg/goal-front.png`
- `../native/primitive-csg/goal-iso.png`
- `../native/primitive-csg/goal-right.png`
- `../native/primitive-csg/model-front.png`
- `../native/primitive-csg/model-iso.png`
- `../native/primitive-csg/model-right.png`
- `../native/primitive-csg/overlay-front.png`
- `../native/primitive-csg/overlay-iso.png`
- `../native/primitive-csg/overlay-right.png`
- `../native/primitive-csg/visual-diff-front.png`
- `../native/primitive-csg/visual-diff-iso.png`
- `../native/primitive-csg/visual-diff-right.png`

### Minimal L-profile (`bracket`)

- `../native/bracket/model.png`
- `../native/bracket/goal-front.png`
- `../native/bracket/goal-iso.png`
- `../native/bracket/goal-right.png`
- `../native/bracket/model-front.png`
- `../native/bracket/model-iso.png`
- `../native/bracket/model-right.png`
- `../native/bracket/overlay-front.png`
- `../native/bracket/overlay-iso.png`
- `../native/bracket/overlay-right.png`
- `../native/bracket/visual-diff-front.png`
- `../native/bracket/visual-diff-iso.png`
- `../native/bracket/visual-diff-right.png`

## Result data

The machine-readable source of this report is `results.json`. Each native case
directory also contains its own `qualification-result.json`, together with the
SolidCraft measurements, saved models, STEP exports and PNG snapshots used as
evidence.

## Qualification model

- **Q1 — Python API:** public API validation and compiler invariants.
- **Q2 — Command contract:** generated SolidCraft command JSON is complete and inspectable.
- **Q3 — Native build:** SolidCraft accepts the command plan and saves an editable design.
- **Q4 — Native semantic validation:** body bounds, feature evidence and joint/anchor relationships are checked against independent expected geometry.
- **Q5 — Parametric mutation:** required saved designs re-solve correctly after parameter changes.
- **Q6 — Visual regression:** fixed front/right/isometric native views are compared with approved reference rasters and diff overlays are retained.

The report structure comes from `qualification/templates/report.md`; CI supplies
the result data but does not construct the document with inline shell markup.

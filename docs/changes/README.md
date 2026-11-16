# Change design records

Design changes are recorded here before or together with implementation.

Naming:

```text
NNNN-short-change-name.md
```

Rules:

- four-digit, monotonically increasing number;
- one change/design per document;
- the document contains the problem, decision, native SolidCraft command contract,
  Forge API contract, lowering and qualification;
- later changes do not rewrite history: add the next numbered document and link
  back to the change it supersedes or extends.

Current records:

- [0001-position-api-design.md](0001-position-api-design.md) — constructor-time `Placement`, removal of private position model parameters, shape placement and SolidCraft lowering. 
- [0002-copy-placement-with-rotation.md](0002-copy-placement-with-rotation.md) — correct native lowering when a copied occurrence combines XYZ Placement with rotation.
- [0003-explicit-component-parameter-publication.md](0003-explicit-component-parameter-publication.md) — restore the original explicit `include=` contract for publishing reusable child-component defaults; parent symbolic bindings remain shared.
- [0004-three-reference-implementations.md](0004-three-reference-implementations.md) — require PythonSCAD, pyBOSL2 and CadQuery reference output for qualification cases unless an explicit technical exception is recorded.

- [0008-stable-forge-occurrence-id.md](0008-stable-forge-occurrence-id.md) — stop using Python object ids to track Forge occurrences; copy gets a new id while group/attach keep the existing one.
- [0009-replay-first-placement.md](0009-replay-first-placement.md) — keep ordinary Placement replay-first: identity first occurrence, numeric unrotated copies, and reject cases that would need guessed occurrence names.
- [0010-replay-safe-attachments.md](0010-replay-safe-attachments.md) — remove guessed occurrence names from attachment commands; use the component name only where SolidCraft 0.42 supports it and reject copied attachment endpoints that need an unavailable native occurrence reference.
- [0011-grouping-is-hierarchy-only.md](0011-grouping-is-hierarchy-only.md) — make `.group()` change browser hierarchy only; groups stay ungrounded and `occurrence.copy(parent=...)` keeps one reusable definition across different groups.
- [0012-definition-identity.md](0012-definition-identity.md) — include every reusable component build input in definition identity and give each native local parameter namespace a unique definition number.
- [0013-correct-0010-placement-cases.md](0013-correct-0010-placement-cases.md) — restore ordinary Placement qualification and bind real SolidCraft occurrence ids through replay variables instead of predicted browser names.
- [0014-parametric-root-grounding.md](0014-parametric-root-grounding.md) — keep parameter-driven root Placement ungrounded on SolidCraft 0.42 so saved parameter edits continue to move the first occurrence.

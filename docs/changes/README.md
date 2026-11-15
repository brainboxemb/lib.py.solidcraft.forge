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

- [0001-position-api-design.md](0001-position-api-design.md) — constructor-time `Placement`, removal of private position model parameters, shape placement and SolidCraft lowering.\n- [0002-copy-placement-with-rotation.md](0002-copy-placement-with-rotation.md) — correct native lowering when a copied occurrence combines XYZ Placement with rotation.

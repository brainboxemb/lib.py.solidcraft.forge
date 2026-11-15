# SCPF repository instructions

Python SCPF is the only supported scripting frontend. SolidCraft remains the
only engine for BRep geometry and native feature history. Forge describes CAD
intent and lowers that intent to SolidCraft commands; it must not grow a second
geometry or mating engine.

## Public API source of truth

The normative public Forge API contract is:

`docs/05-cad-api-design.md`

Read that document before changing a public model expression, placement rule,
anchor rule, Sketch rule or parameter rule.

Do **not** infer public API semantics from:
- the current compiler implementation;
- an existing qualification fixture;
- README or website examples;
- generated command JSON;
- downstream CAD models;
- a numerical workaround that happens to render correctly.

If implementation and the normative API contract disagree, treat that as an
implementation bug or an unresolved API decision. Never make a qualification
fixture pass by adding a copied numeric offset when the API is supposed to
express the relationship semantically.

## Change procedure

For a public API or lowering change:

1. Read `docs/05-cad-api-design.md`.
2. Decide whether the requested behaviour is already part of the contract.
3. If it is already specified, fix the implementation and add a focused
   regression test.
4. If it is not specified, update the normative API contract first.
5. Update the smallest qualification fixture that proves the behaviour.
6. Update generated/derived documentation and examples.
7. Run Q1/Q2 first; run only affected native cases while iterating.
8. Run the complete native qualification before promotion/release.

Keep model objects and CAD feature intent separate from SolidCraft command JSON
and transport. The adapter may translate one high-level feature into multiple
native commands.

## Qualification references

Every qualification case must carry two readable comparison implementations:

- `examples/<case>/pythonscad/model.py`
- `examples/<case>/pybosl2/model.py`

They express the same modelling intent as the Forge fixture. They are reference
models, not alternative Forge specifications. When another library cannot
represent an associative SolidCraft relation, keep the reference geometry
simple and state that limitation in the source instead of inventing equivalent
semantics.

Do not require classic OpenSCAD/BOSL2 `.scad` files when PythonSCAD and
pyBOSL2 already make the comparison clear.

## Qualification performance

A normal model edit should have a short edit-check loop.

- Q1/Q2 must remain fast and independent of SolidCraft.
- Native qualification should support selecting one or more cases.
- Measure build/eval/snapshot/mutation time per case before optimizing startup.
- Do not restart expensive tools unnecessarily when a supported persistent
  session can safely execute the same independent cases.
- Full Q1-Q6 across all cases remains mandatory for a SolidCraft version
  promotion and for the final main-branch qualification.

When changing example models, update Python regressions, generated command
fixtures where applicable, native qualification checks and both reference
implementations. Do not reintroduce the retired SCRF Rust scripting layer.

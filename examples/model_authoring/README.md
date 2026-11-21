# Model authoring Q1/Q2 fixture

> Documentation provenance: issue #213 and its accepted result in PR #214 / commit `4b2801c8a4c6f686b497dbf2927b5b45118c31a5`.

## Purpose

This is the small abstract authoring fixture requested by #213. Its accepted
scope is deliberately Q1/Q2-only: model loading, authoring semantics and Forge
command compilation.

It proves:

- one explicit public component parameter;
- fixed constants and private build-time values remain non-parameters;
- separate physical parts use components/occurrences;
- one Block definition is reused through `occurrence.copy`;
- material intent is represented in the generated command contract.

The fixture does **not** claim native SolidCraft Q3+ verification. The #213
result explicitly records that boundary. Native material behavior is qualified
separately from this authoring fixture.

The current executing owner is
`scpf/tests/test_model_authoring.py::test_model_authoring_fixture_keeps_q1_q2_contract`.

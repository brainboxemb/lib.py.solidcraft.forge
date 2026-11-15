# Forge CAD design

This directory contains the architecture and design decisions that must exist
before Forge compiler changes are implemented.

The public API documentation explains *how a model is written*. These design
documents explain *what Forge means*, *which SolidCraft capability implements
that meaning*, and *which invariants the compiler must preserve*.

## Documents

1. [Foundational CAD model](01-foundational-cad-model.md)
   - component definition;
   - occurrence placement;
   - attachment relationships;
   - the basic create/place/copy/attach use cases;
   - public Placement semantics.

2. [SolidCraft execution and occurrence identity](02-execution-and-identity.md)
   - native SolidCraft 0.42 capabilities;
   - runtime occurrence ids and paths;
   - static replay limitations;
   - lowering rules and forbidden fallbacks.

3. [Forge execution plan and runtime bindings](03-execution-plan.md)
   - logical result bindings and $ref values;
   - phased engine.batch execution;
   - checkpoint-backed atomicity;
   - replay-safe runtime identity.

## Change rule

A compiler change that introduces a new CAD representation or fallback must be
designed here first. The required order is:

1. state the CAD use case;
2. identify the native SolidCraft capability and its limitations;
3. compare alternatives;
4. record the selected design and rejected alternatives;
5. define qualification evidence;
6. implement;
7. release only after the foundational qualification is green.

An implementation problem is not permission to silently substitute another CAD
concept. In particular, placement must never become a joint merely because the
native placement path is inconvenient.

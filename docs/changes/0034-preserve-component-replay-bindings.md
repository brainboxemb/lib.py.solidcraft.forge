# 0034 — preserve replay bindings in reusable components

Status: **implemented**  
Issues: **#279, #288**  
Implementation: **PR #289**  
SolidCraft target: **0.42.0**

## Problem

A reusable component could compile correctly on its own and still produce an
invalid replay document when used inside an assembly.

Commands such as `model.faces` carry replay bindings:

```text
model.faces
  bind -> $face_point_1, $face_index_1

sketch.create
  plane.face  = $face_point_1
  plane.index = $face_index_1
```

The assembly namespacing pass rebuilt component commands from only
`command` and `params`. Command-level fields such as `bind` were lost,
while later commands still referenced the replay variables.

## Fix

Component namespacing now treats replay metadata as part of the command.

For every reusable component definition Forge:

- preserves command-level fields such as `bind`;
- namespaces replay-variable bind keys with the component definition prefix;
- rewrites exact replay-variable references in command params;
- rewrites replay-variable references inside binding selectors such as
  `prepend`;
- leaves normal literal strings unchanged.

Two component definitions can therefore both start with local names such as
`$face_point_1` without colliding in the combined replay document.

## Unit-test coverage

The regression tests cover:

- direct `bind` preservation;
- consistent rewriting of bind keys and later command params;
- replay variables used by `prepend` selectors;
- distinct replay namespaces for different component definitions;
- a reusable component with a TOP-attached Sketch that must pass
  `validate_replay_document(...)`;
- existing parameter namespacing and normal strings.

The downstream HUB75 assembly remains a useful model-level regression, but the
primary guard is now in Forge unit tests.

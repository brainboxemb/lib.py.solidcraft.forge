# 0034 — preserve replay bindings in reusable components

Status: **implementation in qualification**  
Issue: **#279**  
SolidCraft target: **0.42.0**

## Problem

SCPF 0.7.0 can emit replay-bound commands such as native face lookup for an
attached Sketch:

```text
model.faces
  bind -> $face_point_1, $face_index_1

sketch.create
  plane.face  = $face_point_1
  plane.index = $face_index_1
```

The same model worked when compiled standalone, but failed when compiled as a
reusable component inside an assembly.

The component namespacing pass copied only `command` and `params`. It
discarded the command's `bind` metadata. The later `sketch.create` still
referenced the replay variables, so assembly replay failed with an
"uses replay variable before binding" error.

## Decision

Component namespacing now preserves replay bindings.

Component-local replay variables are also renamed with the same stable
definition prefix used for component-local parameters.

Example:

```text
standalone:
  $face_point_1
  $face_index_1

definition 1, LeftPanel:
  $d1_LeftPanel_face_point_1
  $d1_LeftPanel_face_index_1
```

All later exact replay-variable references in that component definition are
rewritten to the same names.

Ordinary strings are not rewritten.

## Why namespace replay variables

Two reusable component definitions may both contain attached Sketches. Without
definition-local replay-variable names, both definitions could independently
emit `$face_point_1` or other identical temporary names.

The component definition prefix keeps those runtime values independent while
preserving deterministic replay output.

## Qualification

Regression coverage uses two different reusable component definitions. Each
contains:

- one Box;
- one TOP-attached Sketch;
- one Circle cut.

The compiled assembly must contain two independent `model.faces` bindings and
two matching `sketch.create` references:

```text
$d1_LeftPanel_face_point_1
$d1_LeftPanel_face_index_1

$d2_RightPanel_face_point_1
$d2_RightPanel_face_index_1
```

The fix must also keep all existing occurrence replay bindings unchanged.

---
title: Reading model pages
weight: 10
---

Each model page brings the geometry, source and published build evidence together.

## Choose a model

Use [Examples](../../examples/) to explore practical models or [Verification](../../verification/) to inspect models used to qualify CAD behaviour. A model can appear in both catalogues.

## Inspect the geometry

The featured result shows the published implementation preview; native SolidCraft builders supply a snapshot of the saved native model rather than an STL rendering. The expected setup diagram describes declared geometry requirements. The two are distinct: a conceptual envelope is not a verification render. Published files are linked below the build evidence.

A missing preview or file means that the corresponding artifact is not available in the published build.

## Read the source

The featured SolidCraft/SCPF source follows immediately after the opening imagery. A collapsed generated command sequence follows the source where available. Each independent implementation then displays its code next to its own result image. The consolidated image overview includes the expected setup, native/result previews and published visual-evidence images; the check overview follows it. Background explanation and raw evidence come afterwards.

For example, a centred box in CadQuery can be described as:

```python
import cadquery as cq

model = cq.Workplane("XY").box(40, 30, 10)
```

The displayed source comes from the site branch. The build revision recorded in the evidence section identifies the source used to produce the published artifacts.

## Understand verification

Each implementation has its own build and verification status. Named verification stages may check different properties, such as mesh geometry or the native CAD document. Open an available stage report to inspect its checks.

A model is marked Verified when its published result reports a passing status. No published build evidence is displayed explicitly when it is unavailable.

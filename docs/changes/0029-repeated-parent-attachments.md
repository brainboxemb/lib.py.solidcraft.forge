# 0029 — repeated parent attachment qualification

Status: **implemented and Q4/Q5 qualified; final exact-head Q1-Q6 gate required before merge**  
Issue: **#162**  
Foundation issue: **#164**  
SolidCraft target: **0.42.0**

## Problem

Forge must support a basic reusable assembly case in which two occurrences of
one Parent definition each have one attached child.

A previous HUB75-derived native test found that two disconnected rigid-joint
graphs can behave differently after a saved parameter mutation: the child on
the grounded graph followed the rebuilt parent while the child on the floating
graph kept its previous pose.

The compiler has since changed substantially. Occurrence ids are now bound to
replay variables and normal attachments no longer emit the old child seed
`occurrence.move`. The old proposed patch must therefore not be applied
without reproducing the problem against the current compiler.

## Minimal case

The qualification fixture uses only rectangular solids:

- Parent: 20 x 20 x 40 mm;
- two Parent occurrences at X=0 and X=60;
- Marker: 10 x 10 x 10 mm;
- one Marker attached TOP-to-BOTTOM to each Parent;
- one shared document parameter `parent_height=40 mm`.

There are exactly two authored rigid attachments.

## Command contract

Forge must emit:

- one reusable Parent definition and one copied Parent occurrence;
- one reusable Marker definition and one copied Marker occurrence;
- exactly two `joint.create(type="rigid")` commands;
- replay-bound occurrence ids for both joint A/B sides;
- no generated placement joint;
- one computed seed `occurrence.move` for each normally attached Marker,
  addressed through its replay-bound occurrence id;
- those seed translations retain the same parameter dependencies as the
  authored mating position.

The second Parent's ordinary numeric X placement remains an
`occurrence.copy(..., translate=[60,0,0])`. The seed moves are occurrence
creation state, not additional assembly relationships.

## Native mutation

Q5 changes:

```text
parent_height: 40 mm -> 60 mm
```

without rerunning Python.

Expected result:

- both Parent bodies become 60 mm tall;
- both Marker bodies move from Z=40..50 to Z=60..70;
- the second disconnected graph is required to follow just like the first.

If the current compiler fails this case, the native evidence from this minimal
fixture defines the required correction. Do not restore the historical
HUB75-specific workaround by assumption.

## Foundation role

This case supplies the previously missing foundation scenario from #164:
repeat a parent definition and attach children to both occurrences, then prove
saved-design mutation without relying on generated browser names.

## First native reproduction

The first SolidCraft 0.42 run reproduced #162 with the minimal fixture.

The first joint graph was correct. The second Parent body was correctly copied
to X=60, but its Marker stayed at the world origin both before and after the
saved parent-height mutation.

`joint.inspect` showed why:

- the second joint had the correct native Parent occurrence id;
- Forge sent TOP-face pick `[0,0,40]`;
- SolidCraft interpreted that as a world pick and converted it to
  `[-60,0,40]` in Parent:2 local coordinates;
- no native face reference was stored for that parent side.

The occurrence id was therefore not the problem. The geometry pick was in the
wrong coordinate frame.

## Native findings and correction

The first correction changed the copied Parent's joint pick from local-like
`[0,0,40]` to the correct world point `[60,0,40]`.

A second native run then proved that this was necessary but not sufficient.
`joint.inspect` now stored the correct `F3:+z` topology reference on
Parent:2, yet Marker:2 still remained at the world origin. SolidCraft 0.42 does
not choose the intended placement for a completely floating second rigid-joint
graph.

Forge therefore uses the Placement already computed by `attach()` as a
**seed pose** before `joint.create`:

```text
occurrence.move("$marker_occurrence_1", translate=[0, 0, parent_height])
occurrence.move("$marker_occurrence_2", translate=[60, 0, parent_height])
```

The seed Placement is not a hidden relationship. It only places the ungrounded
child at the authored mating position before the real rigid joint is created.

For this to remain associative, the seed calculation must preserve symbolic
dependencies. Forge now keeps symbolic rectangular anchor coordinates plus
symbolic attachment `gap`/`offset` values while calculating that Placement.
Concrete values are still read for validation and for the numeric topology
pick that SolidCraft requires when the joint is created.

The native parent and child picks are then evaluated at their current seeded
world positions. For the second graph that means both sides select around
X=60 instead of selecting Parent:2 by id while giving it a point near X=0.

This correction does not:

- predict a SolidCraft browser name;
- add a generated placement joint;
- replace `attach()` with Placement semantics;
- change the public attachment API.

The explicit `Attach ...` joint remains the only relationship. The Q2
contract proves the two replay-bound seed moves, both world-space joint picks
and exactly two authored rigid joints. Q4/Q5 must prove the saved SolidCraft
design places and mutates both disconnected graphs correctly.

## Native qualification result

The corrected source-matched SolidCraft 0.42 run
(`156c88f8bb4297fbb203b9abbea3e282bbf152a7`) proved:

- Q1 PASS — the two Parent and two Marker occurrences retain distinct Forge
  occurrence identity while sharing their respective definitions;
- Q2 PASS — two replay-bound Marker seed moves, two replay-bound rigid joints,
  correct world picks on both sides and no generated Placement joint;
- Q3 PASS — the native design builds and saves without joint errors;
- Q4 PASS — all four bodies match their declared baseline bounds and both
  Markers sit at Z=40..50 on their own Parent;
- Q5 PASS — after saved `parent_height: 40 -> 60 mm`, both Parents rebuild
  and both disconnected Marker graphs move to Z=60..70 without rerunning
  Python;
- native `joint.inspect` resolves `F3:+z` on both Parent occurrences and
  `F7:-z` on both Marker occurrences;
- Q6 expected-shape evidence PASS. The front/right/isometric renders from this
  run were reviewed against the declared geometry and approved as the initial
  render-regression baseline.

The final merge gate must rerun Q1-Q6 on the eventual squashed branch head so
the approved baseline and all documentation changes are tested together.

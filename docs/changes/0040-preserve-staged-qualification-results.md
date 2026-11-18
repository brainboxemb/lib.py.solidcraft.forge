# 0040 — Preserve canonical staged qualification results

**Tracks:** issue #345  
**Scope:** staged Q1–Q6 result collection and persistent build/site evidence.

## Problem

The individually rerunnable staged qualification completes Q1–Q6 successfully,
but stopped producing the canonical per-case
`native/<case>/qualification-result.json`.

`build.json` could therefore truthfully record `q1-q6-full` while the site
could not read `levels.q1..q6`. API coverage then reported Q6 as missing even
though the Q6 stage passed.

## Decision

Keep `qualification/results.py` as the single schema-v4 result collector.

For staged runs, the collector reads the stage-state files plus the existing
native/visual validation output and reconstructs the same canonical result
contract that was produced before staged execution was introduced.

The staged runner invokes that collector after all selected cases pass. It must
fail if any selected case does not collect to overall PASS.

Do not teach the site about stage files and do not introduce a second
qualification-result format.

When the site consumes a normalized build, it resolves the SCPF record and
native-verification state independently for every qualification slug. Site
generation must not reuse `case_record`, `case_verified`, or any equivalent
state from an earlier examples/qualification loop iteration.

Presentation-only site builds may have a different current source commit and
qualification evidence commit. Their site tests must use the selected
`build.json.source_commit` as the evidence SHA rather than assuming the site
source SHA produced the reused qualification evidence.

## Persistent output

A successful affected/full Q1–Q6 run must contain:

```text
native/<case>/qualification-result.json
```

before `scripts/generated_output.py assemble-build` runs. The normal native
tree copy then persists it automatically under:

```text
build/<scope>/examples/<case>/scpf/qualification-result.json
```

## Verification

Regression coverage proves that staged Q1/Q2, compile/replay/evaluate,
native validation and visual validation produce one schema-v4 per-case result
with Q1–Q6 status, including Q6 PASS.

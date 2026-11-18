# Generated output and publication design

Status: **normative**

This document defines how Forge source, technical build output, qualification
evidence and the public website are stored, verified and published.

If a workflow, script, test or repository instruction disagrees with this
document, the implementation is wrong until this document is deliberately
changed.

The purpose is simple: every kind of data has one owner, every event has one
defined effect, and every generated write is scoped so it cannot damage
unrelated output.

## 1. Persistent branch roles

Forge has three persistent branches:

| Branch | Purpose | Human-edited |
| --- | --- | --- |
| `main` | source, tests and documentation | yes, through PRs |
| `build` | generated technical output and qualification evidence | no |
| `gh-pages` | generated public website | no |

An open PR may add one temporary source branch. Closing or merging that PR
removes the need for that branch.

Generated staging branches such as `preview-output`, `qualified-output` or
`model-output` do not exist in this design.

Normal steady state is therefore:

```text
main
build
gh-pages
```

## 2. One canonical store per kind of data

| Information | Canonical store |
| --- | --- |
| editable Forge source | `main` / PR source branch |
| generated SolidCraft command JSON | `build` |
| native SolidCraft files | `build` |
| STEP / SC / STL files | `build` |
| native renders and screenshots | `build` |
| measurements and validation JSON | `build` |
| reference-library results/renders | `build` |
| cross-case qualification reports | `build` |
| generated technical diagrams | `build` |
| public documentation HTML | `gh-pages` |
| public Qualification HTML | `gh-pages/qualification/` |
| PR website preview | `gh-pages/previews/pr-<number>/` |

GitHub Actions artifacts are temporary transport/debug artifacts. They are not a
canonical database.

If evidence exists on `build`, a later site build reads it from `build`.
It must not search old workflow runs to rediscover the same evidence.

## 3. Build branch layout

`build` has two namespaces:

```text
main/
  build.json
  examples/
    <case>/
      scpf/
      pythonscad/
      pybosl2/
      cadquery/
      build123d/
  qualification/

pr/
  <number>/
    build.json
    examples/
      <case>/
        <implementation>/
    qualification/
```

The path below the scope follows the source item, not the workflow that produced
it.

Example:

```text
examples/simple-box/scpf/model.py
-> build/main/examples/simple-box/scpf/...

examples/simple-box/cadquery/model.py
-> build/main/examples/simple-box/cadquery/...
```

Workflow-local trees such as `output/native`, `output/references` and
`output/qualification` may exist while a job is running. They are normalized
before publication.

Top-level producer directories such as `native/` and `references/` are
forbidden on the persistent `build` branch.

## 4. Pages branch layout

The stable website occupies the root of `gh-pages`.

```text
/
  index.html
  guide/
  reference/
  qualification/
  cheatsheet/
  ...
  provenance.json

previews/
  pr-<number>/
    index.html
    guide/
    reference/
    qualification/
    ...
    provenance.json
```

The public `qualification/` directory is intentional. It contains the readable
presentation of qualification status and evidence.

It must not contain copies of technical build evidence such as:

- `.sc`, `.step` or `.stl`;
- generated command JSON;
- measurement/result/validation JSON;
- native renders already stored on `build`;
- reference-library render/result files already stored on `build`.

Qualification HTML links to the corresponding canonical files on `build`.

## 5. Evidence scope for a website

A website build always uses one explicit technical evidence scope.

### Stable site

```text
build/main
```

### Presentation-only PR

```text
build/main
```

A presentation-only PR does not create `build/pr/<number>/`.

### Technical PR with affected cases

```text
build/pr/<number>
```

The website source commit and the evidence commit may differ for a
presentation-only change. Provenance records both.

## 6. Verification strategy

Do not run every model after every edit.

### 6.1 Preflight

Every relevant PR first runs a cheap preflight:

- compile Python;
- validate workflow YAML structure;
- run publication/layout contract tests;
- build and test the website;
- determine affected qualification cases.

A preflight failure stops expensive work.

### 6.2 Affected verification

For API/model work, select cases from:

- changed `examples/<case>/...` paths;
- Q1/Q2 tests referenced by `qualification/case_evidence.py`;
- explicit shared case/evidence registry changes.

A Forge source change without a proving case is an error. Do not hide that by
running all cases.

### 6.3 Final gate by risk

| Change | Required final gate |
| --- | --- |
| site/docs/presentation only | preflight |
| ordinary affected API/model contract | affected Q1/Q2 |
| native/geometry-sensitive Forge change | affected Q1-Q6 |
| foundational compiler/replay/runtime change | full Q1-Q6 |
| SolidCraft promotion | full Q1-Q6 |
| release | full Q1-Q6 |

The final gate is a promotion rule. It is not a reason to make every PR
iteration expensive.

## 7. Event matrix

This table is normative.

| Event | Verification | `build` effect | `gh-pages` effect |
| --- | --- | --- | --- |
| presentation-only PR update | preflight | none | replace `previews/pr-N/` |
| technical PR update | preflight + affected checks | replace `pr/N/` | replace `previews/pr-N/` |
| PR close | none | remove only `pr/N/` if present | remove only `previews/pr-N/` |
| presentation-only merge | preflight already passed; reuse `build/main` | none | replace stable root, preserve previews |
| technical merge | required final gate | replace `main/` after pass | replace stable root, preserve previews |
| release / SolidCraft promotion | full qualification | replace `main/` after pass | replace stable root, preserve previews |

A site-only merge must never trigger full model qualification merely because
site code changed.

## 8. Publication ownership and locks

There are two generated destinations and therefore two global writer locks:

```text
build     -> scpf-build-publish
gh-pages  -> scpf-pages-publish
```

Every writer to the same destination uses the same lock.

For generated branch publication:

```text
cancel-in-progress: false
```

A newer publication may wait. It must not cancel a writer after that writer has
read the destination and before it pushes an updated tree.

## 9. Namespace ownership

A publisher may modify only the namespace it owns.

PR technical publication:

```text
build/pr/<number>/
```

PR website publication:

```text
gh-pages/previews/pr-<number>/
```

Stable technical publication:

```text
build/main/
```

Stable website publication:

```text
gh-pages root, except previews/
```

A stable Pages replacement preserves the current `previews/` tree while
holding the Pages writer lock.

PR cleanup removes only its own namespace while holding the same destination
lock. Cleanup must never rebuild or replace the stable root.

## 10. Provenance

Every technical scope contains `build.json`.

Required fields:

- schema version;
- scope (`main` or `pr`);
- source ref;
- source commit;
- PR number for PR scope;
- Forge version;
- SolidCraft version when applicable;
- workflow run id;
- verification level and status;
- generation time.

Every website root contains `provenance.json`.

For normal technical publication:

```text
site source commit == evidence commit
```

For presentation-only publication:

```text
site source commit = current main/PR commit
evidence commit    = build/main source commit
```

Both commits are explicit. Reused evidence must never be presented as if the
presentation-only source commit was fully requalified.

## 11. Site consumption of technical evidence

`build` is the technical source of truth.

A site-only build reads:

```text
build/main/build.json
build/main/examples/...
build/main/qualification/...
```

It does not search Actions run history for the last passing qualification.

The site generator may inspect a local checkout/copy of that evidence while
rendering HTML. Emitted evidence links and image URLs point to the canonical
`build/<scope>/...` namespace.

Technical evidence is not copied into Pages.

## 12. Workflow responsibilities

Workflow YAML is orchestration only.

Allowed:

- triggers;
- checkout;
- Python/tool setup;
- cache setup;
- calling repository scripts;
- temporary diagnostic artifact upload;
- calling one publication action with already prepared output.

Repository rules belong in tested Python:

- changed-path classification;
- affected-case selection;
- build-tree normalization;
- evidence-scope selection;
- provenance validation;
- stable Pages assembly;
- PR cleanup target calculation;
- generated-tree validation.

Forbidden in workflows:

- model-specific JSON assertions;
- large `git diff` classification algorithms;
- embedded Python one-liners implementing repository policy;
- duplicated branch-layout rules;
- duplicated cleanup rules.

## 13. Hard invariants

CI tests these directly.

1. A complete stable site contains `gh-pages/qualification/`.
2. Pages qualification contains no technical evidence copies.
3. Qualification HTML links to `build/<scope>/...`.
4. A presentation-only PR creates no `build/pr/N`.
5. A technical PR writes only `build/pr/N`.
6. A PR preview writes only `gh-pages/previews/pr-N`.
7. Closing one PR cannot delete another PR's output.
8. Stable Pages replacement preserves all current previews.
9. Every `gh-pages` writer uses `scpf-pages-publish`.
10. Every `build` writer uses `scpf-build-publish`.
11. Site-only changes do not trigger full technical qualification.
12. Forge source changes without a proving case fail selection.
13. Stable technical publication requires passing final verification.
14. Site-only publication reads `build/main`, not Actions-run history.
15. Generated branches contain no editable source-of-truth files.

## 14. Failure and recovery

If generated output becomes inconsistent:

1. identify which invariant failed;
2. fix the publisher/assembly code;
3. regenerate the affected namespace;
4. run the publication/layout tests;
5. do not treat hand-editing generated branch files as the normal repair.

PR cleanup is idempotent. Removing an already absent PR scope is success.

## 15. Acceptance scenarios

This design is not implemented until all scenarios are demonstrated.

### A. Presentation-only PR

Change only site presentation code.

Expected:

- preflight passes;
- affected cases = none;
- reference smoke skipped;
- no `build/pr/N`;
- one Pages preview;
- Qualification HTML exists;
- evidence links point to `build/main`.

### B. One-case API/model PR

Change Forge/API code plus one proving case.

Expected:

- selector names only affected case(s);
- technical output exists only under `build/pr/N`;
- one preview exists under `previews/pr-N`;
- unrelated qualification cases are not rebuilt during normal iteration.

### C. PR close

Expected:

- only that PR's build/preview scopes disappear;
- stable site/build stay unchanged;
- other open PR scopes remain.

### D. Presentation-only merge

Expected:

- no full Q1-Q6 run;
- `build/main` remains unchanged;
- stable Pages rebuilds from current source plus `build/main` evidence;
- `qualification/` remains public;
- previews are preserved.

### E. Technical merge

Expected:

- required final gate passes;
- `build/main` is replaced by output from that technical source;
- stable Pages uses the same evidence;
- previews are preserved.

### F. Concurrent Pages operations

Run stable publication and PR cleanup close together.

Expected:

- both serialize on `scpf-pages-publish`;
- stable root remains current;
- only the intended PR preview disappears;
- no stable directory is lost.

## 16. Reviewer checklist

A reviewer should reject a change when any answer is unclear:

1. Which source commit is being verified?
2. Which cases are affected?
3. Which evidence scope is read?
4. Which exact generated namespace may be written?
5. Which global lock protects that write?
6. Which provenance records source and evidence commits?
7. Can this event overwrite unrelated PR/stable output?
8. Does site-only work avoid technical qualification?
9. Are technical files kept out of Pages?
10. Is the behavior covered by an automated contract test?

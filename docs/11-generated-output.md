# Generated output and publication design

Status: **proposed normative contract — implementation is not yet compliant**

This document defines the target design for Forge source, verification,
technical build output and the public website.

Do not call this design implemented until every acceptance scenario in this
document passes against the real generated branches.

If workflow/code and this document disagree, either the implementation is wrong
or this document must be deliberately changed first.

## 1. Goals

The design has four goals:

1. a small change builds as little as possible;
2. technical evidence is never silently lost or mislabeled;
3. concurrent/out-of-order workflow runs cannot overwrite newer output;
4. a reviewer can determine from changed files exactly what must run and what
   may be published.

Correctness must not depend on GitHub Actions concurrency queues behaving as a
reliable message queue.

## 2. Terms

**Presentation-only change**  
Changes public presentation or documentation but does not change any technical
case input, technical derived output or toolchain input.

**Derived-only change**  
Changes reports/diagrams/aggregation that can be regenerated from existing
per-case evidence without executing model cases.

**Technical case change**  
Changes the input hash of one or more qualification cases.

**Model-sensitive change**  
Changes Forge behavior that requires SolidCraft model verification for affected
cases.

**Foundational change**  
Changes compiler/replay/runtime behavior shared so broadly that the safe final
gate is the complete registered qualification set.

**Technical equivalence**  
Two source trees are technically equivalent for a case when that case's
calculated input hash is equal.

## 3. Persistent branch roles

Forge has three persistent branches:

| Branch | Purpose | Human-edited |
| --- | --- | --- |
| `main` | source, tests and documentation | yes, through PRs |
| `build` | generated technical evidence | no |
| `gh-pages` | generated public website | no |

An open PR may add one temporary source branch. Generated staging branches such
as `preview-output`, `qualified-output` and `model-output` do not exist.

Normal steady state:

```text
main
build
gh-pages
```

## 4. Canonical ownership

| Information | Canonical store |
| --- | --- |
| editable source | `main` / PR source branch |
| command JSON | `build` |
| model verification files | `build` |
| STEP/SC/STL | `build` |
| model verification renders | `build` |
| measurements/validation JSON | `build` |
| reference-library results/renders | `build` |
| per-case verification metadata | `build` |
| derived technical reports/diagrams | `build` |
| public HTML | `gh-pages` |
| public Qualification HTML | `gh-pages/qualification/` |
| PR website preview | `gh-pages/previews/pr-N/` |

Actions artifacts are temporary transport/debug data, not a canonical store.

The repository is public. Public Qualification pages may therefore link to
immutable commits on the public `build` branch.

## 5. Build branch layout

`build/main` is a **complete baseline** for every currently registered case.

`build/pr/N` is a **sparse overlay** containing only cases changed/verified by
that PR.

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
  N/
    build.json
    examples/
      <affected-case>/
        <implementation>/
    qualification/
```

The replacement unit is:

```text
examples/<case>/<implementation>/
```

not the complete scope.

A technical PR must never copy every unchanged main case into `pr/N` merely to
make the overlay look complete.

### 5.1 Overlay resolution

For a PR preview, resolve evidence per case:

1. use `pr/N/examples/<case>/...` when that case exists in the PR overlay;
2. otherwise use `main/examples/<case>/...`.

The resulting logical view is complete even though the PR namespace is sparse.

### 5.2 Promotion to main

Promoting affected evidence to `build/main`:

1. starts from the latest complete `build/main`;
2. replaces only verified affected case/implementation directories;
3. removes cases/implementations explicitly deleted from the authoritative
   catalog;
4. preserves every unaffected case;
5. regenerates cross-case derived output from the merged per-case evidence;
6. writes a new schema-validated `build.json`.

A partial affected run never replaces the complete `main/` directory.

## 6. Per-case evidence manifest

`build.json` schema version 2 describes mixed evidence honestly.

Example shape:

```json
{
  "schema_version": 2,
  "scope": "main",
  "generated_at": "...",
  "workflow_run_id": "...",
  "toolchain": {
    "forge_version": "...",
    "solidcraft_version": "...",
    "reference_versions": {}
  },
  "cases": {
    "simple-box": {
      "implementations": {
        "scpf": {
          "source_commit": "...",
          "source_tree": "...",
          "input_hash": "sha256:...",
          "verification_level": "tool_qualification",
          "status": "pass",
          "generated_at": "..."
        },
        "cadquery": {
          "source_commit": "...",
          "input_hash": "sha256:...",
          "verification_level": "reference",
          "status": "pass",
          "generated_at": "..."
        }
      }
    }
  }
}
```

Scope-level metadata may summarize the minimum verification level, but may not
claim that every case was rebuilt on the latest source commit.

The site must reject an unknown manifest schema.

## 7. Case input hashes and dependency map

Affected-case selection is based on deterministic input hashes, not only on
changed-path guesses.

For each case/implementation, the input hash includes:

- that implementation's source;
- its verification contract/expectations;
- hashes of Forge modules declared as dependencies for that case;
- SolidCraft version where applicable;
- reference-library version where applicable;
- relevant generator/runner version.

The repository contains one explicit, tested module/API-to-case dependency map.
A Forge module change therefore changes the input hash of every dependent case.

Changed paths are still used to classify risk and to explain why a case is
affected, but a case is reusable only when its calculated input hash equals the
stored hash in `build/main/build.json`.

Global/unknown dependencies deliberately invalidate all relevant cases.

## 8. Change classification

Classification is implemented once in tested Python. The overall class is the
maximum risk class of all changed inputs.

| Class | Typical inputs | Default action |
| --- | --- | --- |
| presentation | `site/**`, normal docs, CSS, public templates | preflight/site only |
| publication infrastructure | publication scripts/workflows/provenance | preflight + publication contract/tool_verify tests |
| derived | technical report/diagram generators | regenerate derived output only |
| case | case source/contract/reference source | affected cases |
| model-sensitive | geometry/attachment implementation used by mapped cases | model_verify |
| foundational | compiler, replay, runtime/headless core | full target verification stage |
| toolchain | SolidCraft version, Python/toolchain, reference dependency pins | full target verification stage |
| unknown | anything not classified | full target verification stage |

Unknown paths fail safe to the highest class.

Dependency versions must live in versioned repository data/files, not only as
literal package pins hidden in workflow YAML, so classification and hashing can
see them.

## 9. Verification levels

### 9.1 Preflight

Every relevant PR first runs:

- Python compile;
- workflow YAML structural validation;
- publication/layout contract tests;
- site build/test against resolved existing evidence;
- classification and affected-hash calculation.

Expensive work does not start when preflight fails.

### 9.2 Iteration verification

Normal development runs only affected cheap tests/evidence.

A Forge source change with no mapped proving case is an error.

### 9.3 Pre-merge target verification stage

Every PR has one `merge verification` status on the current PR head.

| Risk | Merge gate |
| --- | --- |
| presentation/publication infrastructure | preflight + relevant publication tests |
| derived-only | regenerate/validate derived output |
| ordinary case | tool_verify |
| model-sensitive | model_verify |
| foundational/toolchain/release | tool_qualification |

The merge gate runs **before merge**. Branch protection requires it for the
current head commit and requires the PR to be current with its merge base
(prefer a merge queue; otherwise require the branch to be up to date).

The merge verification result records both PR-head SHA and base SHA. A base change
invalidates the result.

A technical PR is not merged first and qualified afterwards.

Verification jobs use per-PR concurrency with `cancel-in-progress: true`; they
write no generated branches, so cancelling obsolete verification is safe.

### 9.4 Scheduled full safety run

Run the complete registered full native qualification set on `main` on a schedule (initially
weekly) and on manual request.

This is a safety net for an incomplete dependency map or selector bug. It does
not replace the pre-merge verification.

A failing scheduled run:

- never overwrites passing `build/main` evidence with partial/failing output;
- fails visibly and creates/updates an audit finding;
- blocks release promotion until resolved.

## 10. PR evidence and squash-merge promotion

A technical PR may publish a sparse `build/pr/N` **candidate overlay** after
successful iteration verification. Per-case metadata records the achieved level
(for example tool_verify); the preview must show that level honestly.

The pre-merge verification may update/upgrade the same current-head overlay. Evidence is
**promotable** only when every affected case meets the final level required by
the risk classifier.

On squash merge:

1. read the verified PR overlay before cleanup;
2. compare the PR-head tree with the merge-commit tree;
3. when the trees are equal and case input hashes match current `main`, reuse
   the PR evidence;
4. promote affected case directories into `build/main`;
5. regenerate derived cross-case output;
6. publish the stable site;
7. only then remove the PR overlay/preview.

If the trees differ or current input hashes differ, PR evidence is not promoted.
The required verification is rerun for the merge tree before `build/main`
changes.

If that verification fails:

- `build/main` remains unchanged;
- stable Pages remains on the last honest evidence;
- the workflow fails visibly;
- automated reconciliation/audit reports that `main` is ahead of technical
  evidence.

## 11. Pages layout

```text
/
  index.html
  guide/
  reference/
  qualification/
  cheatsheet/
  provenance.json
  ...

previews/
  pr-N/
    ...
    qualification/
    provenance.json
```

Public `qualification/` is required.

It contains HTML/presentation only. It must not contain duplicate technical
files already canonical on `build`.

## 12. Immutable evidence links

Pages never links to mutable URLs such as:

```text
.../blob/build/main/...
```

A site build records the exact `build` branch commit SHA it consumed and emits
permalinks:

```text
https://github.com/<repo>/blob/<build-commit>/main/...
https://raw.githubusercontent.com/<repo>/<build-commit>/main/...
```

A PR overlay and main baseline may both be read from the same immutable build
branch commit; the path determines `pr/N` versus `main`.

Technical publication therefore occurs before the dependent site publication.

`provenance.json` records at least:

- site source commit;
- evidence/source commit(s);
- immutable build branch commit SHA;
- PR number when applicable;
- generated time;
- site schema version.

## 13. Publication protocol: correctness without trusting concurrency queues

GitHub Actions concurrency is an optimization, not the correctness mechanism.

Every generated-branch mutation uses one tested publisher implementing:

1. validate that the candidate source is still current;
2. fetch the latest destination branch head;
3. create a fresh local tree from that exact head;
4. apply only the owned namespace mutation;
5. validate the resulting tree;
6. commit with the fetched head as parent;
7. push normally, never force;
8. on non-fast-forward, fetch and reapply the same pure mutation;
9. retry a bounded number of times;
10. fail visibly if retries are exhausted.

This is compare-and-swap behavior.

### 13.1 Freshness checks

PR publication:

- publish only when candidate source commit equals current PR head.

Stable site publication:

- publish only for current `main` source commit.

Case promotion:

- publish only when the candidate case input hash equals the current main case
  input hash.

Older runs may finish later, but they cannot overwrite newer evidence.

### 13.2 Concurrency groups

Use per-namespace groups to reduce duplicate work, not one global queue:

```text
publish-build-main
publish-build-pr-N
publish-pages-main
publish-pages-pr-N
```

Same-namespace publication uses `cancel-in-progress: false`.

Different namespaces may run concurrently; branch push collisions are handled
by the retry protocol.

This prevents GitHub's one-pending-run behavior from silently discarding work
for unrelated PR namespaces.

## 14. Event matrix

| Event | Verification | Build effect | Pages effect |
| --- | --- | --- | --- |
| presentation-only PR update | preflight | remove stale `pr/N` if PR was previously technical | replace preview using main evidence |
| technical PR update | affected iteration checks; target verification stage when merge-ready | update current-head sparse candidate `pr/N` only after passing checks | replace preview using overlay+main and show achieved level |
| PR reopened | classify current head again | recreate overlay only if technical | recreate preview |
| PR closed, not merged | none | remove `pr/N` | remove preview |
| technical PR merged | the main Forge run reclassifies the exact merge commit and runs the required stable gate | merge a verified sparse main candidate into `build/main` | rebuild stable site after build promotion |
| presentation-only PR merged | validate `build/main` is a complete passing baseline | no technical write | rebuild stable site from build/main |
| verification failure | none published | no partial/stale candidate write; stale PR output may be removed | no new preview; stale PR preview may be removed |
| force-push/rebase | recompute against new base/head | obsolete run rejected by freshness check | obsolete run rejected |
| draft PR | preflight; expensive gate optional until ready | no durable technical publish unless explicitly requested | optional preview |
| fork PR | read-only verification only | no write | no public preview from untrusted code |
| workflow dispatch on main | tool_qualification recovery of exact current main | replace verified `build/main` | rebuild stable site |
| release | full gate | promote main and tag evidence | stable site uses tagged/immutable evidence |

A presentation-only merge may reuse the existing complete passing `build/main`
baseline without recalculating every case input hash. The presentation-only
classifier is the decision boundary: if any technical input changed, this path
must refuse and the normal technical qualification/promotion flow is authoritative.

## 15. Derived output

Cross-case reports and technical diagrams are derived data.

They are regenerated from the resolved per-case evidence when their generator or
inputs change.

This creates a distinct operation:

```text
regenerate-derived
```

It executes no models unless a case input hash also changed.

Derived output is never the authoritative source for per-case status.

## 16. Cleanup and reconciliation

PR close cleanup is useful but not sufficient.

The daily reconcile phase inside the single Forge workflow:

1. reads current open PR numbers;
2. reads `build/pr/*` and `gh-pages/previews/pr-*`;
3. removes namespaces whose PR is no longer open;
4. detects open technical PRs whose stored source is not current head;
5. detects stable site/build provenance drift;
6. applies repairs through the same retrying publisher.

Cleanup is idempotent.

This makes the system self-healing if a close event or publish job is lost.

## 17. Recovery and live audit

Recovery does not expose a menu of CI phases.

A parameterless manual **Forge** run on `main`, or a normal commit changing
`.github/workflows/forge.trigger`, runs tool_qualification on the exact current main
commit and republishes `build/main` plus stable Pages only after success.

Scheduled reconcile remains an internal phase of the same Forge workflow. It
reads the **real** `build` and `gh-pages` branches and checks/repairs scoped
generated namespaces through the retrying publisher.

Namespace identifiers are integers from GitHub PR metadata, never free-form path
strings.

## 18. Pages root control files

Stable Pages assembly treats root control files explicitly.

- `.nojekyll` is generated as part of the site.
- `CNAME`, if this repository ever configures one, is declared in source
  configuration and re-emitted by stable assembly; it is not preserved by
  accident from an old generated branch.
- `previews/` is the only generated subtree preserved from the previous Pages
  branch during a stable-root replacement.

No other stale root file survives merely because it happened to exist before.

## 19. Releases and retention

Release technical evidence is immutable.

After a release passes full qualification, tag the exact build branch commit:

```text
evidence/vX.Y.Z
```

Release/publication metadata refers to that immutable build commit.

Normal publishers never force-push generated branches.

Version 1 retention policy:

- keep generated-branch history intact;
- audit branch/repository size on a schedule;
- do not introduce automatic history rewriting while public Pages permalinks
  depend on build commit SHAs;
- if size becomes unacceptable, first move large binary evidence to a storage
  mechanism with immutable object IDs, then deliberately revise this design.

Do not silently squash generated history and break existing permalinks.

## 20. Reference implementations

Reference implementations are independently hashable inputs.

A reference implementation reruns when:

- its source changes;
- its runner/exporter changes;
- its pinned library version changes;
- a shared contract it proves changes.

A Forge-only case change does not automatically rerun every reference library
unless its reference input hash changes.

## 21. Workflow responsibilities

The repository exposes exactly one active GitHub Actions workflow:
`.github/workflows/scpf.yml` (**Forge**). PR verification, main promotion,
site publication, recovery, cleanup, reconcile, image reuse/build, contract
snapshot and release publication are conditional jobs/phases inside that one
workflow.

A phase is not a reason to create another workflow file. Performance comes from
risk selection, immutable image reuse and selected cases rather than from making
the operator choose between Actions.

Workflow YAML is orchestration only.

Allowed:

- triggers;
- checkout/setup;
- caches;
- invoking repository commands;
- passing GitHub event metadata;
- temporary diagnostic artifact upload.

Policy belongs in tested Python:

- classification;
- input hashing;
- affected-case calculation;
- overlay resolution;
- manifest validation;
- publication freshness;
- namespace mutation/retry;
- promotion;
- cleanup/reconcile;
- live audit.

Forbidden:

- model-specific JSON assertions in YAML;
- large `git diff` policy scripts;
- duplicated branch-layout logic;
- hand-coded cleanup algorithms in workflows.

## 22. Hard invariants

1. `build/main` contains every technically supported qualification case; deliberately blocked documentation cases are represented only on the public site until they become technically supported.
2. `build/pr/N` is sparse and contains only PR-owned changed evidence.
3. A non-affected main case never disappears during affected promotion.
4. Every case/implementation has its own input hash, source provenance and
   verification status.
5. Unknown inputs classify to the safest/highest gate.
6. Public `qualification/` exists.
7. Pages contains no duplicate technical evidence.
8. Every technical link is an immutable build-commit permalink.
9. A stale PR/main run cannot overwrite newer output.
10. A PR mutation cannot touch another PR namespace.
11. Stable Pages replacement preserves all live previews.
12. Site-only work does not execute technical model qualification.
13. Site-only reuse requires a complete passing `build/main` baseline and a
    presentation-only source classification; it does not recalculate every case
    input hash.
14. Technical PR evidence is promoted before merge cleanup removes it.
15. A failed verification never publishes partial technical evidence.
16. Cross-case derived reports are regenerated from resolved per-case evidence.
17. Every generated namespace belongs to stable state or an open PR.
18. Publication correctness does not depend on a GitHub concurrency queue.
19. Fork PR code never receives write-capable publication credentials.
20. Release evidence has an immutable build reference.
21. A merge verification result is invalid when its recorded base SHA is no longer the
    PR's current merge base.
22. Candidate PR evidence is never presented as having a higher verification
    level than it actually achieved.
23. Scheduled full qualification cannot replace passing stable evidence with
    failing/partial output.

## 23. Acceptance scenarios

Implementation is not complete until automated/tool_verify tests demonstrate all
of these.

### A. Presentation-only PR

- affected hashes: none;
- no reference/model execution;
- no `build/pr/N`;
- one preview;
- Qualification HTML uses immutable `build/main` links.

### B. One-case technical PR

- only that case hash changes;
- only that case executes during normal iteration;
- `build/pr/N` contains only that candidate overlay;
- its manifest records the actually achieved verification level;
- preview resolves affected case from PR overlay and all others from main;
- promotion remains blocked until the required target verification stage has passed.

### C. Affected promotion

- promote one case;
- every other main case remains byte-identical;
- complete cross-case derived report is regenerated.

### D. Out-of-order runs

- commit A starts;
- commit B starts;
- B publishes;
- A finishes later;
- A is rejected as stale;
- B remains published.

### E. Three unrelated publications

Start three publications close together for distinct namespaces.

- no namespace mutation is lost because of concurrency pending limits;
- non-fast-forward conflicts retry successfully.

### F. PR technical -> presentation-only

- later commit removes technical change;
- input hashes match main;
- stale `build/pr/N` is removed;
- preview switches to main evidence.

### G. PR close and lost cleanup

- simulate missing close cleanup;
- reconcile removes orphan build/preview scopes.

### H. Presentation-only merge

- no technical model run;
- `build/main` unchanged;
- stable site source advances;
- evidence/build commit remains explicit and immutable.

### I. Technical squash merge

- pre-merge verification passes;
- merge tree equals verified PR tree;
- PR evidence is promoted without rebuilding;
- cleanup occurs after promotion.

### J. Merge tree mismatch

- PR tree differs from merge tree;
- PR evidence is not promoted;
- required verification reruns on merge tree;
- main evidence changes only after pass.

### K. Derived-only change

- no model executes;
- derived reports/diagrams regenerate from existing evidence.

### L. Fork PR

- verification runs read-only;
- no generated branch is written.

### M. Live audit

- inject a stale orphan preview in a fixture/temporary remote;
- audit detects it;
- reconcile produces the expected scoped removal.

## 24. Reviewer checklist

Reject a change if any answer is unclear:

1. What risk class is this change?
2. Which case input hashes change?
3. Which target verification stage is required before merge?
4. Which immutable build commit supplies site evidence?
5. Which exact namespace may be mutated?
6. How is stale/out-of-order publication rejected?
7. How does the publisher recover from non-fast-forward?
8. Can any unaffected case disappear?
9. Does per-case provenance remain truthful after overlay promotion?
10. Are derived outputs regenerated from resolved evidence?
11. Is cleanup recoverable by reconcile?
12. Does the change keep policy out of workflow YAML?
13. Is there an acceptance/contract test for the behavior?

## 25. Implementation order

Implement in this order:

1. schema v2 per-case manifest + overlay semantics;
2. deterministic input hashes + dependency map/classifier;
3. retrying freshness-aware publication library;
4. immutable build-commit links/provenance;
5. pre-merge merge verification and promotion-before-cleanup flow;
6. derived-output regeneration;
7. reconcile/live audit;
8. workflow simplification to orchestration only;
9. retention/size monitoring.

Do not migrate the CAD repository to this pattern until Forge passes the
acceptance scenarios above.

# Generated output and publication design

Status: **normative**

Forge uses the released, pinned `tool.cad.ci` package for generic CI execution,
durable build output and generated-branch publication. Forge does not implement
a second build-store or Git publisher.

## 1. Ownership

Forge owns domain meaning:

- library, example, reference and diagram commands;
- qualification rules and gate policy;
- SolidCraft/runtime image selection;
- interpretation of evidence;
- website content, CSS and qualification presentation.

`tool.cad.ci` owns generic mechanics:

- item discovery from `cad-ci.yml` and item `ci.yml`;
- changed-input selection and dependency ordering;
- ordered step execution and partial step reruns;
- saved step/item state and safe reuse;
- item output under `build/<item source path>/`;
- complete `build/main` plus sparse `build/pr/<number>` scopes;
- partial main updates and overlay resolution;
- safe retrying publication of `build` and `gh-pages`;
- closed-PR generated-output cleanup.

Names such as `example`, `qualification`, `reference-suite` and
`library-test` have no behavior in the generic tool.

## 2. Persistent branches

Forge has three persistent branches:

| Branch | Purpose | Human-edited |
| --- | --- | --- |
| `main` | source, tests and documentation | yes, through PRs |
| `build` | generic generated item output | no |
| `gh-pages` | generated public website | no |

Normal steady state has no extra generated staging branches.

## 3. Item ownership

The source tree defines output ownership. A source folder that owns `ci.yml`
owns the matching generic build directory.

Example:

```text
examples/simple-box/
  ci.yml
  scpf/
  tests/

build/examples/simple-box/
  item.json
  steps/
  case/
    simple-box.json
    stages/
    native/
      simple-box/
        qualification-result.json
        model.sc
        model.step
        model.png
        ...
```

One example is one item. Do not create a nested CI item for
`examples/<case>/tests` because that would overlap the parent output path.

Reference and diagram output have separate owners:

```text
build/qualification/reference_suite/
build/qualification/diagrams/
```

Their meaning remains Forge-specific.

## 4. Step boundaries

An example item has two ordered stages:

1. `integration` — focused Q1/Q2 compatibility evidence plus Forge command
   compilation; no native SolidCraft execution;
2. `native` — resumes the same staged case at native replay, performs native
   checks/renders/mutation/gate, and writes the structured
   `qualification-result.json`.

The PR iteration loop can stop with `--until integration`. A native gate
resumes with `--from native`. The generic runner validates that the earlier
saved step state and declared outputs are still current before resuming.

A partial integration-only run does not write final `item.json`; therefore it
cannot accidentally enter the durable technical build store as a complete item.

## 5. Build branch

The generic `build` branch layout is:

```text
main/
  build.json
  <complete item source path>/...

pr/
  <number>/
    build.json
    <completed affected item source path>/...
```

`main/` is a complete accepted baseline. A PR scope is a sparse overlay.

Normal main updates use `cad-ci build update-main`: copy the current complete
baseline, replace only selected fresh item directories, preserve unrelated item
directories, and write a new complete manifest.

PR previews use `cad-ci build prepare-pr` and `cad-ci build resolve`.

The generic schema-1 `build.json` is the durable technical manifest. Forge may
create an in-memory/local compatibility view for existing site code, but it may
not publish a second domain-specific technical store.

## 6. Pages

Pages layout is:

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
  pr-<number>/
    ...
    provenance.json
```

The stable root is built from resolved generic `build/main`. A PR preview is
built from resolved `main + pr/<number>`.

Pages contains presentation output only. Native files, generated command
documents, measurements and reference evidence stay on `build`; Pages links to
the immutable build-branch commit that supplied them.

## 7. Generic publication protocol

All generated-branch mutations go through the pinned `tool.cad.ci` publisher.

For technical PR output:

1. run selected Forge items;
2. include only complete passing items in the sparse PR candidate;
3. publish `build/pr/<number>`;
4. resolve it over `build/main`;
5. render/test the preview;
6. publish `gh-pages/previews/pr-<number>`.

For main:

1. run the Forge-selected gate;
2. update only complete affected items in the complete generic baseline;
3. publish `build/main`;
4. render/test stable Pages from that exact result;
5. publish the stable Pages root.

The publisher checks source freshness, uses normal pushes, and retries
non-fast-forward races. Generated branches are never force-pushed.

## 8. First generic-store cutover

The previous Forge build branch used a domain-specific schema. The first generic
`build/main` must therefore be created only by a complete passing full gate.

The cutover commit changes `.github/workflows/forge.trigger`. On `main` this
forces full qualification. `cad-ci build prepare-main` then requires every
configured item output to exist and pass before the first generic baseline can
replace the old one.

After that bootstrap, normal main runs use partial `update-main`.

## 9. Truthful PR previews

A cheap integration-only PR has no complete example item and therefore does not
publish new native evidence for that case.

If the same PR previously published a native overlay and a later commit is only
integration-complete, the old PR build overlay is removed before rendering the
new preview.

For changed cases without fresh native evidence, the Forge site adapter masks
the stable native record. The preview must show that native qualification is not
current rather than presenting old main evidence as if it proved the PR change.

Unaffected cases may continue to use accepted main evidence.

## 10. Reference and diagram evidence

Reference comparisons and generated diagrams are ordinary independent CI items.

The `reference-suite` item watches reference implementation sources, pinned
reference dependencies and reference-validation contracts. A Forge-only SCPF
change does not automatically rebuild all external reference implementations.

The `qualification-diagrams` item watches its diagram inputs/generator.

Forge gate policy decides when these items are required. The generic tool only
executes/stores them.

## 11. Provenance and links

Each completed example item contains its own structured
`qualification-result.json`. The public site interprets that file from the
resolved generic item output.

Public evidence links use the immutable build branch commit and the physical
generic item path. For example:

```text
<build-commit>/main/examples/simple-box/case/native/simple-box/model.png
<build-commit>/main/examples/simple-box/case/simple-box.json
<build-commit>/main/qualification/reference_suite/references/...
```

A PR-resolved view may link some item evidence to `pr/<number>` and unaffected
items to `main`. Forge's site adapter records that per-item build scope.

`provenance.json` records the site source commit, build commit and preview/stable
stage.

## 12. Presentation-only changes

Presentation-only work does not execute native qualification and does not create
new technical PR item output.

Its Pages preview uses the accepted generic main baseline. Technical changes are
never allowed onto this reuse path.

On main, a presentation-only change can rebuild stable Pages while leaving the
generic technical baseline unchanged.

## 13. Cleanup and recovery

Closing a PR removes:

- `build/pr/<number>`;
- `gh-pages/previews/pr-<number>/`.

Cleanup uses `cad-ci publish build-cleanup` and
`cad-ci publish pages-cleanup`.

The existing Forge reconcile operation remains responsible for detecting lost
cleanup/orphan namespaces, but any mutation must use the same generic publisher.

A manual Forge run on `main`, or a deliberate change to
`.github/workflows/forge.trigger`, performs the repository-defined recovery
gate. The operator does not select internal qualification stages.

## 14. Hard invariants

1. `tool.cad.ci` contains no Forge qualification semantics.
2. Every generated file has one non-overlapping consumer item owner.
3. `build/main` is a complete accepted generic item baseline.
4. `build/pr/N` is sparse.
5. A partial main update cannot delete unrelated items.
6. A partial integration-only item is not durable native evidence.
7. A changed PR case never displays stale main native evidence as current.
8. Pages contains presentation output only.
9. Technical evidence links identify an immutable build commit.
10. Generated branches are never force-pushed.
11. A stale source run cannot overwrite newer generated output.
12. Fork PR code never receives write-capable publication credentials.
13. Failing/incomplete item output is never published as accepted technical
    evidence.
14. The first generic baseline is created only by a full passing gate.
15. GitHub Actions YAML contains setup/orchestration, not item/build policy.

## 15. Acceptance scenarios

### Presentation-only PR

- no native item runs;
- no completed technical PR item is published;
- preview renders from generic main evidence.

### Cheap one-case PR

- library tests and that example's integration step run;
- the example has no final `item.json`;
- no new native overlay for that case is published;
- preview does not claim stale main native evidence for the changed case.

### Native one-case PR

- integration state is validated/reused;
- native resumes the same item;
- only that completed example item enters `build/pr/N`;
- preview resolves that item from PR and unaffected items from main.

### Main technical update

- affected items finish completely;
- `update-main` replaces those item directories only;
- unrelated item directories remain intact;
- stable Pages is rendered from the resulting complete baseline.

### Full recovery

- every configured required item is complete;
- `prepare-main` can construct a complete baseline from scratch;
- stable Pages passes native/reference validation before publication.

### Out-of-order publication

- newer source publishes first;
- older source finishes later;
- source-freshness checks reject the older mutation.

### PR close

- only that PR's build overlay and Pages preview are removed.

## 16. Reviewer checklist

Before merging CI/publication work, verify:

1. Is domain meaning still in Forge rather than `tool.cad.ci`?
2. Does every output have exactly one item owner?
3. Can a partial step result be mistaken for a complete item?
4. Which completed item IDs may enter durable output?
5. Does a cheap PR avoid claiming stale native evidence?
6. Does main update preserve unrelated item output?
7. Are public links built from the physical generic item paths?
8. Are build and Pages writes using the generic retrying publisher?
9. Is first-cutover/bootstrap behavior fail-safe?
10. Are these rules covered by focused tests?

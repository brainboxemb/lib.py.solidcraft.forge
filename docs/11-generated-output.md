# Generated output architecture

Forge uses four branch roles. Their names describe ownership, not a stage in a
workflow.

| Branch | Owns |
| --- | --- |
| `main` | Editable source and documentation |
| PR branch | One proposed source change |
| `build` | Generated technical build/qualification output |
| `gh-pages` | Generated browseable website |

There are no `preview-output` or `qualified-output` stages in this model.

## Build branch

The root of `build` is split by source scope:

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

The persistent path follows the source item. A CadQuery reference source at
`examples/simple-box/cadquery/model.py` therefore has generated files under
`examples/simple-box/cadquery/`. Native output created from
`examples/simple-box/scpf/model.py` belongs under
`examples/simple-box/scpf/`.

Workflow-local directories such as `output/native` and
`output/references` are implementation details. They are normalized before
publication and must not become top-level directories on `build`.

Cross-case summaries, qualification reports and technical diagrams belong under
`qualification/`.

## Pages branch

The stable main website occupies the root of `gh-pages`. Each open PR owns
exactly one preview:

Qualification evidence is not a website subtree. `gh-pages/qualification/`
must not exist; that material belongs on the `build` branch.

```text
/
previews/
  pr-<number>/
```

Updating a PR replaces that same preview. It does not create fast/full variants
or a branch-name preview. Closing the PR removes the preview.

A stable-site replacement preserves the complete `previews/` subtree.

## Publication rules

A PR build may replace only `build/pr/<number>/`. A PR preview may replace
only `gh-pages/previews/pr-<number>/`.

A successful full Q1-Q6 run on `main` replaces `build/main/` and may replace
the stable Pages root. Site-only publication may reuse previously qualified
technical evidence, but it still replaces only the stable Pages root and
preserves PR previews.

Every technical build contains `build.json`. Every website contains
`provenance.json`. Publication verifies the source commit before writing the
generated branch.

The workflow is orchestration only. The mapping from intermediate files to the
persistent build tree, stable Pages assembly and PR cleanup are implemented in
`scripts/generated_output.py` and covered by qualification-tooling tests.

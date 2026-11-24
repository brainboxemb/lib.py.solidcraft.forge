# SCPF library owner

`cadlib/` owns the public Forge Python package. The distribution and import name remain `scpf`.

The current source was migrated from the released Forge 0.15.0 package into the template-native layout:

```text
cadlib/
  pyproject.toml
  src/scpf/
  tests/
```

Run owner tests through repository CI rather than installing a second copy of the package. Package qualification builds a wheel from an isolated source copy; it is not a release.

The first bootstrap intentionally migrates package-focused tests only. CI/release/site/model-batch tests from the old repository are not library tests and must move to the capability that owns them, or disappear when the template already provides equivalent behavior.

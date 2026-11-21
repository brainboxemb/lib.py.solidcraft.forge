# Forge examples

The `examples/` tree contains several deliberately different repository roles.

A current full model Verification case owns all of:

```text
examples/<slug>/
  ci.yml
  model.yml
  README.md
  scpf/model.py
  verification/verify.py
  build123d/{ci.yml,model.py}
  cadquery/{ci.yml,model.py}
  pybosl2/{ci.yml,model.py}
  pythonscad/{ci.yml,model.py}
```

Those cases are discovered from their local files; there is no central
executable model-case registry.

Any other top-level directory below `examples/` must contain `role.yml`.
That file makes the exception explicit and records why the directory still
exists, who currently owns it, and the current keep/promote/retire decision.

Supported exception roles are:

- `release-verification` — fixture owned by Forge package release verification;
- `regression-fixture` — focused source fixture whose behavior is owned by a
  current executing test outside the full model-verification catalog. This also
  covers deliberately non-native Q1/Q2 fixtures such as `model_authoring`.

Temporary migration candidates and unowned legacy samples are not permanent
roles. They must be promoted, explicitly superseded, or retired before the
reconciliation issue closes.

The historical lineage of the current 32-case catalog and every current
exception is recorded in `docs/background/example-history.md`.

Do not create a new directory under `examples/` without either the complete
Verification contract or an explicit local role.

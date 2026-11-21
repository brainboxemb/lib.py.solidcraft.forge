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

- `verification-candidate` — historical or requested model case that still
  needs an explicit full Verification migration;
- `release-verification` — fixture owned by Forge package release verification;
- `regression-fixture` — focused source fixture whose behavior is owned by a
  current test outside the full model-verification catalog;
- `legacy-sample` — old sample retained only while an explicit
  modernize/retire decision is pending.

The historical lineage of the current 32-case catalog and every current
exception is recorded in `docs/background/example-history.md`.

Do not create a new directory under `examples/` without either the complete
Verification contract or an explicit local role.

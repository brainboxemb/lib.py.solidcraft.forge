# Mitcad version references

Forge keeps version-pinned Mitcad backend evidence below this directory.

The first target is [0.70.0](0.70.0/SOURCE.md). Its `commands.md` is the
exact upstream release command reference, not a hand-selected subset.

When a qualified `mitcad-cli` is available, capture the live MCP catalog:

```sh
PYTHONPATH=modules/mitcad-reference/src \
python -m cad_library_mitcad_reference capture \
  --mitcad-cli /absolute/path/to/mitcad-cli
```

That capture reads both:
- `mitcad://reference/commands`, the runtime-filtered native reference whose
  blob identity is pinned separately from the complete upstream source;
- `model_reference {}` for the machine-readable commands, queries, feature
  types and JSON-schema catalogue.

Verify the source snapshot without a CLI:

```sh
PYTHONPATH=modules/mitcad-reference/src \
python -m cad_library_mitcad_reference verify
```

Pass `--mitcad-cli` to additionally require the runtime reference and
machine catalog to match. Version directories are immutable evidence.

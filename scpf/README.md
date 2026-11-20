# SCPF package

`scpf` is the Python authoring package for SolidCraft Forge. It expresses
parametric modelling intent in Python and lowers that intent to native
SolidCraft commands.

## Install for development

From the repository root:

```powershell
python -m pip install -e ./scpf
```

Run the package unit tests:

```powershell
python -m unittest discover -s scpf/tests -v
```

## Run a model

Compile a trusted model to native command JSON:

```powershell
python -m scpf path/to/model.py --out output/model.json
```

With SolidCraft open and Assistant access enabled, apply the model to the active
design:

```powershell
python -m scpf path/to/model.py --connect
```

Real product models live in
[2026-011-02.cad.solidcraft](https://github.com/brainboxemb/2026-011-02.cad.solidcraft).
This library repository keeps reusable API/compiler code and focused
verification fixtures.

## Documentation

Do not treat this package README as a second API specification.

- [Forge API](../docs/api.md) — current cross-object public semantics.
- [Forge design](../docs/design.md) — repository-wide architecture.
- [Forge development](../docs/development.md) — working on this repository.
- [Forge manual](../docs/manual/README.md) — task-oriented guidance.
- [Forge requirements](../docs/requirements.md) — stable repository requirements.
- [Forge release](../docs/release.md) — release/version rules.

Exact public names, signatures, defaults and enum members come from the Python
implementation and its docstrings. The generated API reference and
`docs/agent/forge-api.json` are derived from those sources.

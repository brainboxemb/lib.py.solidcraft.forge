# Abstract model-authoring fixture

This fixture is intentionally not a product model. It exists to prove the
basic modelling boundary that failed during downstream Simple MFT work.

The fixture contains:

- one `Plate` component with one explicitly published CAD parameter;
- fixed UPPER_CASE dimensions that remain Python constants;
- one root `_plate_y` build-time value;
- one reusable `Block` component and one copied occurrence;
- two materials assigned inside their own component definitions;
- an `Assembly` made from three physical occurrences.

It deliberately does not contain MFT dimensions, hole patterns, anchors or
product-specific geometry. Those belong in the CAD model repository.

The Q1/Q2 contract is:

1. `python -m scpf check examples/model_authoring/scpf/model.py` passes;
2. only the selected `Plate.length` becomes a native CAD parameter;
3. Birch and Steel are separate native material definitions;
4. the Block is reused with `occurrence.copy`;
5. physical parts are composed as an Assembly, not as material-assigned Shapes.

Native Q3-Q6 evidence may be added when it answers a separate native question;
it is not required to prove this fail-fast authoring workflow.

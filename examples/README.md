# Examples

Each example is an independent owner. It keeps model-specific source and expectations together while generic builder and verification mechanics stay in modules.

A typical example declares:

```yaml
schema: 1
id: simple-box
kind: example
builder: builder-cadquery
source: cadquery/model.py
verification:
  module: verification
  adapter: mesh-geometry
  definition: verification/geometry.json
preview:
  module: preview
  adapter: mesh
```

`model.yml` owns presentation metadata. Use `purpose: example` or `purpose: [example, verification]` for a public example. Use `purpose: verification` for a CI fixture that must not enter the public catalogue.

Examples may declare `needs: [cadlib]` or normal module ids. A change to a declared dependency selects the example on `dev`.

Builders declare their execution runtime. The verifier and preview capabilities declare their own runtime. This allows SolidCraft to build in the light SolidCraft image and the resulting STL to be verified in the reference image without adding engine-specific orchestration.

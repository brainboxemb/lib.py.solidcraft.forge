# CAD preview module

The deterministic reference STL renderer is adapted from the existing Forge verification/reference_preview.py implementation. It consumes an actual verified mesh, uses the local cad_verification camera helpers, and writes model.png and preview.json. It does not change the geometry verification status or rebuild models. The example declares its preview adapter explicitly. Reference rendering runs in the existing reference runtime; native SolidCraft preview is a subsequent adapter. Pages only reads the durable files.

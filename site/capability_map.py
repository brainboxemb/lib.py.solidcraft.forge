"""Curated CAD capability map for completeness analysis.

The map is intentionally capability-based, not a mirror of SolidCraft's
hundreds of individual commands.
"""

CAPABILITY_GROUPS = [
    ("fundamentals", "1 · Geometry fundamentals"),
    ("sketches", "2 · Sketches and parametric profiles"),
    ("features", "3 · Part features and face references"),
    ("components", "4 · Components, occurrences and relationships"),
    ("advanced", "5 · Advanced modelling"),
    ("inspection", "6 · Inspection and exchange"),
]

SOLIDCRAFT_CAPABILITIES = [
    # group, capability, SolidCraft capability, Forge status, Forge today,
    # priority/target, reference model, note
    ("fundamentals", "Box", "Native box primitive.", "Supported", "Q6 · native-qualified in the current Forge subset.", "Core", "PythonSCAD + OpenSCAD", "Core rectangular solid."),
    ("fundamentals", "Cylinder", "Native cylinder primitive, including principal-axis support.", "Supported", "Q6 · principal-axis Cylinder behaviour is qualified through the shared primitive matrix and native primitive-csg case.", "Core", "PythonSCAD + OpenSCAD", "Arbitrary non-principal rotation remains a separate transform capability."),
    ("fundamentals", "Sphere", "Native sphere primitive.", "Supported", "Q6 · native-qualified through primitive CSG.", "Core", "PythonSCAD + OpenSCAD", "Core rounded primitive."),
    ("fundamentals", "Cone", "Native cone / frustum primitive.", "Partial", "Q2 · public Cone semantics and native command lowering are covered; a dedicated Q6 visual case is still missing.", "Later Q6", "PythonSCAD + OpenSCAD", "Keep it in the shared primitive contract matrix; add native visual coverage when a real model needs it."),
    ("fundamentals", "Torus", "Native torus primitive.", "Missing", "Not exposed in Forge.", "Later", "PythonSCAD + OpenSCAD", "Useful breadth, not needed for current frame work."),
    ("fundamentals", "Boolean join / cut / intersect", "Native solid operations.", "Supported", "Q6", "Core", "PythonSCAD + OpenSCAD", "Operator syntax is a good fit."),
    ("fundamentals", "Translation", "Native primitive positions and occurrence moves.", "Supported", "Primitive translation plus replay-bound numeric and parameter-driven occurrence moves are verified.", "Core", "PythonSCAD + OpenSCAD", "Keep world movement distinct from local attachment offsets."),
    ("fundamentals", "General rotation / mirror / scale", "Occurrence rotation is native; SolidCraft has richer placement machinery.", "Partial", "Rotation is partial; mirror and scale remain gaps.", "Core rotation; mirror/scale later", "PythonSCAD + OpenSCAD", "Prefer one general transform model over type-specific shortcuts."),

    ("sketches", "Lines / rectangles / circles / polygons / text", "Rich native sketch entities.", "Partial", "Forge exposes only a useful subset today.", "Core", "PythonSCAD + OpenSCAD", "Broaden from real modelling use cases."),
    ("sketches", "Sketch constraints", "Native geometric constraints.", "Missing", "Very limited/no public Forge constraint API.", "High", "SolidCraft", "Needed for genuinely editable sketches."),
    ("sketches", "Sketch dimensions and expressions", "Native dimensions and parameter expressions.", "Partial", "Expression support exists, but the full sketch-dimension surface is not exposed.", "High", "SolidCraft", "Needed for a mature parametric API."),
    ("sketches", "Face workplanes / projections", "Native sketches can live on faces and reference/project geometry.", "Partial", "Face-based placement exists; projection/reference breadth is incomplete.", "High", "SolidCraft", "Central to feature construction."),

    ("features", "Extrude", "Native new/join/cut/intersect, symmetric, two-sided and to/from-object extents.", "Partial", "Q6 basic subset.", "Core", "PythonSCAD/OpenSCAD + SolidCraft richness", "Expose advanced extents only from real use cases."),
    ("features", "Hole", "Native direction, through/to, countersink/counterbore, threads and edge references.", "Partial", "Partial Q6 through-hole support.", "Core", "SolidCraft", "Grow from user scenarios instead of wrapping every option at once."),
    ("features", "Fillet / chamfer / shell", "Native topology-based feature operations.", "Partial", "Basic Edges.VERTICAL fillet is Q6-qualified; chamfer, shell and richer edge-selection modes still have native gaps.", "High", "PythonSCAD", "Important mechanical/workshop operations."),
    ("features", "Patterns", "Native solid and sketch rectangular/circular patterns.", "Partial", "Hole pattern subset is available.", "High", "PythonSCAD + OpenSCAD", "General pattern API remains a gap."),
    ("features", "Materials / appearance", "Native material and appearance support.", "Partial", "Material assignment exists; appearance breadth is incomplete.", "Useful", "PythonSCAD", "Important for readable assemblies, not core geometry."),

    ("components", "Components and repeated occurrences", "Native component definitions and occurrence copies.", "Supported", "Q6 basic reusable-definition/copy path.", "Core", "PythonSCAD objects + SolidCraft components", "One definition, many physical placements."),
    ("components", "Component-local parameters and inherited expressions", "Native user parameters and expressions can drive reusable component geometry.", "Supported", "Q5 · implicit parameters, inherited expressions and parent-derived child dimensions verified through saved-design mutation.", "Core", "PythonSCAD + SolidCraft", "Public defaults are implicit editable parameters; inherited expressions reuse the parent dependency."),
    ("components", "Occurrence local/world placement", "Native local/world translation, axis-angle and matrices.", "Partial", "Numeric, symbolic and rotated-copy Placement paths are native-verified through replay-bound occurrence IDs; the full transform surface is not exposed.", "Core", "PythonSCAD + OpenSCAD", "Forge should expose a smaller coherent transform API."),
    ("components", "Parent/child relation via a face", "Native face/topology references can remain associative.", "Supported", "Q5 for standard face/corner anchors.", "Core", "SolidCraft + BOSL2", "Saved-design parent size mutations are qualified for standard face/corner relationships."),
    ("components", "Local attachment frame / joint origin", "Native face, circle, edge, corner, point, plane or axis origins plus orientation.", "Partial", "Standard corners, child AnchorFrame and direct AnchorTopology edge/on/corner picks are qualified; explicitly rotated AnchorTopology occurrences remain a gap.", "Core", "BOSL2", "Topology-backed local frames follow saved-design parent mutations; richer origin types remain incomplete."),
    ("components", "Rigid / planar relationships", "Native persistent component relationships and editable values.", "Partial", "Rigid and planar relationships have native Verification coverage; as-built rigid now has a dedicated preserved-pose geometry case. Broader relationship types remain incomplete.", "Needed after basic parent/child placement", "BOSL2 conceptually; SolidCraft technically", "Keep joint terminology in the advanced/native layer."),
    ("components", "Motion joints / limits / kinematics", "Native degrees of freedom, limits and motion solving.", "Missing", "Not exposed in Forge.", "Later", "SolidCraft", "Not needed for current static assemblies."),

    ("advanced", "Revolve", "Native parametric revolve.", "Missing", "Not exposed in Forge.", "High", "PythonSCAD + OpenSCAD", "Common mechanical modelling operation."),
    ("advanced", "Sweep", "Native sweep with path orientation, twist, scale and rails.", "Missing", "Not exposed in Forge.", "Later", "PythonSCAD + OpenSCAD", "Useful, not a prerequisite for current projects."),
    ("advanced", "Loft", "Native multi-section loft with optional rails.", "Partial", "Internal/special-case use only.", "Later", "PythonSCAD + OpenSCAD", "Expose only when a real scenario needs it."),
    ("advanced", "Threads / emboss / sheet metal", "Native specialized features exist.", "Partial", "ThreadedHole is Q6-qualified. The first sheet-metal subset is Q6-qualified through Sketch.sheet_metal() + Shape.fold(); emboss and broader sheet operations remain missing.", "Expand only from real model needs", "SolidCraft + build123d reference", "Keep the public API small; add sheet operations only when a qualification case proves the workflow."),

    ("inspection", "Measurements / topology / interference", "Native inspection and topology queries are extensive.", "Partial", "Used heavily by qualification; little is public modelling API.", "High for verification", "SolidCraft", "Qualification should consume this even if the modelling API stays small."),
    ("inspection", "Import / export / linked components", "Native exchange and component-linking workflows.", "Partial", "Available mainly through CLI/project workflow.", "Later", "SolidCraft", "Separate workflow capability from modelling API."),
]
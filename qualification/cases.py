"""Qualification case metadata for the Forge library site.

Keep this deliberately explicit.  A qualification case is documentation of a
contract between the public Forge API, Forge's compiler model and native
SolidCraft behaviour.  The site and site tests both consume this table.
"""

from scpf.version import TESTED_SOLIDCRAFT_VERSION

REFERENCE_URLS = {
    "SolidCraft": "https://docs.solidcraft.io/guide/assemblies.html",
    "BOSL2": "https://github.com/BelfrySCAD/BOSL2/wiki/Tutorial-Attachment-Overview",
    "OpenSCAD": "https://openscad.org/documentation.html",
    "PythonSCAD": "https://github.com/pythonscad/pythonscad",
    "CadQuery": "https://cadquery.readthedocs.io/",
}

DEFAULT_REFERENCE_IMPLEMENTATIONS = ("pythonscad", "pybosl2", "cadquery")
REFERENCE_IMPLEMENTATION_LABELS = {
    "pythonscad": "PythonSCAD",
    "pybosl2": "pyBOSL2",
    "cadquery": "CadQuery",
}


def reference_implementations_for(case: dict) -> tuple[str, ...]:
    """Return required references after explicit technical exceptions."""

    if "reference_implementations" in case:
        raise ValueError(
            f"{case['slug']}: reference_implementations is obsolete; "
            "use reference_exceptions only for documented technical exceptions"
        )

    exceptions = case.get("reference_exceptions", {})
    unknown = set(exceptions) - set(DEFAULT_REFERENCE_IMPLEMENTATIONS)
    if unknown:
        raise ValueError(
            f"{case['slug']}: unknown reference exceptions: "
            + ", ".join(sorted(unknown))
        )
    for name, reason in exceptions.items():
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(
                f"{case['slug']}: reference exception {name!r} needs a reason"
            )

    return tuple(
        name
        for name in DEFAULT_REFERENCE_IMPLEMENTATIONS
        if name not in exceptions
    )


QUALIFICATION_LEVELS = [
    ("Q1", "Python API", "Public API validation, symbolic values and compiler invariants."),
    ("Q2", "Command contract", "Generated SolidCraft command JSON is complete and inspectable."),
    ("Q3", "Native build", f"SolidCraft {TESTED_SOLIDCRAFT_VERSION} accepts the command plan and saves an editable design."),
    ("Q4", "Native measurement", "Timeline and actual body measurements match the expected result."),
    ("Q5", "Parametric mutation", "A saved design re-solves correctly after parameters.change."),
    ("Q6", "Visual regression", "Fixed-camera native renders are checked from multiple views and published with reference/diff evidence."),
]


QUALIFICATION_GROUPS = [
    ("fundamentals", "1 · Basic geometry", "Primitives, profiles, CSG and simple reusable reference geometry."),
    ("features", "2 · Parent/child features and faces", "Features that belong to an existing object and use a meaningful parent face."),
    ("parameters", "3 · Parameters and dependencies", "Editable values, component-local parameters and inherited symbolic dependencies."),
    ("components", "4 · Components and occurrences", "Reusable physical parts and more than one placed occurrence."),
    ("anchors", "5 · Anchors and local frames", "Richer component references: faces, corners, topology and oriented local frames."),
    ("associativity", "6 · Associative relationships", "Editable distances and local offsets that must keep their meaning after parameter changes."),
]


QUALIFICATION_CASES = [
    {
        "slug": "simple-box",
        "group": "fundamentals",
        "title": "Parameterized Box",
        "intent": "Establish the smallest model/parameter contract: three public Python fields create one editable native box.",
        "forge_api": "class fields -> Parameter; Box(length, width, height); build()",
        "forge_model": "One root Shape with symbolic length, width and height; no occurrence or assembly layer.",
        "lowering": "parameters.add for the public dimensions, followed directly by native solid.box; no sketch is synthesized.",
        "native_expectation": "One rectangular solid with the requested 40 x 30 x 10 mm dimensions and an error-free timeline.",
        "mutation": "Not required in this fixture; parameter-expression preservation is covered by focused Q1 tests and more specific native mutation cases.",
        "references": [
            ("OpenSCAD", "cube([40,30,10]) is the constructive-geometry baseline; Forge differs by preserving editable SolidCraft history."),
        ],
    },
    {
        "slug": "anchored-holes",
        "group": "features",
        "title": "Face-relative hole pattern",
        "intent": "Verify a 2D profile, native extrusion, patterned holes and placement on a selected face.",
        "forge_api": "with Sketch(plane='XY'): Rectangle2D(...); sketch.extrude(...); Hole(...).pattern(...).on(..., face=Faces.TOP)",
        "forge_model": "A feature-based plate plus a patterned Hole feature anchored to the plate's TOP face.",
        "lowering": "Native sketch/extrude commands followed by native hole/pattern placement commands; Forge does not subtract hand-built cylinders.",
        "native_expectation": "One plate with two through holes at the requested Y spacing and no feature errors.",
        "mutation": "No saved-design mutation in this fixture; geometry and feature placement are measured at Q4.",
        "references": [
            ("OpenSCAD", "Comparable geometry would normally use difference() and repeated cylinders; Forge intentionally prefers SolidCraft hole features."),
        ],
    },
    {
        "slug": "parameter-scope",
        "q5_required": True,
        "group": "parameters",
        "title": "Explicit component parameters and shared dependencies",
        "intent": "Verify that reusable component defaults stay fixed unless explicitly included, while selected defaults become native parameters and parent Parameters/Expressions are reused rather than duplicated in the child.",
        "forge_api": "@component(include=('width',)) class Panel; Panel(width=self.shared_width); Panel(width=half(self.shared_width))",
        "forge_model": "Only explicitly included width defaults become component-local Parameters. The lower-case depth default remains fixed. Inherited Parameter/Expression inputs become external bindings to the existing parent dependency.",
        "lowering": "Explicitly included component parameters are namespaced (for example Panel_width); unincluded child defaults stay fixed; inherited names such as shared_width remain unprefixed and are emitted once even when several child definitions use them.",
        "native_expectation": "The saved SolidCraft design exposes Panel_width, Panel_2_width and shared_width; changing shared_width updates both directly-bound children and the derived half-width child without rerunning Python.",
        "mutation": "Change shared_width from 80 to 100 mm in the saved native design; widths must change from [40,40,60,80,80] to [40,50,60,100,100].",
        "references": [
            ("PythonSCAD", "Reference geometry remains ordinary Python; Forge adds explicit native parameter publication because that is persistence/editability intent rather than geometry syntax."),
            ("SolidCraft", "Native parameters and expressions are the source of truth for saved-design editability and rebuild behaviour."),
        ],
    },
    {
        "slug": "parent-derived-child-size",
        "q5_required": True,
        "group": "parameters",
        "title": "Child dimensions derived from parent parameters",
        "intent": "Isolate one dependency contract: a reusable child receives width and depth expressions derived from parent parameters, and those child dimensions remain editable/associative in the saved SolidCraft design.",
        "forge_api": "DerivedChild(width=self.base_width / 2, depth=self.base_depth / 2)",
        "forge_model": "One ParentBlock and one DerivedChild. Only base_width and base_depth are published as document parameters; the child carries expressions that reference those existing parent parameters instead of receiving independent duplicated values.",
        "lowering": "The parent and child sketch dimensions preserve base_width/base_depth expressions. Forge must not flatten base_width / 2 or base_depth / 2 to numeric constants when compiling the child component.",
        "native_expectation": "At 120x80 mm parent size, the child measures 60x40 mm. Its fixed height and fixed body layout are deliberately unrelated to this qualification.",
        "mutation": "Change base_width/base_depth from 120x80 to 160x120 mm in the saved .sc design; without rerunning Python the child must rebuild from 60x40 to 80x60 mm.",
        "references": [
            ("SolidCraft", "Native parameters and expressions must preserve the parent-to-child dimensional dependency after the Python compiler has finished."),
            ("PythonSCAD", "The Python model expresses the dependency with ordinary arithmetic rather than a special application-specific sizing API."),
        ],
    },
    {
        "slug": "components",
        "group": "components",
        "title": "Reuse one component definition in two placements",
        "intent": "Verify that one reusable component definition can have two occurrences with ordinary Placement and no attachment relationship.",
        "forge_api": "left = Block(); right = left.copy(placement=Placement(x=Block.length))",
        "forge_model": "Two ModelInstance occurrences share one ModelDefinition. The second occurrence carries only Placement metadata; neither occurrence carries an Attachment.",
        "lowering": "Forge creates one Block component definition and one occurrence.copy with translate=[40,0,0]. No joint.create and no later occurrence.move are needed.",
        "native_expectation": "Two identical blocks touch face-to-face at X=20 while retaining one shared editable component definition.",
        "mutation": "No mutation in this base case; parameter-driven Placement is qualified separately.",
        "references": [
            ("SolidCraft", "One component definition may be placed more than once; this case qualifies that basic component/occurrence structure without introducing a joint."),
        ],
    },
    {
        "slug": "assembly-decorator",
        "group": "components",
        "title": "Imported @assembly subassembly",
        "intent": "Verify the public @assembly decorator on an imported reusable subassembly, independently of anchor or feature complexity.",
        "forge_api": "@component class Post; @assembly class PostPair; root model imports and returns PostPair()",
        "forge_model": "One reusable Post component definition plus two occurrences produced inside an imported @assembly factory. The root model treats the returned subassembly as ordinary assembly geometry.",
        "lowering": "The Python-only @assembly wrapper disappears during lowering: Forge emits one Post component definition and one copied occurrence placed directly by occurrence.copy; no occurrence.move is needed.",
        "native_expectation": "Two identical 10 x 10 x 20 mm posts remain at X=-15 and X=+15 while the imported @assembly result builds from a replay-safe component/copy command plan.",
        "mutation": "No saved-design mutation in this fixture; it isolates imported @assembly construction and native lowering.",
        "references": [
            ("PythonSCAD", "The public Python object/decorator layer should remain natural while still producing reusable native CAD structure."),
            ("SolidCraft", "The resulting assembly must lower to native component/occurrence commands and build without special runtime handling."),
        ],
    },
    {
        "slug": "group-hierarchy",
        "group": "components",
        "title": "Named native subassembly group",
        "intent": "Verify that group(name) creates a real nested native component rather than a Python-only label.",
        "forge_api": "(left + right).group('PanelGroup'); group + Frame()",
        "forge_model": "Two Panel occurrences share one definition under a named PanelGroup component, while Frame remains a direct root child.",
        "lowering": "Forge emits component.create(name='PanelGroup'), creates Panel with parent='PanelGroup', copies its occurrence, and creates Frame at the design root.",
        "native_expectation": "Two 10 x 2 x 20 mm panels remain nested under PanelGroup and one 35 x 10 x 40 mm frame remains at root; native BOM inspection must preserve that hierarchy.",
        "mutation": "No saved-design mutation in this fixture; it isolates persisted native grouping and hierarchy.",
        "references": [
            ("SolidCraft", "Native components form a tree; top-level BOM inspection exposes direct children while flat BOM inspection expands subassemblies."),
            ("PythonSCAD", "Python-side composition should lower to inspectable native CAD structure rather than remain a transient wrapper."),
        ],
    },
    {
        "slug": "attach-angle",
        "group": "associativity",
        "title": "Native attachment clocking angle",
        "intent": "Verify that attach(angle=...) remains a native rigid-joint turn rather than being pre-baked into child geometry or an occurrence rotation.",
        "forge_api": "Arm().attach(base, parent=Anchor.TOP, child=Anchor.BOTTOM, angle=90)",
        "forge_model": "One square Base and one non-square 30x10 Arm. The child definition stays neutral; only the attachment carries the quarter-turn.",
        "lowering": "joint.create(type='rigid', angle=90) is the only authored clocking relationship. Forge does not rotate the Arm occurrence separately.",
        "native_expectation": "The Arm sits on the Base TOP face and its 30x10 footprint is quarter-turned to 10x30 in world XY.",
        "mutation": "Not required; this case isolates native orientation/clocking and is qualified by measured bounds plus fixed-camera visual regression.",
        "references": [
            ("SolidCraft", "The joint angle is the persisted native relationship value that clocks the child about the attachment normal."),
            ("BOSL2", "Conceptually comparable to spin/clocking around an attachment normal, while the child geometry remains reusable and neutral."),
        ],
    },
    {
        "slug": "parametric-attach",
        "q5_required": True,
        "group": "associativity",
        "title": "Editable distance between attached components",
        "intent": "Verify that distance along the attachment normal remains a native editable joint parameter.",
        "forge_api": "attach(..., gap=self.gap)",
        "forge_model": "Rigid Attachment with a symbolic gap expression; anchor identities are unchanged.",
        "lowering": "joint.create(type='rigid', offset='gap'); gap is not flattened into occurrence.move.",
        "native_expectation": "The child sits 10 mm away from the parent's RIGHT face along the joint normal.",
        "mutation": "Change gap from 10 to 30 mm in the saved .sc design; the child must move another 20 mm without rerunning Python.",
        "references": [
            ("BOSL2", "Conceptually similar to an attachment displacement along the local anchor normal rather than a world-axis translate."),
        ],
    },
    {
        "slug": "parametric-offset",
        "q5_required": True,
        "group": "associativity",
        "title": "Editable local offset at an attachment",
        "intent": "Verify the existing local (u,v) attachment-plane offset and make its coordinate semantics explicit.",
        "forge_api": "attach(..., offset=(u, v))",
        "forge_model": "Attachment stores two symbolic local planar values; these are not world X/Y/Z coordinates.",
        "lowering": "A non-zero/symbolic local offset becomes joint.create(type='planar', values=[u,v,angle]).",
        "native_expectation": "The marker moves within the selected corner anchor's local attachment plane.",
        "mutation": "Change shift from 5 to 10 mm in the saved design; the marker must follow the same local axis by another 5 mm.",
        "references": [
            ("BOSL2", "Important reference: attach() operates in the local coordinate system at the parent anchor, not blindly in world coordinates."),
            ("OpenSCAD", "A raw translate([x,y,z]) is world/object transform syntax and therefore is not equivalent to this local joint offset."),
        ],
    },
    {
        "slug": "parametric-anchor",
        "q5_required": True,
        "group": "anchors",
        "title": "Face anchor follows parent geometry",
        "intent": "Verify that a standard face anchor remains tied to changing parent topology.",
        "forge_api": "Anchor.RIGHT / Anchor.LEFT with parent parameter propagation",
        "forge_model": "The attachment references the parent's semantic RIGHT face, not a frozen absolute X coordinate.",
        "lowering": "joint.create uses a native face reference derived from the parent occurrence; the parent width remains a SolidCraft parameter.",
        "native_expectation": "The attached block stays on the parent's right face.",
        "mutation": "Change base_width from 40 to 80 mm in the saved design; the block follows the moved RIGHT face.",
        "references": [
            ("BOSL2", "BOSL2 cardinal anchors similarly express a meaningful side of the parent instead of an absolute coordinate."),
        ],
    },
    {
        "slug": "corner-anchor",
        "q5_required": True,
        "group": "anchors",
        "title": "Topology-backed corner anchor",
        "intent": "Verify a corner reference that follows both parent width and height changes.",
        "forge_api": "Anchor.FRONT_TOP_RIGHT paired with child Anchor.BACK_TOP_RIGHT",
        "forge_model": "A standard corner Anchor is resolved to an edge/on/corner native topology reference rather than a free point.",
        "lowering": "joint.create receives SolidCraft edge/on/corner picks so the saved design can re-find the corner after geometry changes.",
        "native_expectation": "The marker sits on the front-top-right corner of the base.",
        "mutation": "Change the base from 40x20 to 80x40 mm; the marker must follow both the new right side and new top.",
        "references": [
            ("BOSL2", "BOSL2 supports side/edge/corner anchors; its anchor also carries orientation, which is a useful design reference for Forge."),
        ],
    },
    {
        "slug": "anchor-topology-mutation",
        "q5_required": True,
        "group": "anchors",
        "title": "Explicit topology pick follows parent resize",
        "intent": "Verify the AnchorTopology contract directly: Forge supplies fixed baseline edge/face/corner pick coordinates once, then native SolidCraft must retain that selected topology when the parent dimensions change.",
        "forge_api": "anchors() -> AnchorTopology(edge=..., on=..., corner=..., z=..., x=...); attach(parent='front_top_left_pick', child=AnchorFrame())",
        "forge_model": "One parametric Board, one named topology anchor with deliberately fixed numeric pick points, and one centered Marker attached to that anchor.",
        "lowering": "AnchorTopology is inlined into joint.create as edge/on/corner plus optional z/x. No persistent joint.origin and no Forge-side recomputation of the pick coordinates occurs after the saved design is mutated.",
        "native_expectation": "On the 40x20x20 board the marker is centered on the front-top-left corner selected by the explicit topology pick.",
        "mutation": "Change base_width/base_height from 40x20 to 80x40 mm in the saved .sc design; the unchanged native relationship must move the marker to the new front-top-left corner without rerunning Python.",
        "references": [
            ("SolidCraft", "This is a direct test of native topology persistence: the initial pick identifies topology, while later parameter changes move that topology."),
            ("BOSL2", "The higher-level intent is still a semantic attachment point, but this fixture specifically qualifies Forge's lower-level explicit topology reference."),
        ],
    },
    {
        "slug": "assembly-owned-anchor",
        "q5_required": True,
        "group": "anchors",
        "title": "Assembly-owned named anchor",
        "intent": "Verify that an assembly can publish a semantic attachment name without putting that application-specific datum on the reusable component, and that a consumer of the name still lowers to an associative native relationship.",
        "forge_api": "(base + companion).with_anchor('inspection_corner', base, Anchor.FRONT_TOP_RIGHT); datum = frame.anchor('inspection_corner'); Marker().attach(datum.target, parent=datum.reference, ...)",
        "forge_model": "The assembly stores a name mapped to an existing target occurrence plus a normal Forge anchor reference. The reusable Base knows nothing about the semantic name.",
        "lowering": "with_anchor()/anchor() are Forge-side semantic indirection only. The resulting native joint is the same topology-backed FRONT_TOP_RIGHT relationship that a direct attach would emit; no extra native helper object is required.",
        "native_expectation": "The marker sits on the base front-top-right corner while an unrelated companion occurrence remains part of the same assembly.",
        "mutation": "Change base_width/base_height from 40x20 to 80x40 mm in the saved .sc design; the marker created through the assembly-owned name must follow the moved corner without rerunning Python.",
        "references": [
            ("BOSL2", "Semantic attachment names belong naturally to the assembly that owns their meaning rather than to a generic reusable component."),
            ("SolidCraft", "The semantic name disappears during lowering; the persisted native relationship remains topology-backed and associative."),
        ],
    },
    {
        "slug": "four-corner-l",
        "q5_required": True,
        "group": "components",
        "title": "Four centred vertical L-profiles",
        "intent": "Place one short vertical angle profile around each of the four rounded side corners of a rectangular frame. The assembly calculates each occurrence pose directly from frame dimensions.",
        "forge_api": "LProfile.copy(placement=Placement(x=..., y=..., z=..., rotation=(Z, ...)))",
        "forge_model": "One rounded parametric FrameBlock plus four occurrences of one neutral vertical LProfile definition. Position and clocking belong to the assembly; there is no Attachment.",
        "lowering": "Forge binds the occurrence ids returned by component.create/occurrence.copy to replay variables. Numeric unrotated copies use occurrence.copy translate directly; symbolic positions and rotations use a later occurrence.move addressed by the bound id.",
        "native_expectation": "One vertical angle profile wraps each front-left, front-right, rear-right and rear-left rounded side corner. All four occupy Z=22..38 on the 60 mm frame.",
        "mutation": "Change frame_width/depth from 120x80 to 160x120 mm in the saved .sc design; all four profiles follow the calculated corner positions while remaining centred at the same frame height.",
        "references": [
            ("SolidCraft", "component.create/occurrence.copy return real occurrence ids; the replay executor binds those ids before later parametric occurrence.move commands."),
            ("BOSL2", "The neutral angle profile is reused while the assembly owns position and orientation."),
        ],
    },
    {
        "slug": "eight-corner-brackets",
        "q5_required": True,
        "group": "components",
        "title": "Eight vertical L-profiles: two per side corner",
        "intent": "Place two short vertical angle profiles on each rounded side corner, one at the bottom and one at the top. The assembly calculates all eight poses directly from frame dimensions.",
        "forge_api": "LProfile.copy(placement=Placement(x=..., y=..., z=..., rotation=(Z, ...)))",
        "forge_model": "One rounded parametric FrameBlock plus eight occurrences of one neutral LProfile definition. Position and clocking belong to the assembly; there is no Attachment.",
        "lowering": "Forge binds the occurrence ids returned by component.create/occurrence.copy to replay variables. Numeric unrotated copies use occurrence.copy translate directly; symbolic positions and rotations use a later occurrence.move addressed by the bound id.",
        "native_expectation": "Each rounded vertical side corner carries exactly two outside angle profiles. On the 60 mm frame they occupy Z=0..16 and Z=44..60.",
        "mutation": "Change frame_width/depth/height from 120x80x60 to 160x120x90 mm; all four corner pairs follow the calculated X/Y positions and each upper member moves to Z=74..90.",
        "references": [
            ("SolidCraft", "component.create/occurrence.copy return real occurrence ids; the replay executor binds those ids before later parametric occurrence.move commands."),
            ("BOSL2", "One neutral component is repeated by assembly-owned placement."),
        ],
    },
    {
        "slug": "eight-flightcase-corners",
        "q5_required": True,
        "group": "components",
        "title": "Eight flightcase corner protectors",
        "intent": "Reuse one neutral three-plate corner protector on all eight case corners. The assembly calculates each XYZ position and 3D orientation directly from case dimensions.",
        "forge_api": "FlightcaseCorner.copy(placement=Placement(x=..., y=..., z=..., rotation=(axis, angle)))",
        "forge_model": "One rounded CaseBlock plus eight occurrences of one neutral trihedral protector. Position and orientation belong to the assembly; there is no Attachment.",
        "lowering": "Forge binds the occurrence ids returned by component.create/occurrence.copy to replay variables. Numeric unrotated copies use occurrence.copy translate directly; symbolic positions and rotations use a later occurrence.move addressed by the bound id.",
        "native_expectation": "Each of the eight case corners is wrapped by three connected plates: one horizontal and two vertical. The protector outer envelope is a fixed 24x24x24 mm at every corner.",
        "mutation": "Change case_width/depth/height from 120x80x60 to 160x120x90 mm; all protectors follow the calculated corner positions without rerunning Python, while every protector remains exactly 24x24x24 mm.",
        "references": [
            ("SolidCraft", "component.create/occurrence.copy return real occurrence ids; the replay executor binds those ids before later parametric occurrence.move commands."),
            ("BOSL2", "One neutral trihedral part is reused in eight assembly-owned poses."),
        ],
    },
    {
        "slug": "xz-anchor",
        "q5_required": True,
        "group": "anchors",
        "title": "Anchors on XZ-profile extrusion",
        "intent": "Verify standard corner anchors on geometry authored as an XZ polygon and extruded in Y.",
        "forge_api": "with Sketch(plane='XZ'): Polygon2D(..., plane='XZ', world=True); sketch.extrude(...); standard corner Anchors",
        "forge_model": "Forge recovers rectangular bounds/topology from the XZ profile while preserving symbolic width and height. RightMarker and LeftMarker are separate small test parts so this case tests the board anchors, not copied-occurrence addressing.",
        "lowering": "Two joint.create commands use the Board corner topology plus explicit RightMarker and LeftMarker occurrence references. No generated Component:N name is required.",
        "native_expectation": "Left and right markers attach to their respective front-top corners with mirrored spatial results.",
        "mutation": "Change board width/height from 40x20 to 80x40 mm; both markers follow their own corners.",
        "references": [
            ("OpenSCAD", "The profile/extrusion resembles polygon()+linear_extrude(), but Forge retains native SolidCraft parameters and attachment topology."),
            ("BOSL2", "Mirrored corner anchors are a useful check that local anchor frames, not a single global direction assumption, control attachment."),
        ],
    },
    {
        "slug": "circle-negative-extrude",
        "group": "fundamentals",
        "title": "Negative circle profile extrusion",
        "intent": "Qualify Circle2D authored inside an explicit Sketch and an explicitly selected negative extrusion direction with one minimal native model.",
        "forge_api": "with Sketch(plane='XY'): Circle2D(d=20); sketch.extrude(30, direction=Direction.NEGATIVE)",
        "forge_model": "One circular 2D profile authored in an explicit XY Sketch and extruded 30 mm along negative Z; no CSG or attachment is involved.",
        "lowering": "Native XY sketch with one circle followed by solid.extrude(direction='negative').",
        "native_expectation": "One 20 mm diameter cylindrical body spans X/Y -10..10 mm and Z -30..0 mm, with an error-free saved SolidCraft timeline.",
        "mutation": "No saved-design mutation in this fixture; it isolates direct circle-profile lowering and negative extrusion semantics.",
        "references": [
            ("OpenSCAD", "Comparable to a circle followed by linear_extrude(height=30) after selecting the opposite extrusion direction."),
            ("SolidCraft", "The persisted native extrusion direction and measured Z bounds are the source of truth for negative-direction semantics."),
        ],
    },
    {
        "slug": "rounded-rectangle-sketch",
        "group": "features",
        "title": "Explicit rounded-rectangle sketch pad",
        "intent": "Qualify RoundedRectangle2D in the explicit named Sketch API using true native rounded-rectangle sketch geometry.",
        "forge_api": "with Sketch(name='Rounded pad', on=body): add(RoundedRectangle2D(...)); body + sketch.extrude(...)",
        "forge_model": "One 80 x 60 x 5 mm base plate plus a centered 40 x 30 mm rounded-rectangle pad with 5 mm corner radius and 8 mm height.",
        "lowering": "The named explicit Sketch emits one sketch.rectangle.rounded with true arc corners, then a native solid.extrude(operation='join').",
        "native_expectation": "The result is one joined body: an 80 x 60 x 5 mm base plate with a centered 40 x 30 x 8 mm rounded pad on top. The Rounded pad sketch has one closed profile made from four straight edges and four corner arcs. SolidCraft 0.42 also adds one construction diagonal between opposite arc centres; that construction line is not part of the profile.",
        "mutation": "No saved-design mutation in this fixture; it isolates explicit rounded-rectangle sketch geometry and native join extrusion.",
        "references": [
            ("SolidCraft", "Native rounded sketch rectangles preserve true arc geometry and remain inspectable in the saved sketch."),
            ("PythonSCAD", "The explicit Sketch scope keeps 2D profile authoring separate from the subsequent 3D extrusion."),
        ],
    },
    {
        "slug": "primitive-csg",
        "group": "fundamentals",
        "title": "Primitive CSG",
        "intent": "Qualify direct primitive/CSG modelling independently of feature-history geometry: Sphere and Box union, translated primitives, one native X-axis Cylinder cut and intersection.",
        "forge_api": "Sphere(); Box(...).move(...); Cylinder(..., axis=Axis.X).at(...); + / - / &",
        "forge_model": "A Shape CSG tree rooted in Sphere so Forge deliberately selects the direct CSG compiler instead of the feature-history Box compiler.",
        "lowering": "solid.sphere(new), solid.box(join), one X-axis solid.cylinder(cut), then solid.box(intersect).",
        "native_expectation": "SolidCraft accepts the complete CSG command path, produces one valid clipped body and evaluates the native timeline without errors.",
        "mutation": "No saved-design mutation in this case; it isolates primitive CSG lowering. Parametric edits are covered by dedicated Q5 cases.",
        "references": [
            ("OpenSCAD", "Closest to ordinary union()/difference()/intersection() with translate()/rotate() around primitives."),
            ("PythonSCAD", "Useful comparison for Python objects and operators while Forge still delegates all geometry to SolidCraft."),
        ],
    },
    {
        "slug": "bracket",
        "group": "fundamentals",
        "title": "Minimal L-profile",
        "intent": "Provide a deliberately simple reusable L-shaped reference component for later attachment/orientation qualification.",
        "forge_api": "with Sketch(plane='XZ'): Polygon2D(..., plane='XZ'); sketch.extrude(width, direction=Direction.SYMMETRIC)",
        "forge_model": "One symbolic L profile extruded symmetrically through its width; no holes, fillets, anchors or secondary features.",
        "lowering": "Native XZ sketch/polygon plus symmetric extrusion. No assembly commands are present yet.",
        "native_expectation": "A clean 40 mm L profile with 12 mm arms and 24 mm symmetric extrusion width.",
        "mutation": "Not yet an attachment mutation case. This component is intentionally the geometry baseline for upcoming multi-orientation anchor tests.",
        "references": [
            ("OpenSCAD", "Equivalent baseline is a 2D L polygon followed by linear_extrude(center=true)."),
            ("BOSL2", "Later attachment cases can reuse this simple shape while testing anchor/orient semantics independently of bracket feature complexity."),
        ],
    },
]



def blocked_qualification_cases() -> tuple[dict, ...]:
    """Cases kept in the qualification catalog but not currently supported."""
    return tuple(
        case for case in QUALIFICATION_CASES
        if case.get("blocked_reason")
    )


def supported_qualification_cases() -> tuple[dict, ...]:
    """Cases expected to compile and pass the normal Q1-Q6 flow."""
    return tuple(
        case for case in QUALIFICATION_CASES
        if not case.get("blocked_reason")
    )


def supported_case_slugs() -> tuple[str, ...]:
    """Slugs for cases that may enter command/native qualification."""
    return tuple(case["slug"] for case in supported_qualification_cases())

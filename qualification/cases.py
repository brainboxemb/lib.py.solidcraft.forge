"""Qualification case metadata for the Forge library site.

Keep this deliberately explicit.  A qualification case is documentation of a
contract between the public Forge API, Forge's compiler model and native
SolidCraft behaviour.  The site and site tests both consume this table.
"""

from pathlib import Path

from scpf.version import TESTED_SOLIDCRAFT_VERSION

REFERENCE_URLS = {
    "SolidCraft": "https://docs.solidcraft.io/guide/assemblies.html",
    "BOSL2": "https://github.com/BelfrySCAD/BOSL2/wiki/Tutorial-Attachment-Overview",
    "OpenSCAD": "https://openscad.org/documentation.html",
    "PythonSCAD": "https://github.com/pythonscad/pythonscad",
    "CadQuery": "https://cadquery.readthedocs.io/",
    "build123d": "https://build123d.readthedocs.io/en/stable/",
}

DEFAULT_REFERENCE_IMPLEMENTATIONS = ("pythonscad", "pybosl2", "cadquery", "build123d")
REFERENCE_IMPLEMENTATION_LABELS = {
    "pythonscad": "PythonSCAD",
    "pybosl2": "pyBOSL2",
    "cadquery": "CadQuery",
    "build123d": "build123d",
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
    ("Tool verify", "Generated command contract", "Example tests pass and Forge compiles a complete SolidCraft command document."),
    ("Model verify", "SolidCraft execution", f"SolidCraft {TESTED_SOLIDCRAFT_VERSION} replays the command document and saves an editable design."),
    ("Geometry", "Native geometry", "Timeline and measured body geometry match the declared proof contract."),
    ("Saved design", "Associativity", "Cases that claim associativity still pass after editing the saved SolidCraft design."),
    ("Visual", "Visual regression", "Fixed-camera native renders match the expected shape from the required views."),
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
        "saved_design_required": True,
        "group": "fundamentals",
        "title": "Parameterized Box",
        "intent": "Establish the smallest model/parameter contract: three public Python fields create one editable native box.",
        "forge_api": "class fields -> Parameter; Box(length, width, height); build()",
        "forge_model": "One root Shape with symbolic length, width and height; no occurrence or assembly layer.",
        "lowering": "parameters.add for the public dimensions, followed directly by native solid.box; no sketch is synthesized.",
        "native_expectation": "One rectangular solid with the requested 40 x 30 x 10 mm dimensions and an error-free timeline.",
        "mutation": "Required because this case explicitly claims an editable native Box. Change length from 40 to 50 mm in the saved .sc design; the Box must rebuild to 50 x 30 x 10 mm without rerunning Python.",
        "references": [
            ("OpenSCAD", "cube([40,30,10]) is the constructive-geometry baseline; Forge differs by preserving editable SolidCraft history."),
        ],
    },
    {
        "slug": "anchored-holes",
        "group": "features",
        "title": "Face-relative hole with native pattern",
        "intent": "Verify one TOP-face source hole cut followed by one native rectangular history pattern.",
        "forge_api": "with Sketch(on=plate, parent=Anchor.TOP): Circle2D(...); source_cut = sketch.extrude(Depth.THROUGH_ALL); plate.rectangular_pattern(source_cut, ...)",
        "forge_model": "A feature-based plate with one face-attached source hole cut and one native rectangular pattern that creates the second hole.",
        "lowering": "Forge emits one attached Hole sketch/cut and one native solid.pattern.rectangular history feature. No Forge-side repeat helper or expanded duplicate profiles are used.",
        "native_expectation": "One plate with two through holes at the requested Y spacing, one source cut and one native rectangular pattern feature.",
        "mutation": "No saved-design mutation in this fixture; geometry and feature placement are measured at geometry.",
        "references": [
            ("OpenSCAD", "Comparable geometry normally uses difference() and repeated cylinders. This case instead qualifies one semantic TOP-face source cut plus native SolidCraft pattern history; native solid.hole itself is qualified separately by hole-family."),
        ],
    },
    {
        "slug": "hole-family",
        "group": "features",
        "title": "Native Hole family",
        "intent": "Qualify the four normal mechanical hole intents as direct native features: simple, counterbore, countersink and threaded.",
        "forge_api": "Hole(...); CounterboreHole(...); CountersinkHole(...); ThreadedHole(...)",
        "forge_model": "One 120 x 40 x 12 mm plate with four explicitly positioned Hole-family features. ThreadedHole keeps thread intent separate from the simple bore diameter.",
        "lowering": "Each Forge Hole-family object lowers one-to-one to one native solid.hole command. Counterbore and countersink use the native hole type fields; ThreadedHole uses native thread metadata/modeling fields. No sketch or helper subtraction solid is synthesized.",
        "native_expectation": "One plate contains four editable native Hole features: Ø6 simple, Ø6/Ø12 x 4 counterbore, Ø6/Ø12 90° countersink, and an M6 modeled threaded hole using an explicit Ø5 tap drill.",
        "mutation": "No saved-design mutation is required in this first Hole-family qualification; unit, integration and native geometry checks prove API, native command identity and geometry while visual proves the visible forms.",
        "references": [
            ("build123d", "build123d 0.12.0 provides native Hole, CounterBoreHole and CounterSinkHole operations. Its core library has no equivalent native tapped-hole metadata feature, so the fourth reference cut is the Ø5 M6 tap-drill envelope."),
            ("CadQuery", "CadQuery independently expresses simple, counterbore and countersink geometry; the threaded reference uses the Ø5 tap-drill envelope because native thread metadata is SolidCraft-specific."),
            ("PythonSCAD", "Constructive geometry independently reproduces the four hole envelopes; the thread reference is the Ø5 tap-drill envelope."),
            ("pyBOSL2", "Constructive geometry independently reproduces the four hole envelopes; the thread reference is the Ø5 tap-drill envelope."),
        ],
    },
    {
        "slug": "sheet-fold",
        "group": "features",
        "title": "Flat sheet, through hole and 90° fold",
        "intent": "Qualify the fabrication workflow used by later bent parts: create one flat sheet blank, cut an ordinary Hole while flat, fold existing material, and recover the developed flat pattern.",
        "forge_api": "with Sketch(...): Rectangle2D(...); blank.sheet_metal(thickness=..., bend_radius=..., k_factor=...); sheet + Hole(...).at(...); sheet.fold(line=..., angle=..., fixed=...)",
        "forge_model": "One 80 x 40 mm rectangular flat blank with a shared 2 mm sheet rule, one Ø6 through hole in the fixed flat, and one 90 degree fold along the Y direction near the right side.",
        "lowering": "Forge emits one sheet.manage_rules, one Blank sketch, one sheet.flange(type='base'), one native solid.hole and one native sheet.fold. No solid.extrude or fused-solid bend approximation is used.",
        "native_expectation": "SolidCraft 0.42 keeps one connected sheet-metal body with the Ø6 hole on the fixed flat, one native Fold feature and a flat pattern that recovers the original rectangular blank and cutout.",
        "mutation": "No saved-design mutation is required in this first sheet-metal qualification. unit, integration and native geometry checks prove the shared rule, native feature history and formed geometry; a post-build flat-pattern inspection proves recoverability of the developed blank.",
        "references": [
            ("build123d", "The pinned build123d 0.12.0 reference uses make_brake_formed for an independent final-geometry comparison. Its newer BuildSheet/bend API is design input only and is not silently substituted into the pinned reference runtime."),
            ("CadQuery", "Independent final geometry is built from flat and bent solid envelopes; CadQuery does not provide the same native sheet-history contract."),
            ("PythonSCAD", "Constructive geometry independently represents the formed envelope and through hole; native sheet rules/history remain SolidCraft-only evidence."),
            ("pyBOSL2", "Constructive geometry independently represents the formed envelope and through hole; native sheet rules/history remain SolidCraft-only evidence."),
        ],
    },
    {
        "slug": "top-sketch-after-chamfer",
        "group": "features",
        "title": "TOP Sketch after chamfer",
        "intent": "Verify that a TOP-attached Sketch still selects the resulting planar +Z face after a native chamfer changes the body's topology.",
        "forge_api": "Box(...).chamfer(..., edges=Edges.VERTICAL); with Sketch(on=plate, parent=Anchor.TOP): Circle2D(...); cut through all",
        "forge_model": "One 100 x 70 x 10 mm plate, four 8 mm plan-view corner chamfers, then one native TOP-attached Sketch containing a centered 12 mm through hole.",
        "lowering": "Forge emits solid.chamfer before model.faces. Replay selects the largest +Z planar face by plane_normal and area, tolerating only tiny numeric-vector noise from the native kernel, then passes its point/index to face-attached sketch.create.",
        "native_expectation": "SolidCraft 0.42 builds one chamfered plate with one centered through hole. The Top hole Sketch remains a solved feature attached to the actual post-chamfer top face.",
        "mutation": "No saved-design mutation in this fixture; it isolates stable face lookup after topology-changing native features.",
        "references": [
            ("PythonSCAD", "Independent CSG reference cuts the four corner wedges before subtracting the central through hole."),
            ("CadQuery", "Independent feature reference applies a vertical-edge chamfer before creating the top-face hole."),
            ("build123d", "Independent builder reference applies the same feature order: Box, vertical-edge chamfer, top-face hole."),
        ],
    },
    {
        "slug": "parameter-scope",
        "saved_design_required": True,
        "group": "parameters",
        "title": "Explicit component parameters and shared dependencies",
        "intent": "Verify that reusable component defaults stay fixed unless explicitly included, while selected defaults become native parameters and parent Parameters/Expressions are reused rather than duplicated in the child.",
        "forge_api": "@component(include=('width',)) class Panel; Panel(width=self.shared_width); Panel(width=half(self.shared_width))",
        "forge_model": "Only explicitly included width defaults become component-local Parameters. The lower-case depth default remains fixed. Inherited Parameter/Expression inputs become external bindings to the existing parent dependency.",
        "lowering": "Explicitly included component parameters are namespaced with the internal definition number plus readable component name (for example d1_Panel_width); unincluded child defaults stay fixed; inherited names such as shared_width remain unprefixed and are emitted once even when several child definitions use them.",
        "native_expectation": "The saved SolidCraft design exposes d1_Panel_width, d2_Panel_2_width and shared_width; changing shared_width updates both directly-bound children and the derived half-width child without rerunning Python.",
        "mutation": "Change shared_width from 80 to 100 mm in the saved native design; widths must change from [40,40,60,80,80] to [40,50,60,100,100].",
        "references": [
            ("PythonSCAD", "Reference geometry remains ordinary Python; Forge adds explicit native parameter publication because that is persistence/editability intent rather than geometry syntax."),
            ("SolidCraft", "Native parameters and expressions are the source of truth for saved-design editability and rebuild behaviour."),
        ],
    },
    {
        "slug": "parent-derived-child-size",
        "saved_design_required": True,
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
        "slug": "repeated-parent-attachments",
        "saved_design_required": True,
        "group": "associativity",
        "title": "Attachments on repeated parent occurrences",
        "intent": "Verify two disconnected rigid-joint graphs when two occurrences of one shared parent definition each own one attached child.",
        "forge_api": "right = left.copy(placement=Placement(x=60)); marker_a = Marker().attach(left, parent=Anchor.TOP, child=Anchor.BOTTOM); marker_b = marker_a.copy().attach(right, parent=Anchor.TOP, child=Anchor.BOTTOM)",
        "forge_model": "Two Parent occurrences share one definition and one parent_height dependency. Two Marker occurrences share one definition. Each Marker has exactly one rigid Attachment to a different Parent occurrence.",
        "lowering": "Forge creates one Parent definition plus one translated copy and one Marker definition plus one copy. Each Marker receives its symbolic computed seed Placement through a replay-bound occurrence.move, followed by exactly one authored rigid joint.create to its replay-bound Parent occurrence. No generated placement joint is allowed.",
        "native_expectation": "Both markers sit on their own parent TOP face. After parent_height changes in the saved design, both disconnected joint graphs must rebuild so both markers follow the changed top faces.",
        "mutation": "Change parent_height from 40 to 60 mm in the saved .sc design; both Parent occurrences become 60 mm tall and both Marker occurrences move from Z=40..50 to Z=60..70 without rerunning Python.",
        "references": [
            ("SolidCraft", "This case isolates the 0.42 joint-solver behaviour for two disconnected graphs that share reusable component definitions."),
            ("BOSL2", "Two independent TOP-to-BOTTOM attachments express the same parent/child intent without SolidCraft-specific replay identity."),
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
        "saved_design_required": True,
        "group": "associativity",
        "title": "Editable distance between attached components",
        "intent": "Verify that distance along the attachment normal remains a native editable joint parameter.",
        "forge_api": "attach(..., gap=self.gap)",
        "forge_model": "Rigid Attachment with a symbolic gap expression; anchor identities are unchanged.",
        "lowering": "The child receives a symbolic seed pose so a floating graph starts at the authored mating position; joint.create(type='rigid', offset='gap') remains the relationship and the gap remains a native expression in both places rather than a flattened number.",
        "native_expectation": "The child sits 10 mm away from the parent's RIGHT face along the joint normal.",
        "mutation": "Change gap from 10 to 30 mm in the saved .sc design; the child must move another 20 mm without rerunning Python.",
        "references": [
            ("BOSL2", "Conceptually similar to an attachment displacement along the local anchor normal rather than a world-axis translate."),
        ],
    },
    {
        "slug": "parametric-offset",
        "saved_design_required": True,
        "group": "associativity",
        "title": "Editable local offset at an attachment",
        "intent": "Verify the existing local (u,v) attachment-plane offset and make its coordinate semantics explicit.",
        "forge_api": "attach(..., offset=(u, v))",
        "forge_model": "Attachment stores two symbolic local planar values; these are not world X/Y/Z coordinates.",
        "lowering": "The computed child seed pose retains the symbolic local offset, then the actual relationship is joint.create(type='planar', values=[u,v,angle]). The seed move is not an additional joint.",
        "native_expectation": "The marker moves within the selected corner anchor's local attachment plane.",
        "mutation": "Change shift from 5 to 10 mm in the saved design; the marker must follow the same local axis by another 5 mm.",
        "references": [
            ("BOSL2", "Important reference: attach() operates in the local coordinate system at the parent anchor, not blindly in world coordinates."),
            ("OpenSCAD", "A raw translate([x,y,z]) is world/object transform syntax and therefore is not equivalent to this local joint offset."),
        ],
    },
    {
        "slug": "parametric-anchor",
        "saved_design_required": True,
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
        "saved_design_required": True,
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
        "saved_design_required": True,
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
        "saved_design_required": True,
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
        "saved_design_required": True,
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
        "saved_design_required": True,
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
        "saved_design_required": True,
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
        "saved_design_required": True,
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
        "slug": "round-top-sketch",
        "group": "fundamentals",
        "title": "TOP Sketch on circular body",
        "intent": "Verify that a TOP-attached explicit Sketch can select the largest +Z planar face of a circular extrusion without rectangular-body metadata.",
        "forge_api": "disc = Sketch(... Circle2D ...).extrude(10); with Sketch(on=disc, parent=Anchor.TOP): Circle2D(d=44); body + hub.extrude(16)",
        "forge_model": "One Ø100 x 10 mm circular base plus one Ø44 x 16 mm hub joined from the selected top face.",
        "lowering": "Forge emits the circular base extrusion, model.faces with plane_normal=[0,0,1] and max=area, then a face-attached Hub Sketch and join extrusion. No rectangular base lookup is required.",
        "native_expectation": "One stepped cylindrical body spans Z=0..26 mm. Disc and Hub remain two solved native Sketch/Extrude feature pairs and the Hub is attached to the actual top face of the Disc.",
        "mutation": "No saved-design mutation; this fixture isolates support-face lookup on a non-rectangular feature body.",
        "references": [
            ("SolidCraft", "Native geometry proves the face-attached Hub Sketch builds on the circular Disc and stays solved."),
            ("PythonSCAD", "Independent CSG reference proves the stepped-cylinder geometry."),
            ("CadQuery", "Independent union reference proves the same two-radius stepped body."),
            ("build123d", "Independent builder reference proves the same baseline geometry."),
        ],
    },
    {
        "slug": "circle-negative-extrude",
        "group": "fundamentals",
        "title": "Negative circle profile extrusion",
        "intent": "Qualify Circle2D authored inside an explicit Sketch and a negative signed extrusion distance with one minimal native model.",
        "forge_api": "with Sketch(plane='XY'): Circle2D(d=20); sketch.extrude(-30)",
        "forge_model": "One circular 2D profile authored in an explicit XY Sketch and extruded 30 mm along negative Z; no CSG or attachment is involved.",
        "lowering": "The signed Forge distance is normalized to a positive native distance plus solid.extrude(direction='negative').",
        "native_expectation": "One 20 mm diameter cylindrical body spans X/Y -10..10 mm and Z -30..0 mm, with an error-free saved SolidCraft timeline.",
        "mutation": "No saved-design mutation in this fixture; it isolates direct circle-profile lowering and negative extrusion semantics.",
        "references": [
            ("OpenSCAD", "Comparable to a circle followed by linear_extrude(height=30) after selecting the opposite extrusion direction."),
            ("SolidCraft", "The persisted native extrusion direction and measured Z bounds are the source of truth for negative-direction semantics."),
        ],
    },
    {
        "slug": "sketch-pattern-mirror",
        "saved_design_required": True,
        "group": "associativity",
        "title": "Associative sketch pattern and mirror",
        "intent": "Verify that one Circle seed and one Slot seed drive repeated sketch geometry through native SolidCraft rectangular patterns and mirrors instead of Python-expanded copies.",
        "forge_api": "seed = sketch.add(Circle2D(...)); sketch.rectangular_pattern(seed, ...); sketch.mirror(pattern, axis=Axis.X/Y); same flow for SlotCenterToCenter2D",
        "forge_model": "One 240 x 160 x 5 mm plate with two attached Sketches. Dog holes use one Circle seed, one native sketch pattern and one mirror. Clamp slots use one Slot seed, one native sketch pattern and three mirrors. Each Sketch is cut once.",
        "lowering": "Forge binds the real native curves returned by the seed profile, feeds those ids into sketch.pattern.rectangular, binds the pattern curves, and feeds those into sketch.mirror. User Python never contains SolidCraft-generated ids.",
        "native_expectation": "SolidCraft saves one Dog holes Sketch and one Clamp slots Sketch with associative pattern/mirror relationships. Baseline geometry contains 8 Ø8 holes and 8 straight Slots. No expanded set of independent seed commands is emitted.",
        "mutation": "Change hole_diameter 8->10 mm, hole_pitch 25->30 mm and slot_pitch 50->30 mm in the saved .sc design. Without rerunning Python all existing pattern and mirror copies must follow the changed seed and spacing. Pattern counts remain native editable parameters, but SolidCraft 0.42 mirrors a fixed selected entity set and does not automatically adopt new entities added later by an upstream count change.",
        "references": [
            ("SolidCraft", "The native saved design is the source of truth for the associative sketch pattern/mirror relationships and their saved-design mutation."),
            ("PythonSCAD", "Independent final geometry confirms the repeated cuts without relying on Forge's command lowering."),
            ("CadQuery", "Independent final geometry confirms the expected hole and Slot positions."),
            ("build123d", "Independent final geometry confirms the expected profile repetition and cut result."),
        ],
    },
    {
        "slug": "selective-profile-extrude",
        "saved_design_required": True,
        "group": "associativity",
        "title": "Selective Sketch profile extrusion",
        "intent": "Verify that one associative Sketch pattern can keep all generated profiles while one native extrusion selects only the intended closed regions by sketch-local points.",
        "forge_api": "sketch.rectangular_pattern(...); sketch.extrude(Depth.THROUGH_ALL, profiles=[(x, y), ...], exact_regions=True)",
        "forge_model": "One 120 x 60 x 5 mm plate, one Circle seed, one native four-instance sketch pattern and one through-all cut selecting three of the four circle profiles.",
        "lowering": "Forge emits the Circle and native sketch pattern once, then passes three fixed point selections directly to solid.extrude profiles with exact_regions=true. No profile indices, generated curve ids or deleted pattern copies appear in user Python.",
        "native_expectation": "SolidCraft saves one Selected holes Sketch containing the associative four-circle pattern and one cut ExtrudeFeature that removes exactly three profiles while leaving the fourth region uncut.",
        "mutation": "Change hole_diameter 8->10 mm and hole_pitch 20->24 mm in the saved .sc design. Without rerunning Python the three selected cuts must follow their associated pattern profiles, including profiles whose centres move away from the original pick points; the unselected profile remains uncut.",
        "references": [
            ("SolidCraft", "Native saved-design proves that saved point-based profile selections remain attached to the intended profile curves after pattern spacing and diameter changes."),
            ("PythonSCAD", "Independent final geometry confirms the baseline three-hole result without using Forge's profile-selection lowering."),
            ("CadQuery", "Independent final geometry confirms that only three of the four possible patterned positions are cut."),
            ("build123d", "Independent final geometry confirms the selected-hole plate."),
        ],
    },
    {
        "slug": "circular-feature-pattern",
        "saved_design_required": True,
        "group": "features",
        "title": "Native circular feature pattern",
        "intent": "Qualify one real SolidCraft circular History pattern over an existing cut feature, rather than Forge-expanded repeated holes.",
        "forge_api": "source = bolt.extrude(Depth.THROUGH_ALL); body = body - source; body.circular_pattern(source, count=bolts, axis=Axis.Z)",
        "forge_model": "One 100 x 100 x 6 mm plate, one native Ø8 source cut on a 60 mm pitch circle and one native six-instance circular feature pattern.",
        "lowering": "Forge emits the source Sketch/cut once, then exactly one solid.pattern.circular with features=['BoltHole']; bolts is a dimensionless native count parameter and pcd remains a millimetre parameter used by the source profile position.",
        "native_expectation": "SolidCraft saves one plate with six through holes and one native CircularPatternFeature that references the original BoltHole cut.",
        "mutation": "Required because bolts is a saved native pattern-count parameter. Change bolts from 6 to 4 in the saved .sc design; the pattern must rebuild to four holes without rerunning Python while retaining one source cut and one CircularPatternFeature.",
        "references": [
            ("SolidCraft", "Native integration through saved-design checks prove one saved CircularPatternFeature and count mutation. The four comparison libraries independently prove the baseline six-hole geometry."),
        ],
    },
    {
        "slug": "rectangular-pattern",
        "saved_design_required": True,
        "group": "features",
        "title": "Native rectangular feature pattern",
        "intent": "Qualify a real SolidCraft rectangular History pattern over one existing cut feature, rather than Forge-expanded repeated geometry.",
        "forge_api": "source = slot.extrude(-4); body = body - source; body.rectangular_pattern(source, count=columns, spacing=pitch, direction=Axis.X, count2=rows, spacing2=row_pitch, direction2=Axis.Y)",
        "forge_model": "One 120 x 80 x 4 mm plate, one native straight Slot cut and one native 3 x 2 rectangular feature pattern.",
        "lowering": "Forge emits the source Sketch/cut once, then exactly one solid.pattern.rectangular with features=['Slot']; columns/rows are dimensionless native parameters and pitches remain millimetre parameters.",
        "native_expectation": "SolidCraft saves one plate with six slot cuts and one native rectangular pattern History feature that references the original Slot cut.",
        "mutation": "Required because columns and pitch are saved native pattern parameters. Change columns from 3 to 2 and pitch from 24 to 30 mm in the saved .sc design; the pattern must rebuild to a 2 x 2 layout without rerunning Python while retaining one source Slot cut and one RectangularPatternFeature.",
        "references": [
            ("SolidCraft", "Native integration through geometry checks additionally prove one saved RectangularPatternFeature. The four comparison libraries independently prove the final 3 x 2 slot geometry."),
        ],
    },
    {
        "slug": "slot-family",
        "group": "features",
        "title": "Native sketch Slot family",
        "intent": "Qualify all five SolidCraft 0.42 Slot construction methods as direct SCPF sketch profiles rather than approximating them with rounded rectangles or hand-built curves.",
        "forge_api": "SlotCenterToCenter2D(...); SlotOverall2D(...); SlotCenterPoint2D(...); SlotArcThreePoint2D(...); SlotArcCenter2D(...) inside one explicit Sketch",
        "forge_model": "One 160 x 120 x 5 mm plate with five separate closed Slot profiles in one named sketch, removed with one through-all cut.",
        "lowering": "Each public constructor emits exactly its matching sketch.slot.* command; the sketch is finished once and one native cut extrusion removes all five profiles.",
        "native_expectation": "SolidCraft saves one plate, one Slot family sketch containing five closed profiles and one error-free cut extrusion. The native timeline must not contain sketch.rectangle.rounded as a substitute for Slot construction.",
        "mutation": "No saved-design mutation is required; this case isolates the five native sketch construction methods and their saved feature history.",
        "references": [
            ("SolidCraft", "Native integration through geometry checks additionally prove the five sketch.slot.* command identities. The four comparison libraries independently prove the resulting five cut shapes."),
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
        "mutation": "No saved-design mutation in this case; it isolates primitive CSG lowering. Parametric edits are covered by dedicated saved-design cases.",
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
    """Cases expected to compile and pass the normal full qualification flow."""
    return tuple(
        case for case in QUALIFICATION_CASES
        if not case.get("blocked_reason")
    )


def supported_case_slugs() -> tuple[str, ...]:
    """Slugs for cases that may enter command/native qualification."""
    return tuple(case["slug"] for case in supported_qualification_cases())


REPO_ROOT = Path(__file__).resolve().parents[1]


def case_source_path(slug: str, implementation: str = "scpf") -> Path:
    """Return the registered source model for one qualification implementation.

    Existing cases use the historical examples/<slug>/<implementation>/model.py
    convention. A case may override that location with a `sources` mapping so
    qualification execution is not structurally tied to the examples tree.
    """
    case = next(
        (row for row in QUALIFICATION_CASES if row["slug"] == slug),
        None,
    )
    if case is None:
        raise KeyError(slug)
    override = (case.get("sources") or {}).get(implementation)
    relative = (
        Path(override)
        if override
        else Path("examples") / slug / implementation / "model.py"
    )
    return REPO_ROOT / relative

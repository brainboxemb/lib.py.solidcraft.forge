"""Declared qualification coverage for the public SCPF surface.

The goal is not to pretend every symbol needs a native screenshot.  Each row
declares the appropriate target qualification level for that kind of API and
the highest dedicated coverage currently available.
"""

from scpf.version import TESTED_SOLIDCRAFT_VERSION


EXPORT_COVERAGE = {
    "Box": ("Visual", "Visual", ["simple-box"], "Native primitive and parameter baseline."),
    "Cylinder": ("Visual", "Visual", ["primitive-csg"], f"Native principal-axis Cylinder is qualified with explicit Axis.X in SolidCraft {TESTED_SOLIDCRAFT_VERSION}; Axis.Y/Z use the same primitive field."),
    "Cone": ("Tool verify", "Tool verify", [], f"Public Cone/frustum semantics, parameter preservation and CSG combinations are covered by the shared geometry contract matrix; the pinned SolidCraft {TESTED_SOLIDCRAFT_VERSION} command snapshot proves the native solid.cone contract. A dedicated visual visual fixture remains separate capability work."),
    "Sphere": ("Visual", "Visual", ["primitive-csg"], f"Primitive CSG creation is native-qualified in SolidCraft {TESTED_SOLIDCRAFT_VERSION}."),
    "Hole": ("Visual", "Visual", ["hole-family", "anchored-holes"], "Simple native Hole.at() is qualified directly by hole-family; anchored-holes separately qualifies face-relative repeated placement."),
    "CounterboreHole": ("Visual", "Visual", ["hole-family"], "Native cylindrical counterbore intent is command-, geometry- and visual-qualified."),
    "CountersinkHole": ("Visual", "Visual", ["hole-family"], "Native conical countersink intent is command-, geometry- and visual-qualified."),
    "ThreadedHole": ("Visual", "Visual", ["hole-family"], "Native M6 tapped-hole metadata and modeled-thread intent are qualified by the Hole-family fixture."),
    "Lip": ("Visual", "GAP", [], "Plastic feature needs a dedicated native fixture."),
    "SnapFit": ("Visual", "GAP", [], "Plastic feature needs a dedicated native fixture."),
    "Boss": ("Visual", "Tool verify", [], "Boss.attach() retains command-level unit coverage; a dedicated native qualification case is still required."),
    "Rest": ("Visual", "GAP", [], "Plastic feature needs a dedicated native fixture."),
    "Depth": ("Tool verify", "Visual", ["anchored-holes"], "THROUGH_ALL is exercised by the native hole fixture."),
    "Rectangle2D": ("Visual", "Visual", ["anchored-holes"], "Rectangle2D is authored inside an explicit Sketch and native-qualified through the rectangle sketch/extrude path."),
    "RoundedRectangle2D": ("Visual", "Visual", ["rounded-rectangle-sketch"], "Explicit named Sketch lowering preserves one solved eight-curve rounded profile with four true arc corners."),
    "SlotCenterToCenter2D": ("Visual", "Visual", ["slot-family"], "Native center-to-center Slot constructor is qualified directly through sketch.slot.center_to_center."),
    "SlotOverall2D": ("Visual", "Visual", ["slot-family"], "Native overall-length Slot constructor is qualified directly through sketch.slot.overall."),
    "SlotCenterPoint2D": ("Visual", "Visual", ["slot-family"], "Native center-point Slot constructor is qualified directly through sketch.slot.center_point."),
    "SlotArcThreePoint2D": ("Visual", "Visual", ["slot-family"], "Native three-point arc Slot constructor is qualified directly through sketch.slot.arc_three_point."),
    "SlotArcCenter2D": ("Visual", "Visual", ["slot-family"], "Native center-arc Slot constructor is qualified directly through sketch.slot.arc_center."),
    "Circle2D": ("Visual", "Visual", ["circle-negative-extrude"], "Circle2D is native- and visual-qualified inside an explicit Sketch scope with negative extrusion."),
    "Polygon2D": ("Visual", "Visual", ["xz-anchor", "bracket"], "XZ Polygon2D authored inside explicit Sketch scopes is native-qualified for symmetric and positive extrusion."),
    "Shape": ("Tool verify", "Visual", ["simple-box", "anchored-holes", "bracket", "sheet-fold"], "Core composition node is exercised by solid and sheet-metal native cases."),
    "Parameter": ("Saved design", "Saved design", ["parameter-scope", "parent-derived-child-size", "parametric-attach", "parametric-offset", "parametric-anchor"], "Component-local parameters, inherited bindings and parent-derived child expressions are qualified through saved-design mutation."),
    "Placement": ("Visual", "Visual", ["components", "four-corner-l"], "Numeric Placement is native-qualified by components; symbolic parameter-driven Placement and replay-safe occurrence.move lowering are mutation-qualified by four-corner-l."),
    "Edges": ("Visual", "Visual", ["four-corner-l", "eight-corner-brackets", "eight-flightcase-corners"], "Edges.VERTICAL is native-qualified through rounded reference frames; profile-derived and explicit edge selections still need separate coverage."),
    "Faces": ("Visual", "Visual", ["anchored-holes"], "TOP face placement is qualified; other face selections need capability coverage."),
    "Anchor": ("Visual", "Visual", ["parametric-anchor", "corner-anchor", "xz-anchor"], "Face and corner selectors are qualified by real native anchor cases; AnchorFrame is tracked separately."),
    "AnchorFrame": ("Visual", "Tool verify", ["anchor-topology-mutation"], "The public AnchorFrame command path is covered with a real qualification fixture, but arbitrary oriented-frame native/visual coverage is still missing."),
    "AnchorTopology": ("Saved design", "Saved design", ["anchor-topology-mutation"], "Explicit edge/on/corner topology is native-qualified through saved-design parent resize; explicitly rotated occurrences remain unsupported."),
    "Axis": ("Tool verify", "Visual", ["anchored-holes", "primitive-csg"], "Axis values are exercised by native feature patterns and principal-axis Cylinder geometry."),
    "X": ("Tool verify", "Tool test", [], "Covered as an occurrence-rotation and parent-bound token; dedicated command-contract coverage remains."),
    "Y": ("Tool verify", "Tool test", [], "Covered as an occurrence-rotation and parent-bound token; dedicated command-contract coverage remains."),
    "Z": ("Tool verify", "Tool test", [], "Covered as an occurrence-rotation token; dedicated command-contract coverage remains."),
    "CENTER": ("Visual", "Visual", ["anchored-holes", "rounded-rectangle-sketch"], "Semantic Sketch profile centre; command-level centering and native centred Rectangle2D/RoundedRectangle2D geometry are qualified."),
    "TOP": ("Tool verify", "Tool verify", [], "Cardinal direction constant; combination semantics are covered by API regressions."),
    "BOTTOM": ("Tool verify", "Tool verify", [], "Cardinal direction constant; combination semantics are covered by API regressions."),
    "LEFT": ("Tool verify", "Tool verify", [], "Cardinal direction constant; combination semantics are covered by API regressions."),
    "RIGHT": ("Tool verify", "Tool verify", [], "Cardinal direction constant; combination semantics are covered by API regressions."),
    "FRONT": ("Tool verify", "Tool verify", [], "Cardinal direction constant; combination semantics are covered by API regressions."),
    "BACK": ("Tool verify", "Tool verify", [], "Cardinal direction constant; combination semantics are covered by API regressions."),
    "up": ("Tool test", "Tool test", [], "BOSL2-style cardinal offset helper; Python-level arithmetic qualification is appropriate."),
    "down": ("Tool test", "Tool test", [], "BOSL2-style cardinal offset helper; Python-level arithmetic qualification is appropriate."),
    "left": ("Tool test", "Tool test", [], "BOSL2-style cardinal offset helper; Python-level arithmetic qualification is appropriate."),
    "right": ("Tool test", "Tool test", [], "BOSL2-style cardinal offset helper; Python-level arithmetic qualification is appropriate."),
    "front": ("Tool test", "Tool test", [], "BOSL2-style cardinal offset helper; Python-level arithmetic qualification is appropriate."),
    "back": ("Tool test", "Tool test", [], "BOSL2-style cardinal offset helper; Python-level arithmetic qualification is appropriate."),
    "half": ("Tool test", "Tool test", [], "Numeric/symbolic geometry helper; Python-level arithmetic qualification is appropriate."),
    "midpoint": ("Tool test", "Tool test", [], "Numeric/symbolic geometry helper; Python-level arithmetic qualification is appropriate."),
    "pv": ("Tool test", "Tool test", [], "Build-time numeric extraction/validation helper; native coverage is not appropriate."),
    "Sketch": ("Visual", "Visual", ["anchored-holes", "circle-negative-extrude", "rounded-rectangle-sketch", "xz-anchor", "bracket", "sheet-fold"], "Explicit Sketch is visual-qualified for normal solid profiles and as the source of a native sheet-metal blank; Text2D remains a capability-level gap."),
    "compile_model": ("Tool verify", "Tool verify", ["simple-box"], "Compiler entry point is a command-contract API; simple-box provides a concrete generated-command fixture."),
    "run_script": ("Tool verify", "Tool verify", ["simple-box"], "Runner entry point is exercised by the concrete simple-box command fixture and the wider qualification suite."),
    "component": ("Visual", "Visual", ["components", "parameter-scope"], "Reusable definitions/occurrences and component-parameter semantics are native-qualified."),
    "assembly": ("Visual", "Visual", ["assembly-decorator"], "Imported @assembly subassembly construction is command-, native- and visual-qualified."),
    "ModelParameterWarning": ("Tool test", "Tool test", [], "Warning contract belongs to Python-level qualification."),
    "ModelError": ("Tool test", "Tool test", [], "Compiler validation/error contract belongs to Python-level qualification."),
}


CAPABILITY_COVERAGE = [
    ("Primitive objects", "Box", "Visual", "Visual", ["simple-box"], "Native parameterized box baseline."),
    ("Primitive objects", "Cylinder(axis=Axis.X/Y/Z)", "Visual", "Visual", ["primitive-csg"], "Principal-axis native cylinder lowering passed native build, measurement and visual qualification."),
    ("Primitive objects", "Sphere", "Visual", "Visual", ["primitive-csg"], "Sphere passed native build, measurement and visual qualification."),
    ("Primitive objects", "Cone / frustum", "Tool verify", "Tool verify", [], "Public native solid.cone lowering is covered by the shared primitive matrix and pinned command contract; add a dedicated native visual qualification case for visual."),
    ("Primitive objects", "Torus", "Visual", "GAP", [], "Not yet exposed through the public Forge API."),
    ("Primitive CSG", "union / difference / intersection", "Visual", "Visual", ["primitive-csg"], "All three Boolean operators passed native SolidCraft qualification."),
    ("Shape transforms", "Shape.move(x,y,z)", "Visual", "Visual", ["primitive-csg"], "Translated primitive passed native SolidCraft qualification."),
    ("Shape transforms", "General arbitrary primitive rotation", "Visual", "GAP", [], "Principal Cylinder axes are native; arbitrary primitive rotation remains a separate transform capability."),
    ("Profiles", "with Sketch(...): Circle2D; sketch.extrude()", "Visual", "Visual", ["circle-negative-extrude"], "Explicit circle Sketch compiles to a native Sketch plus ExtrudeFeature and is measured/visually qualified."),
    ("Profiles", "Sketch.extrude(+d / -d / d, sym=True)", "Visual", "Visual", ["circle-negative-extrude", "bracket"], "Signed distance selects positive/negative extrusion; sym=True selects symmetric extrusion. Native direction and bounds remain qualified."),
    ("Features", "fillet()", "Visual", "Visual", ["four-corner-l", "eight-corner-brackets", "eight-flightcase-corners"], "Basic vertical-edge fillet is command-, native- and visual-qualified; richer edge-selection modes remain separate gaps."),
    ("Features", "Shape.rectangular_pattern()", "Visual", "Visual", ["rectangular-pattern"], "Native SolidCraft rectangular History pattern passed command, build, measured geometry and visual qualification."),
    ("Features", "Sketch.sheet_metal()", "Visual", "Visual", ["sheet-fold"], "Native base-sheet creation is qualified from flat Sketch through formed body, visual evidence and recovered flat pattern."),
    ("Features", "Shape.fold()", "Visual", "Visual", ["sheet-fold"], "Native sheet fold is qualified with formed geometry, feature history and flat-pattern bend metadata."),
    ("Features", "chamfer()", "Visual", "GAP", [], "Add profile-edge and explicit pick cases."),
    ("Features", "shell()", "Visual", "GAP", [], "Add open-face shell measurement."),
    ("Features", "with_material()", "Geometry", "Visual", ["xz-anchor"], "Material creation/assignment runs natively; add explicit material assertions if needed."),
    ("Features", "directional Hole.at()", "Visual", "Visual", ["hole-family"], "All four qualified Hole-family features use explicit -Z native direction and pass native geometry checks."),
    ("Features", "CounterboreHole.at()", "Visual", "Visual", ["hole-family"], "Native counterbore recess is qualified independently from the main bore."),
    ("Features", "CountersinkHole.at()", "Visual", "Visual", ["hole-family"], "Native 90 degree countersink is qualified with conical geometry evidence."),
    ("Features", "ThreadedHole.at()", "Visual", "Visual", ["hole-family"], "Native M6 thread metadata and modeled thread geometry are qualified; references independently prove the tap-drill envelope."),
    ("Plastic features", "Lip.at()/attach()", "Visual", "GAP", [], "Dedicated native plastic fixture required."),
    ("Plastic features", "SnapFit.at()/attach()", "Visual", "GAP", [], "Dedicated native plastic fixture required."),
    ("Plastic features", "Boss.attach()", "Visual", "Tool verify", [], "Command-level coverage remains; add a dedicated native Boss qualification fixture."),
    ("Plastic features", "Boss.at() / directional Boss", "Visual", "GAP", [], "Explicit placement/direction variants still need a dedicated native fixture."),
    ("Plastic features", "Rest.at()/attach()", "Visual", "GAP", [], "Dedicated native plastic fixture required."),
    ("Explicit Sketch", "Sketch.add(Circle2D)/extrude()", "Visual", "Visual", ["circle-negative-extrude"], "Named explicit circle sketch persists as its own native Sketch plus ExtrudeFeature and passes visual regression."),
    ("Explicit Sketch", "Sketch.add(RoundedRectangle2D)/extrude()", "Visual", "Visual", ["rounded-rectangle-sketch"], "Saved native sketch has eight curves, one profile and four cylindrical corner faces after join extrusion."),
    ("Explicit Sketch", "Native Slot family", "Visual", "Visual", ["slot-family"], "All five SolidCraft Slot construction methods lower one-to-one to their native sketch.slot.* commands and are qualified together in one sketch."),
    ("Explicit Sketch", "Rectangle2D in Sketch / extrude()", "Visual", "Visual", ["anchored-holes"], "Rectangle2D authored in an explicit Sketch is native-qualified."),
    ("Explicit Sketch", "Sketch.add(..., anchor=CENTER)", "Visual", "Visual", ["anchored-holes", "rounded-rectangle-sketch"], "Dimension-defined profiles are centred semantically; offset is reserved for deliberate local displacement."),
    ("Explicit Sketch", "Text2D in Sketch / extrude()", "Visual", "GAP", [], "Text2D explicit-sketch path still needs dedicated native coverage."),
    ("Occurrences", "Placement / absolute at()", "Visual", "Tool verify", [], "Public placement state is separated from native lowering; numeric extra occurrences lower directly through occurrence.copy translate. Native identity/replay qualification remains required."),
    ("Occurrences", "parameter-driven Placement / occurrence.move lowering", "Saved design", "Saved design", ["four-corner-l"], "Symbolic Placement lowers to replay-safe occurrence.move values and follows saved-design frame dimension changes."),
    ("Occurrences", "copy + Placement rotation", "Visual", "Visual", ["eight-flightcase-corners"], "Repeated copies with absolute 3D Placement and rotation are native- and visually qualified on all eight case corners."),
    ("Occurrences", "group()", "Visual", "Visual", ["group-hierarchy"], "Native top/flat BOM inspection proves the named subassembly hierarchy and repeated child occurrences."),
    ("Assemblies", "rigid attach()", "Visual", "Visual", ["components"], "Native rigid relationship."),
    ("Assemblies", "@assembly imported subassembly", "Visual", "Visual", ["assembly-decorator"], "An imported @assembly factory returns reusable occurrences that compile and build natively."),
    ("Assemblies", "gap", "Saved design", "Visual", ["parametric-attach"], "Saved-design mutation qualified."),
    ("Assemblies", "local planar offset=(u,v)", "Saved design", "Visual", ["parametric-offset"], "Current semantics explicitly local to joint frame."),
    ("Assemblies", "angle", "Visual", "Visual", ["attach-angle"], "A non-square child is quarter-turned by the native rigid-joint angle and verified by bounds plus visual regression."),
    ("Assemblies", "as_built=True", "Visual", "Tool verify", [], "Command-level tests cover joint.as_built, but no dedicated qualification case currently proves both native and visual behaviour."),
    ("Assemblies", "standard face anchors", "Saved design", "Visual", ["parametric-anchor"], "Parent topology mutation qualified."),
    ("Assemblies", "standard corner anchors", "Saved design", "Visual", ["corner-anchor", "xz-anchor"], "Width/height mutation and mirrored corners qualified."),
    ("Assemblies", "eight profiles as two per vertical side corner", "Visual", "Visual", ["eight-corner-brackets"], "The 4-profile baseline is duplicated in Z so each rounded vertical side corner has one lower and one upper angle profile."),
    ("Assemblies", "four centred vertical side-corner L-profiles", "Visual", "Visual", ["four-corner-l"], "One neutral vertical angle profile wraps each rounded side corner and is centred in height through symbolic native joint placement."),
    ("Assemblies", "four-profile placement follows parent width/depth", "Saved design", "Saved design", ["four-corner-l"], "Saved-design 120x80 -> 160x120 mutation moves all four XY side corners while the fixed-height profiles remain centred vertically."),
    ("Assemblies", "AnchorFrame", "Visual", "Tool verify", ["anchor-topology-mutation"], "A real fixture exercises AnchorFrame as the child reference at command-contract level; arbitrary oriented-frame native qualification remains open."),
    ("Assemblies", "AnchorTopology", "Saved design", "Saved design", ["anchor-topology-mutation"], "A fixed explicit topology pick follows the selected parent corner after native saved-design resize."),
    ("Assemblies", "assembly.with_anchor()/anchor()", "Saved design", "Saved design", ["assembly-owned-anchor"], "Assembly-owned semantic names lower to ordinary native topology-backed relationships and remain associative after saved-design mutation."),
    ("Parameters", "implicit component parameters and inherited bindings", "Saved design", "Saved design", ["parameter-scope"], "Native SolidCraft mutation proves local independence, shared bindings and derived expressions."),
    ("Parameters", "child dimensions derived from parent geometry", "Saved design", "Saved design", ["parent-derived-child-size"], "A reusable child keeps width/depth expressions derived from parent parameters and rebuilds natively after saved-design mutation."),
    ("CLI", "--out command generation", "Tool verify", "Tool verify", ["simple-box"], "The simple-box fixture provides concrete command-generation evidence; the wider CI suite repeats the same path."),
    ("CLI", "native solidcraft-cli run/eval/snapshot", "Visual", "Visual", ["simple-box"], f"Native run/eval/snapshot is exercised by the qualification cases against SolidCraft {TESTED_SOLIDCRAFT_VERSION}; simple-box is the concrete baseline link."),
    ("CLI", "live --connect / replay", "Tool verify", "Tool test", [], "Transport/argument behavior should be tested separately from headless geometry."),
]


def _coverage_rows():
    for name, (target, current, cases, note) in EXPORT_COVERAGE.items():
        yield f"export {name}", target, current, cases, note
    for _group, capability, target, current, cases, note in CAPABILITY_COVERAGE:
        yield f"capability {capability}", target, current, cases, note


COVERAGE_ORDER = {
    "Tool test": 1,
    "Tool verify": 2,
    "Model verify": 3,
    "Geometry": 4,
    "Saved design": 5,
    "Visual": 6,
}
RESULT_CHECK = {
    "Tool verify": "tool_verify",
    "Model verify": "model_verify",
    "Geometry": "geometry",
    "Saved design": "saved_design",
    "Visual": "visual",
}


def coverage_rank(value):
    """Return the ordered semantic coverage rank, or None for GAP/invalid."""

    return COVERAGE_ORDER.get(value)

def validate_coverage_cases(qualification_cases):
    """Reject stale case links and impossible semantic coverage claims."""
    case_by_slug = {case["slug"]: case for case in qualification_cases}
    errors = []
    for label, _target, current, cases, _note in _coverage_rows():
        unknown = [slug for slug in cases if slug not in case_by_slug]
        if unknown:
            errors.append(f"{label}: unknown qualification case(s): {', '.join(unknown)}")
            continue

        if current == "GAP":
            if cases:
                errors.append(f"{label}: GAP rows cannot claim qualification cases")
            continue

        level = coverage_rank(current)
        if level is None:
            errors.append(f"{label}: invalid current level {current!r}")
            continue

        if level >= 3 and not cases:
            errors.append(
                f"{label}: {current} requires at least one concrete qualification case"
            )

        if level == 5:
            non_mutation = [
                slug
                for slug in cases
                if not case_by_slug[slug].get("saved_design_required", False)
            ]
            if non_mutation:
                errors.append(
                    f"{label}: saved-design evidence must use mutation cases, not "
                    + ", ".join(non_mutation)
                )

    if errors:
        raise ValueError("Invalid qualification coverage:\n- " + "\n- ".join(errors))


def validate_coverage_results(qualification_manifest):
    """Reject coverage claims not proven by their linked item results."""
    errors = []
    cases = qualification_manifest["cases"]
    for label, _target, current, evidence_cases, _note in _coverage_rows():
        check = RESULT_CHECK.get(current)
        if check is None or not evidence_cases:
            continue
        for slug in evidence_cases:
            case = cases.get(slug)
            if case is None:
                errors.append(f"{label}: result for {slug} is missing")
                continue
            status = case.get("checks", {}).get(check, {}).get("status")
            if status != "pass":
                errors.append(
                    f"{label}: claims {current} from {slug}, "
                    f"but {check} is {status!r}"
                )

    if errors:
        raise ValueError("Coverage exceeds qualification evidence:\n- " + "\n- ".join(errors))


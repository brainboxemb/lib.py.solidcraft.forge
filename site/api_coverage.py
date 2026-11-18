"""Declared qualification coverage for the public SCPF surface.

The goal is not to pretend every symbol needs a native screenshot.  Each row
declares the appropriate target qualification level for that kind of API and
the highest dedicated coverage currently available.
"""

from scpf.version import TESTED_SOLIDCRAFT_VERSION


EXPORT_COVERAGE = {
    "Box": ("Q6", "Q6", ["simple-box"], "Native primitive and parameter baseline."),
    "Cylinder": ("Q6", "Q6", ["primitive-csg"], f"Native principal-axis Cylinder is qualified with explicit Axis.X in SolidCraft {TESTED_SOLIDCRAFT_VERSION}; Axis.Y/Z use the same primitive field."),
    "Cone": ("Q2", "Q2", [], f"Public Cone/frustum semantics, parameter preservation and CSG combinations are covered by the shared geometry contract matrix; the pinned SolidCraft {TESTED_SOLIDCRAFT_VERSION} command snapshot proves the native solid.cone contract. A dedicated Q6 visual fixture remains separate capability work."),
    "Sphere": ("Q6", "Q6", ["primitive-csg"], f"Primitive CSG creation is native-qualified in SolidCraft {TESTED_SOLIDCRAFT_VERSION}."),
    "Hole": ("Q6", "Q6", ["hole-family", "anchored-holes"], "Simple native Hole.at() is qualified directly by hole-family; anchored-holes separately qualifies face-relative repeated placement."),
    "CounterboreHole": ("Q6", "Q6", ["hole-family"], "Native cylindrical counterbore intent is command-, geometry- and visual-qualified."),
    "CountersinkHole": ("Q6", "Q6", ["hole-family"], "Native conical countersink intent is command-, geometry- and visual-qualified."),
    "ThreadedHole": ("Q6", "Q6", ["hole-family"], "Native M6 tapped-hole metadata and modeled-thread intent are qualified by the Hole-family fixture."),
    "Lip": ("Q6", "GAP", [], "Plastic feature needs a dedicated native fixture."),
    "SnapFit": ("Q6", "GAP", [], "Plastic feature needs a dedicated native fixture."),
    "Boss": ("Q6", "Q2", [], "Boss.attach() retains command-level unit coverage; a dedicated native qualification case is still required."),
    "Rest": ("Q6", "GAP", [], "Plastic feature needs a dedicated native fixture."),
    "Depth": ("Q2", "Q6", ["anchored-holes"], "THROUGH_ALL is exercised by the native hole fixture."),
    "Rectangle2D": ("Q6", "Q6", ["anchored-holes"], "Rectangle2D is authored inside an explicit Sketch and native-qualified through the rectangle sketch/extrude path."),
    "RoundedRectangle2D": ("Q6", "Q6", ["rounded-rectangle-sketch"], "Explicit named Sketch lowering preserves one solved eight-curve rounded profile with four true arc corners."),
    "SlotCenterToCenter2D": ("Q6", "Q6", ["slot-family"], "Native center-to-center Slot constructor is qualified directly through sketch.slot.center_to_center."),
    "SlotOverall2D": ("Q6", "Q6", ["slot-family"], "Native overall-length Slot constructor is qualified directly through sketch.slot.overall."),
    "SlotCenterPoint2D": ("Q6", "Q6", ["slot-family"], "Native center-point Slot constructor is qualified directly through sketch.slot.center_point."),
    "SlotArcThreePoint2D": ("Q6", "Q6", ["slot-family"], "Native three-point arc Slot constructor is qualified directly through sketch.slot.arc_three_point."),
    "SlotArcCenter2D": ("Q6", "Q6", ["slot-family"], "Native center-arc Slot constructor is qualified directly through sketch.slot.arc_center."),
    "Circle2D": ("Q6", "Q6", ["circle-negative-extrude"], "Circle2D is native- and visual-qualified inside an explicit Sketch scope with negative extrusion."),
    "Polygon2D": ("Q6", "Q6", ["xz-anchor", "bracket"], "XZ Polygon2D authored inside explicit Sketch scopes is native-qualified for symmetric and positive extrusion."),
    "Shape": ("Q2", "Q6", ["simple-box", "anchored-holes", "bracket"], "Core composition node is exercised by many native cases."),
    "Parameter": ("Q5", "Q5", ["parameter-scope", "parent-derived-child-size", "parametric-attach", "parametric-offset", "parametric-anchor"], "Component-local parameters, inherited bindings and parent-derived child expressions are qualified through saved-design mutation."),
    "Placement": ("Q6", "Q6", ["components", "four-corner-l"], "Numeric Placement is native-qualified by components; symbolic parameter-driven Placement and replay-safe occurrence.move lowering are mutation-qualified by four-corner-l."),
    "Edges": ("Q6", "Q6", ["four-corner-l", "eight-corner-brackets", "eight-flightcase-corners"], "Edges.VERTICAL is native-qualified through rounded reference frames; profile-derived and explicit edge selections still need separate coverage."),
    "Faces": ("Q6", "Q6", ["anchored-holes"], "TOP face placement is qualified; other face selections need capability coverage."),
    "Anchor": ("Q6", "Q6", ["parametric-anchor", "corner-anchor", "xz-anchor"], "Face and corner selectors are qualified by real native anchor cases; AnchorFrame is tracked separately."),
    "AnchorFrame": ("Q6", "Q2", ["anchor-topology-mutation"], "The public AnchorFrame command path is covered with a real qualification fixture, but arbitrary oriented-frame native/Q6 coverage is still missing."),
    "AnchorTopology": ("Q5", "Q5", ["anchor-topology-mutation"], "Explicit edge/on/corner topology is native-qualified through saved-design parent resize; explicitly rotated occurrences remain unsupported."),
    "Axis": ("Q2", "Q6", ["anchored-holes", "primitive-csg"], "Axis values are exercised by linear repetition and principal-axis Cylinder geometry."),
    "X": ("Q2", "Q1", [], "Covered as an occurrence-rotation and parent-bound token; dedicated command-contract coverage remains."),
    "Y": ("Q2", "Q1", [], "Covered as an occurrence-rotation and parent-bound token; dedicated command-contract coverage remains."),
    "Z": ("Q2", "Q1", [], "Covered as an occurrence-rotation token; dedicated command-contract coverage remains."),
    "CENTER": ("Q6", "Q6", ["anchored-holes", "rounded-rectangle-sketch"], "Semantic Sketch profile centre; command-level centering and native centred Rectangle2D/RoundedRectangle2D geometry are qualified."),
    "TOP": ("Q2", "Q2", [], "Cardinal direction constant; combination semantics are covered by API regressions."),
    "BOTTOM": ("Q2", "Q2", [], "Cardinal direction constant; combination semantics are covered by API regressions."),
    "LEFT": ("Q2", "Q2", [], "Cardinal direction constant; combination semantics are covered by API regressions."),
    "RIGHT": ("Q2", "Q2", [], "Cardinal direction constant; combination semantics are covered by API regressions."),
    "FRONT": ("Q2", "Q2", [], "Cardinal direction constant; combination semantics are covered by API regressions."),
    "BACK": ("Q2", "Q2", [], "Cardinal direction constant; combination semantics are covered by API regressions."),
    "up": ("Q1", "Q1", [], "BOSL2-style cardinal offset helper; Python-level arithmetic qualification is appropriate."),
    "down": ("Q1", "Q1", [], "BOSL2-style cardinal offset helper; Python-level arithmetic qualification is appropriate."),
    "left": ("Q1", "Q1", [], "BOSL2-style cardinal offset helper; Python-level arithmetic qualification is appropriate."),
    "right": ("Q1", "Q1", [], "BOSL2-style cardinal offset helper; Python-level arithmetic qualification is appropriate."),
    "front": ("Q1", "Q1", [], "BOSL2-style cardinal offset helper; Python-level arithmetic qualification is appropriate."),
    "back": ("Q1", "Q1", [], "BOSL2-style cardinal offset helper; Python-level arithmetic qualification is appropriate."),
    "half": ("Q1", "Q1", [], "Numeric/symbolic geometry helper; Python-level arithmetic qualification is appropriate."),
    "midpoint": ("Q1", "Q1", [], "Numeric/symbolic geometry helper; Python-level arithmetic qualification is appropriate."),
    "pv": ("Q1", "Q1", [], "Build-time numeric extraction/validation helper; native coverage is not appropriate."),
    "Sketch": ("Q6", "Q6", ["anchored-holes", "circle-negative-extrude", "rounded-rectangle-sketch", "xz-anchor", "bracket"], "Explicit Sketch is Q6-qualified with Rectangle2D, Circle2D, Polygon2D and RoundedRectangle2D; Text2D remains a capability-level gap."),
    "compile_model": ("Q2", "Q2", ["simple-box"], "Compiler entry point is a command-contract API; simple-box provides a concrete generated-command fixture."),
    "run_script": ("Q2", "Q2", ["simple-box"], "Runner entry point is exercised by the concrete simple-box command fixture and the wider qualification suite."),
    "component": ("Q6", "Q6", ["components", "parameter-scope"], "Reusable definitions/occurrences and component-parameter semantics are native-qualified."),
    "assembly": ("Q6", "Q6", ["assembly-decorator"], "Imported @assembly subassembly construction is command-, native- and visual-qualified."),
    "ModelParameterWarning": ("Q1", "Q1", [], "Warning contract belongs to Python-level qualification."),
    "ModelError": ("Q1", "Q1", [], "Compiler validation/error contract belongs to Python-level qualification."),
}


CAPABILITY_COVERAGE = [
    ("Primitive objects", "Box", "Q6", "Q6", ["simple-box"], "Native parameterized box baseline."),
    ("Primitive objects", "Cylinder(axis=Axis.X/Y/Z)", "Q6", "Q6", ["primitive-csg"], "Principal-axis native cylinder lowering passed native build, measurement and visual qualification."),
    ("Primitive objects", "Sphere", "Q6", "Q6", ["primitive-csg"], "Sphere passed native build, measurement and visual qualification."),
    ("Primitive objects", "Cone / frustum", "Q2", "Q2", [], "Public native solid.cone lowering is covered by the shared primitive matrix and pinned command contract; add a dedicated native visual qualification case for Q6."),
    ("Primitive objects", "Torus", "Q6", "GAP", [], "Not yet exposed through the public Forge API."),
    ("Primitive CSG", "union / difference / intersection", "Q6", "Q6", ["primitive-csg"], "All three Boolean operators passed native SolidCraft qualification."),
    ("Shape transforms", "Shape.move(x,y,z)", "Q6", "Q6", ["primitive-csg"], "Translated primitive passed native SolidCraft qualification."),
    ("Shape transforms", "General arbitrary primitive rotation", "Q6", "GAP", [], "Principal Cylinder axes are native; arbitrary primitive rotation remains a separate transform capability."),
    ("Profiles", "with Sketch(...): Circle2D; sketch.extrude()", "Q6", "Q6", ["circle-negative-extrude"], "Explicit circle Sketch compiles to a native Sketch plus ExtrudeFeature and is measured/visually qualified."),
    ("Profiles", "Sketch.extrude(+d / -d / d, sym=True)", "Q6", "Q6", ["circle-negative-extrude", "bracket"], "Signed distance selects positive/negative extrusion; sym=True selects symmetric extrusion. Native direction and bounds remain qualified."),
    ("Features", "fillet()", "Q6", "Q6", ["four-corner-l", "eight-corner-brackets", "eight-flightcase-corners"], "Basic vertical-edge fillet is command-, native- and visual-qualified; richer edge-selection modes remain separate gaps."),
    ("Features", "Shape.repeat_linear()", "Q2", "Q2", ["anchored-holes"], "Forge-side primitive repetition retained under an explicit non-Pattern name; it is not a SolidCraft History pattern."),
    ("Features", "Shape.rectangular_pattern()", "Q6", "Q6", ["rectangular-pattern"], "Native SolidCraft rectangular History pattern passed command, build, measured geometry and visual qualification."),
    ("Features", "chamfer()", "Q6", "GAP", [], "Add profile-edge and explicit pick cases."),
    ("Features", "shell()", "Q6", "GAP", [], "Add open-face shell measurement."),
    ("Features", "with_material()", "Q4", "Q6", ["xz-anchor"], "Material creation/assignment runs natively; add explicit material assertions if needed."),
    ("Features", "directional Hole.at()", "Q6", "Q6", ["hole-family"], "All four qualified Hole-family features use explicit -Z native direction and pass native geometry checks."),
    ("Features", "CounterboreHole.at()", "Q6", "Q6", ["hole-family"], "Native counterbore recess is qualified independently from the main bore."),
    ("Features", "CountersinkHole.at()", "Q6", "Q6", ["hole-family"], "Native 90 degree countersink is qualified with conical geometry evidence."),
    ("Features", "ThreadedHole.at()", "Q6", "Q6", ["hole-family"], "Native M6 thread metadata and modeled thread geometry are qualified; references independently prove the tap-drill envelope."),
    ("Plastic features", "Lip.at()/attach()", "Q6", "GAP", [], "Dedicated native plastic fixture required."),
    ("Plastic features", "SnapFit.at()/attach()", "Q6", "GAP", [], "Dedicated native plastic fixture required."),
    ("Plastic features", "Boss.attach()", "Q6", "Q2", [], "Command-level coverage remains; add a dedicated native Boss qualification fixture."),
    ("Plastic features", "Boss.at() / directional Boss", "Q6", "GAP", [], "Explicit placement/direction variants still need a dedicated native fixture."),
    ("Plastic features", "Rest.at()/attach()", "Q6", "GAP", [], "Dedicated native plastic fixture required."),
    ("Explicit Sketch", "Sketch.add(Circle2D)/extrude()", "Q6", "Q6", ["circle-negative-extrude"], "Named explicit circle sketch persists as its own native Sketch plus ExtrudeFeature and passes visual regression."),
    ("Explicit Sketch", "Sketch.add(RoundedRectangle2D)/extrude()", "Q6", "Q6", ["rounded-rectangle-sketch"], "Saved native sketch has eight curves, one profile and four cylindrical corner faces after join extrusion."),
    ("Explicit Sketch", "Native Slot family", "Q6", "Q6", ["slot-family"], "All five SolidCraft Slot construction methods lower one-to-one to their native sketch.slot.* commands and are qualified together in one sketch."),
    ("Explicit Sketch", "Rectangle2D in Sketch / extrude()", "Q6", "Q6", ["anchored-holes"], "Rectangle2D authored in an explicit Sketch is native-qualified."),
    ("Explicit Sketch", "Sketch.add(..., anchor=CENTER)", "Q6", "Q6", ["anchored-holes", "rounded-rectangle-sketch"], "Dimension-defined profiles are centred semantically; offset is reserved for deliberate local displacement."),
    ("Explicit Sketch", "Text2D in Sketch / extrude()", "Q6", "GAP", [], "Text2D explicit-sketch path still needs dedicated native coverage."),
    ("Occurrences", "Placement / absolute at()", "Q6", "Q2", [], "Public placement state is separated from native lowering; numeric extra occurrences lower directly through occurrence.copy translate. Native identity/replay qualification remains required."),
    ("Occurrences", "parameter-driven Placement / occurrence.move lowering", "Q5", "Q5", ["four-corner-l"], "Symbolic Placement lowers to replay-safe occurrence.move values and follows saved-design frame dimension changes."),
    ("Occurrences", "copy + Placement rotation", "Q6", "Q6", ["eight-flightcase-corners"], "Repeated copies with absolute 3D Placement and rotation are native- and visually qualified on all eight case corners."),
    ("Occurrences", "group()", "Q6", "Q6", ["group-hierarchy"], "Native top/flat BOM inspection proves the named subassembly hierarchy and repeated child occurrences."),
    ("Assemblies", "rigid attach()", "Q6", "Q6", ["components"], "Native rigid relationship."),
    ("Assemblies", "@assembly imported subassembly", "Q6", "Q6", ["assembly-decorator"], "An imported @assembly factory returns reusable occurrences that compile and build natively."),
    ("Assemblies", "gap", "Q5", "Q6", ["parametric-attach"], "Saved-design mutation qualified."),
    ("Assemblies", "local planar offset=(u,v)", "Q5", "Q6", ["parametric-offset"], "Current semantics explicitly local to joint frame."),
    ("Assemblies", "angle", "Q6", "Q6", ["attach-angle"], "A non-square child is quarter-turned by the native rigid-joint angle and verified by bounds plus visual regression."),
    ("Assemblies", "as_built=True", "Q6", "Q2", [], "Command-level tests cover joint.as_built, but no dedicated native qualification case currently proves Q3-Q6."),
    ("Assemblies", "standard face anchors", "Q5", "Q6", ["parametric-anchor"], "Parent topology mutation qualified."),
    ("Assemblies", "standard corner anchors", "Q5", "Q6", ["corner-anchor", "xz-anchor"], "Width/height mutation and mirrored corners qualified."),
    ("Assemblies", "eight profiles as two per vertical side corner", "Q6", "Q6", ["eight-corner-brackets"], "The 4-profile baseline is duplicated in Z so each rounded vertical side corner has one lower and one upper angle profile."),
    ("Assemblies", "four centred vertical side-corner L-profiles", "Q6", "Q6", ["four-corner-l"], "One neutral vertical angle profile wraps each rounded side corner and is centred in height through symbolic native joint placement."),
    ("Assemblies", "four-profile placement follows parent width/depth", "Q5", "Q5", ["four-corner-l"], "Saved-design 120x80 -> 160x120 mutation moves all four XY side corners while the fixed-height profiles remain centred vertically."),
    ("Assemblies", "AnchorFrame", "Q6", "Q2", ["anchor-topology-mutation"], "A real fixture exercises AnchorFrame as the child reference at command-contract level; arbitrary oriented-frame native qualification remains open."),
    ("Assemblies", "AnchorTopology", "Q5", "Q5", ["anchor-topology-mutation"], "A fixed explicit topology pick follows the selected parent corner after native saved-design resize."),
    ("Assemblies", "assembly.with_anchor()/anchor()", "Q5", "Q5", ["assembly-owned-anchor"], "Assembly-owned semantic names lower to ordinary native topology-backed relationships and remain associative after saved-design mutation."),
    ("Parameters", "implicit component parameters and inherited bindings", "Q5", "Q5", ["parameter-scope"], "Native SolidCraft mutation proves local independence, shared bindings and derived expressions."),
    ("Parameters", "child dimensions derived from parent geometry", "Q5", "Q5", ["parent-derived-child-size"], "A reusable child keeps width/depth expressions derived from parent parameters and rebuilds natively after saved-design mutation."),
    ("CLI", "--out command generation", "Q2", "Q2", ["simple-box"], "The simple-box fixture provides concrete command-generation evidence; the wider CI suite repeats the same path."),
    ("CLI", "native solidcraft-cli run/eval/snapshot", "Q6", "Q6", ["simple-box"], f"Native run/eval/snapshot is exercised by the qualification cases against SolidCraft {TESTED_SOLIDCRAFT_VERSION}; simple-box is the concrete baseline link."),
    ("CLI", "live --connect / replay", "Q2", "Q1", [], "Transport/argument behavior should be tested separately from headless geometry."),
]


def _coverage_rows():
    for name, (target, current, cases, note) in EXPORT_COVERAGE.items():
        yield f"export {name}", target, current, cases, note
    for _group, capability, target, current, cases, note in CAPABILITY_COVERAGE:
        yield f"capability {capability}", target, current, cases, note


def qualification_number(value):
    if value.startswith("Q") and value[1:].isdigit():
        return int(value[1:])
    return None


def validate_coverage_cases(qualification_cases):
    """Reject stale case links and structurally impossible Q claims."""
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

        level = qualification_number(current)
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
                if not case_by_slug[slug].get("q5_required", False)
            ]
            if non_mutation:
                errors.append(
                    f"{label}: Q5 evidence must use mutation cases, not "
                    + ", ".join(non_mutation)
                )

    if errors:
        raise ValueError("Invalid qualification coverage:\n- " + "\n- ".join(errors))


def validate_coverage_results(qualification_manifest):
    """Reject current Q claims that the linked native results did not PASS."""
    errors = []
    cases = qualification_manifest["cases"]
    for label, _target, current, evidence_cases, _note in _coverage_rows():
        level = qualification_number(current)
        if level is None or not evidence_cases:
            continue
        key = f"q{level}"
        for slug in evidence_cases:
            case = cases.get(slug)
            if case is None:
                errors.append(f"{label}: result for {slug} is missing")
                continue
            status = case.get("levels", {}).get(key, {}).get("status")
            if status != "pass":
                errors.append(
                    f"{label}: claims {current} from {slug}, but {key.upper()} is {status!r}"
                )

    if errors:
        raise ValueError("Coverage exceeds qualification evidence:\n- " + "\n- ".join(errors))


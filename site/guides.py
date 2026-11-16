"""Long-form, source-maintained API guide pages for the library website.

This is educational documentation, not executable API fixtures. Claims about
supported operations must match scpf/scpf/*.py and scpf/tests/*.py.
"""
from html import escape


def code(source):
    return '<pre><code>' + escape(source.strip()) + '</code></pre>'


GUIDES = [
    {
        "slug": "getting-started",
        "title": "Getting started",
        "summary": "From a Python class to editable SolidCraft geometry.",
        "body": """
<h2 id="what">What SCPF does</h2>
<p>SCPF is a Python interface and compiler for <strong>native SolidCraft commands</strong>.
It is not a replacement CAD kernel. You describe a model using ordinary Python;
SolidCraft executes the generated commands and owns the final geometry and
feature history.</p>
<h2 id="install">Install the library</h2>
<p>In the <code>lib.py.solidcraft.forge</code> repository and an active Python environment:</p>
""" + code("""python -m pip install -e ./scpf
python -m unittest discover -s scpf/tests -v""") + """
<h2 id="first-model">Your first model</h2>
<p>Define one class, give it numeric dimensions, and return the body from
<code>build()</code>. No <code>main()</code> or <code>show()</code> is necessary.</p>
""" + code("""from scpf import Box, Edges

class Plate:
    length = 100.0
    width = 60.0
    thickness = 10.0

    def build(self):
        plate = Box(self.length, self.width, self.thickness)
        return plate.fillet(2, edges=Edges.VERTICAL)

Plate()""") + """
<h2 id="run">Compile, inspect, then execute</h2>
<p>Save the model as <code>model.py</code>. Compilation alone does not open SolidCraft.
The JSON is a native command plan, not a mesh or STEP file.</p>
""" + code("""python -m scpf model.py --out output/model.json
python -m json.tool output/model.json""") + """
<p>For a live GUI run, open SolidCraft, enable
<em>Preferences → Assistant → Let AI agents connect</em>, and use:</p>
""" + code("""python -m scpf model.py --connect --new""") + """
<p><code>--new</code> asks SolidCraft to replace the active design with a new,
empty one before the model batch is sent. Leave it off when you deliberately
want to add commands to the current design. Neither form saves the design.
The CAD project also provides a separate native CLI qualification workflow.</p>
<h2 id="next">Where to continue</h2>
<p>Read <a href="../model-objects/">Model objects</a> to understand the difference
between a shape definition and a placed component occurrence. Then read
<a href="../assembly-basics/">From one component to an assembly</a> before building
multi-part models: it explains when to use placement, anchors, relationships and
groups. The <a href="../transformations/">Transformations</a> chapter covers coordinate axes,
rotation and the common “my panel is lying flat” problem.</p>""",
    },
    {
        "slug": "model-objects",
        "title": "Model objects and parameters",
        "summary": "What a class, Shape, component and occurrence mean.",
        "body": """
<h2 id="class">A model is a normal Python class</h2>
<p>Numeric class attributes become editable SolidCraft parameters when SCPF
compiles a plain model class. <code>build()</code> returns geometry. If a file
contains exactly one public class with <code>build()</code>, that class is the
root automatically; no trailing constructor call or launcher file is needed.</p>
""" + code("""from scpf import Box

class Plate:
    length = 100.0
    width = 60.0
    thickness = 10.0

    def build(self):
        return Box(self.length, self.width, self.thickness)""") + """
<p>Run that source file directly with
<code>python -m scpf plate.py --connect</code>. The same rule lets a reusable
component file serve as its standalone model while assemblies import the exact
same class. If a file contains several public model classes, SCPF deliberately
does not guess: finish the script with an explicit call such as
<code>Assembly()</code> to choose the root.</p>
<p>An explicit final call is also how you override root parameters for a
particular run, for example <code>Plate(width=80)</code>. Arithmetic such as
<code>self.length / 2</code> is preserved symbolically for supported
expressions; general Python computations are not automatically made
parametric.</p>
<h2 id="parameter-intent">Parameter intent is visible in the name</h2>
<p>SCPF distinguishes three kinds of numeric class attributes. This keeps a
Python build setting from looking like a native editable CAD parameter.</p>
""" + code("""class Display:
    PANEL_COUNT = 5          # fixed constant
    _panel_pitch = 160.0     # Forge/build-time input
    opening_width = 844.0    # native model parameter""") + """
<table><thead><tr><th>Name</th><th>Meaning</th><th>SolidCraft parameter</th></tr></thead><tbody>
<tr><td><code>UPPER_CASE</code></td><td>Fixed constant</td><td>No</td></tr>
<tr><td><code>_lower_case</code></td><td>Forge/build-time input</td><td>No</td></tr>
<tr><td><code>lower_case</code></td><td>Editable model parameter</td><td>Yes</td></tr>
</tbody></table>
<p>If a public lower-case parameter is consumed only as a concrete Python
value—for example through <code>pv()</code>—Forge emits a
<code>ModelParameterWarning</code>. The same warning is emitted when a
parameter remains native in some geometry but is also flattened into concrete
occurrence placement. Such a parameter is only partly associative: editing it
in SolidCraft would update only part of the model. Keep
<code>Placement</code> coordinates symbolic or rename an intentionally
build-time input with a leading underscore.</p>
<h2 id="shared-parameters">Share one model parameter across child components</h2>
<p>Passing a parent parameter into several component inputs keeps one native
SolidCraft parameter instead of creating component-specific duplicates.</p>
""" + code("""bottom = BottomBoard(corner_radius=self.corner_radius)
roof = RoofBoard(corner_radius=self.corner_radius)
bracket = Bracket(
    bracket_width=self.bracket_width,
    inside_corner_radius=self.corner_radius,
)""") + """
<p>Here the wooden fillets and bracket inside fillet all depend on the same
<code>corner_radius</code>. Passing the parent parameter into the child input
reuses that existing native dependency rather than creating a duplicate child
parameter.</p>
<p>Reusable component defaults stay fixed unless they are explicitly
published with <code>include=</code>. Parent Parameters/Expressions passed into
child inputs always stay symbolic and reuse the existing parent dependency.</p>
""" + code("""Bracket = component(
    CornerBracket,
    include=("inside_corner_radius",),
)

# Or publish all public defaults explicitly:
FullyEditableBracket = component(CornerBracket, include="*")""") + """
<p>This publication rule is recorded in
<a href="../../changes/0003-explicit-component-parameter-publication/">change 0003</a>.</p>
<h2 id="shape">Shape versus component occurrence</h2>
<p><strong>Shape</strong> describes geometry or a feature expression
(<code>Box</code>, <code>Hole</code>, an extrusion). A <strong>component
occurrence</strong> is one placed instance of a shared, editable model definition.
Do not confuse a new occurrence with a new feature history.</p>
""" + code("""from scpf import Box, Placement, component

class Block:
    def build(self):
        return Box(40, 20, 10)

BlockComponent = component(Block)
first = BlockComponent(placement=Placement(x=-25))
second = first.copy(placement=Placement(x=25))
assembly = first + second""") + """
<p>The two occurrences share the same <code>Block</code> definition.
<code>Placement</code> is occurrence creation metadata: XYZ is absolute in the
parent coordinate frame and optional rotation adds orientation. The component
definition never receives <code>placement</code> as a model parameter.</p>
<h2 id="groups">Groups are actual native parent components</h2>
""" + code("""blocks = (first + second).group("Blocks")""") + """
<p>Grouping changes the browser hierarchy, not the geometry's orientation.
At present one shared definition cannot be split among different groups.</p>
<h2 id="limits">Important boundaries</h2>
<p>Associative attachment is supported for a limited set of rectangular
component faces. General mates, arbitrary face queries and rotational
constraints are not implemented as a complete assembly solver.</p>""",
    },
    {
        "slug": "assembly-basics",
        "title": "From one component to an assembly",
        "summary": "When to use a Shape, component, occurrence, anchor, relationship or group.",
        "body": """
<h2 id="mental-model">Start with the mental model</h2>
<p>Forge separates <strong>geometry</strong> from <strong>physical parts</strong>
and from <strong>relationships between parts</strong>. Most assembly code becomes
much easier once those three levels are kept separate.</p>
<table><thead><tr><th>You mean…</th><th>Forge concept</th><th>SolidCraft result</th></tr></thead><tbody>
<tr><td>Geometry inside one part</td><td><code>Shape</code></td><td>Native geometry/features in one definition</td></tr>
<tr><td>One reusable physical part</td><td><code>@component</code> class</td><td>Reusable component definition</td></tr>
<tr><td>Where/how one occurrence stands</td><td><code>placement=Placement(...)</code></td><td>Occurrence placement</td></tr>
<tr><td>One placed copy of that part</td><td><code>Block()</code> / <code>copy()</code></td><td>Component occurrence</td></tr>
<tr><td>Several parts collected together</td><td><code>a + b</code></td><td>Assembly containing occurrences</td></tr>
<tr><td>One part depends on another</td><td><code>attach()</code></td><td>Native SolidCraft assembly relationship/joint</td></tr>
<tr><td>A named mounting reference</td><td><code>Anchor</code>, <code>AnchorFrame</code>, <code>AnchorTopology</code></td><td>Reference used by that relationship</td></tr>
<tr><td>Browser/subassembly organisation</td><td><code>group()</code></td><td>Nested native component</td></tr>
</tbody></table>

<h2 id="simple-component">1. A component means one physical part</h2>
<p>A component is <strong>not</strong> limited to one primitive. It is the
definition of one physical manufactured item. Its <code>build()</code> may
contain several primitives, sketches, holes, bosses, fillets and other features
as long as they together describe that one part.</p>
""" + code("""from scpf import Box, Cylinder, component

@component
class MountingPlate:
    width = 80.0
    depth = 50.0
    thickness = 5.0

    def build(self):
        plate = Box(self.width, self.depth, self.thickness)
        boss = Cylinder(d=16, h=12).at(0, 0, self.thickness)
        return plate + boss""") + """
<p>The plate and cylindrical boss are geometry/features inside
<strong>one component</strong>. They do not need an assembly joint because
they are not separate physical parts.</p>
<div class="notice"><strong>Physical-part test:</strong> if the boss is machined,
printed or moulded as part of the plate, keep it inside one component. If it is
actually a separate brass insert pressed into the plate, make a second component
and relate the two occurrences in an assembly.</div>
<p><code>MountingPlate</code> is the reusable definition. Calling
<code>MountingPlate()</code> creates one occurrence; <code>copy()</code>
creates another occurrence of the same definition without duplicating the
feature history.</p>

<h2 id="collection">2. Put components in one assembly</h2>
""" + code("""first = Block(placement=Placement(x=-30))
second = first.copy(placement=Placement(x=30))

assembly = first + second""") + """
<p>Here <code>first + second</code> means “these two component occurrences
belong to one assembly”. It does <strong>not</strong> Boolean-union their solids.</p>
<div class="notice"><strong>Same operator, different level:</strong>
<code>Shape + Shape</code> describes supported geometric union;
<code>occurrence + occurrence</code> builds an assembly of physical parts.</div>
<p><code>placement=Placement(...)</code> declares the pose when an occurrence
is created or copied. It does not create a mechanical relationship; use
<code>attach()</code> when another occurrence owns the relationship.</p>

<h2 id="reusable-assembly">3. Use @assembly when the composition itself is reusable</h2>
<p>You do not need <code>@assembly</code> merely because a script contains
several components. Use it when the <em>composition itself</em> is a reusable
model object that you want to import or instantiate as a subassembly.</p>
""" + code("""from scpf import Anchor, assembly

@assembly
class BlockPair:
    def build(self):
        left = Block()
        right = Block().attach(
            left,
            parent=Anchor.RIGHT,
            child=Anchor.LEFT,
        )
        return left + right

pair = BlockPair()""") + """
<p>The component definitions remain the physical parts. <code>BlockPair</code>
describes how those occurrences are composed. This is different from
<code>group()</code>: an assembly expresses the model composition; grouping
controls the native nested hierarchy/browser unit.</p>

<h2 id="relationship">4. Use attach() when the relationship is the intent</h2>
<p>If the real rule is “the left side of this part belongs on the right side of
that part”, encode that relationship instead of calculating a replacement XYZ
coordinate yourself.</p>
""" + code("""from scpf import Anchor

left = Block()
right = Block().attach(
    left,
    parent=Anchor.RIGHT,
    child=Anchor.LEFT,
)

assembly = left + right""") + """
<p>Forge records an associative attachment between the two occurrences and
lowers that to the native SolidCraft relationship mechanism. The anchors say
<strong>which references are related</strong>; they are not just prettier names
for a hard-coded XYZ point.</p>
<p>This is the important rule: <strong>use an anchor when you need to describe a
relationship or semantic mounting reference</strong>. Do not add anchors to every
component pre-emptively.</p>

<h2 id="anchor-choice">5. Which kind of anchor?</h2>
<table><thead><tr><th>Situation</th><th>Use</th></tr></thead><tbody>
<tr><td>Normal rectangular face/corner is enough</td><td><code>Anchor.LEFT</code>, <code>Anchor.FRONT_TOP_RIGHT</code>, etc.</td></tr>
<tr><td>The reusable part owns a special mounting point and orientation</td><td>Named <code>AnchorFrame</code> returned by the component's <code>anchors()</code></td></tr>
<tr><td>The reference must follow a particular native edge/corner topology</td><td><code>AnchorTopology</code></td></tr>
<tr><td>The reference exists only because of this larger assembly</td><td>Assembly-owned <code>with_anchor()</code>, not an application-specific anchor added to the generic part</td></tr>
</tbody></table>
<p>Start with the simplest standard <code>Anchor</code>. Move to
<code>AnchorFrame</code> or <code>AnchorTopology</code> only when a face/corner
reference cannot express the actual mounting intent.</p>

<h2 id="solidcraft-relations">6. Let SolidCraft own the native relationship</h2>
<p>Forge describes the relationship; SolidCraft owns the resulting native
geometry, occurrence hierarchy and joint data. Forge is not intended to grow a
second general mating solver. That is also why a meaningful
<code>attach()</code> is preferable to Forge inventing increasingly clever
coordinate corrections.</p>
<p><code>offset=(u, v)</code> moves within the attachment plane,
<code>gap</code> is normal distance between references, and <code>angle</code>
is the relative turn around the attachment normal. These are relationship
values, not a replacement global XYZ transform.</p>
<p>There are two useful attachment modes. Normal <code>attach()</code> uses the
chosen references to determine the relationship and placement. Use
<code>attach(..., as_built=True)</code> when both occurrences are already in the
intended pose and SolidCraft should record that existing pose as a fixed
assembly relationship instead of repositioning them.</p>

<h2 id="group">7. A group is organisation, not a relationship</h2>
""" + code("""frame = (left + right).group("Frame")""") + """
<p><code>group("Frame")</code> creates a real nested native component so the
occurrences appear together in the SolidCraft browser hierarchy. Grouping does
not mate, align or rotate the parts and does not replace <code>attach()</code>.</p>
<p>Use a group when the collection itself is a useful named subassembly or
browser unit. Do not create a group merely because two components touch.</p>

<h2 id="decision">A practical decision sequence</h2>
<ol>
<li>Will these features be manufactured as one physical item? Keep them in one component, even if the geometry is complex.</li>
<li>Is something installed or manufactured separately? Give it its own component occurrence.</li>
<li>Do you only need a deliberate occurrence pose? Supply <code>placement=Placement(...)</code> when creating or copying it.</li>
<li>Should one separate part follow another semantically? Use <code>attach()</code> and the simplest suitable anchor.</li>
<li>Is a standard face/corner insufficient? Define an <code>AnchorFrame</code> or topology-backed reference at the level that owns that meaning.</li>
<li>Do several occurrences form a useful named subassembly/browser unit? Then use <code>group()</code>.</li>
</ol>
<p>After this page, the <a href="../components/">Components and assemblies</a>
chapter covers parameter sharing, offsets, custom frames, topology anchors and
assembly-owned datums in detail.</p>""",
    },
    {
        "slug": "geometry",
        "title": "Geometry, sketches and Boolean operations",
        "summary": "Solids, 2D profiles, extrusions and the CSG operators.",
        "body": """
<h2 id="solids">Start with a solid</h2>
<p><code>Box</code>, <code>Cylinder</code> and <code>Sphere</code> are centred
on their geometric CENTER by default. Use <code>anchor=...</code> when a face,
axial end or tangent datum should lie at the origin. For Cylinder the anchor is
resolved after choosing <code>Axis.X</code>, <code>Axis.Y</code> or
<code>Axis.Z</code>; for example LEFT/RIGHT are the axial ends of an X-axis
cylinder and BOTTOM/TOP are the axial ends of a Z-axis cylinder.</p>
""" + code("""from scpf import (
    BOTTOM, FRONT, LEFT, RIGHT,
    Axis, Box, Cylinder, Sphere,
)

plate = Box(80, 50, 8)
board = Box(80, 50, 12).at(
    0, 0, 0,
    anchor=FRONT + BOTTOM,
).fillet(
    4,
    edges=[BOTTOM + LEFT, BOTTOM + RIGHT],
)
pin = Cylinder(d=8, h=20, axis=Axis.Z).at(
    10, 10, 8,
    anchor=BOTTOM,
)
side_pin = Cylinder(d=8, h=20, axis=Axis.X).at(-10, 0, 0)
ball = Sphere(12)

body = Sphere(20) & Box(30, 30, 30)
centered_bore = Cylinder(d=8, h=30, axis=Axis.X).at(body)""") + """
<p><code>at(x, y, z)</code> places CENTER at those coordinates unless another
<code>anchor=...</code> is supplied. Passing another Shape instead uses
shape-relative CENTER-to-CENTER placement. Forge derives the native Box corner,
Cylinder base or Sphere center from the selected datum; callers do not add
manual half-size corrections.</p>
<h2 id="profiles">Draw a 2D profile, then extrude it</h2>
<p>A <code>Rectangle2D</code> is a planar profile rather than a 3D body. 2D geometry is authored inside an explicit <code>Sketch</code> scope. <code>Polygon2D</code> can be created on the XY, XZ or YZ plane.</p>
""" + code("""from scpf import Sketch, Rectangle2D, Polygon2D

with Sketch(plane="XY") as plate_sketch:
    Rectangle2D(80, 50)
plate = plate_sketch.extrude(8)

with Sketch(plane="XZ") as side_sketch:
    Polygon2D(
        [(0, 0), (40, 0), (40, 8), (8, 8), (8, 30), (0, 30)],
        plane="XZ",
        world=True,
    )
side = side_sketch.extrude(10)""") + """
<p>A sketch plane affects where its axes go; changing the camera does not rotate its geometry. Leave the <code>with Sketch(...)</code> scope, then call <code>sketch.extrude(...)</code> to create 3D material. Direct <code>Rectangle2D(...).extrude(...)</code> syntax is intentionally not supported.</p>
<h2 id="boolean">Add, subtract and intersect</h2>
""" + code("""body = Box(50, 50, 20)
tool = Cylinder(d=12, h=22).at(0, 0, 0)
joined = body + tool       # union, where supported
cut = body - tool          # difference, where supported
shared = body & tool       # intersection, where supported""") + """
<p>The supported compiler path depends on the operands. Native feature
history and CSG trees are not interchangeable for every operation.
For manufacturing features such as holes, prefer the native
<a href="../features/">feature operations</a>.</p>""",
    },
    {
        "slug": "transformations",
        "title": "Transformations and orientation",
        "summary": "Coordinate systems, movement, rotation, copies and what is not yet supported.",
        "body": """
<h2 id="axes">First choose the coordinate system</h2>
<p>SolidCraft models are three-dimensional: X, Y and Z are axes, not
synonyms for left, up and front in every project. The conventional
<code>Box</code> base is in XY and its height extends along +Z.
A portrait HUB75 module may be authored with its large face in XY, then
placed upright in the assembly's XZ plane.</p>
<p>Differentiate <strong>definition coordinates</strong> (how one component
is built) from <strong>assembly coordinates</strong> (where an occurrence
is placed). A camera rotation is only a change of view; it does not
change any of these coordinates.</p>
<h2 id="move">Move: translation</h2>
""" + code("""from scpf import Box

body = Box(40, 20, 10)
shifted = body.move(x=10, y=0, z=25)""") + """
<p>For supported CSG shapes, <code>move()</code> translates the local geometry
expression. Occurrence placement is a different layer and is declared when the
occurrence is created or copied.</p>
""" + code("""from scpf import Placement, component

class Panel:
    def build(self):
        return Box(160, 320, 14.5)

PanelComponent = component(Panel)
first = PanelComponent()
right = first.copy(placement=Placement(x=160))""") + """
<h2 id="rotate">Orientation is part of Placement</h2>
<p>Occurrence orientation is declarative data in <code>Placement</code>, not a
separate rotation action.</p>
""" + code("""from scpf import Placement, X, Y, Z

upside_down = first.copy(
    placement=Placement(rotation=(Z, 180))
)
upright = first.copy(
    placement=Placement(rotation=(X, 90))
)

sideways = first.copy(
    placement=Placement(rotation=((0, 1, 0), 90))
)""") + """
<p>SCPF supports one absolute axis-angle orientation per occurrence.
Orientation is part of the complete <code>Placement</code>; it is not a
separate occurrence rotation action.</p>
<h2 id="copies">Copies are independent placements</h2>
<p>One <strong>component definition</strong> describes the shape and its
editable features. Every <strong>occurrence</strong> says where one copy
belongs in the assembly. Several occurrences reuse the same definition.</p>
""" + code("""first = PanelComponent(
    placement=Placement(z=160, rotation=(X, 90))
)
second = first.copy(
    placement=Placement(x=160, z=160, rotation=(X, 90))
)
screen = first + second""") + """
<p><code>copy()</code> without a placement override inherits the source
Placement. Supplying <code>placement=...</code> gives the new occurrence its
complete declared pose. The compiler then chooses the smallest native
creation/copy plus placement fallback needed by SolidCraft 0.42.</p>
<h2 id="json">What SCPF actually sends to SolidCraft</h2>
<p>The sequence below is deliberately simple: create one component,
copy it once, then ask SolidCraft to place both occurrences. The
editable shape features are omitted here for clarity.</p>
""" + code("""{
  "commands": [
    {"command":"component.create","params":{"name":"Panel"}},
    {"command":"occurrence.copy","params":{
      "component":"Panel",
      "translate":[160,0,160]
    }},
    {"command":"occurrence.move","params":{
      "occurrence":"Panel:1",
      "translate":[0,0,160],
      "axis":[1,0,0],
      "angle":"90 deg",
      "move_grounded":true
    }},
    {"command":"occurrence.move","params":{
      "occurrence":"Panel:2",
      "translate":[0,0,0],
      "axis":[1,0,0],
      "angle":"90 deg"
    }}
  ]
}""") + """
<p>SolidCraft 0.42.0 understands the native <code>translate</code>,
<code>axis</code> and <code>angle</code> parameters. SCPF does
<strong>not</strong> calculate transformation matrices. Forge uses the qualified 0.42.0 occurrence-placement contract directly; it
does not invent transformation matrices or depend on an unqualified placement
field.</p>
<p>Passing a command-plan test is not enough to prove the CAD is right.
The CAD project's native tests also inspect the rotations and
positions saved in SolidCraft's own design, and front/rear screenshots
help verify the result visually. A camera change does not rotate
the actual panel geometry.</p>
<h2 id="limitations">Current support summary</h2>
<table><thead><tr><th>Operation</th><th>Scope</th><th>Limit</th></tr></thead><tbody>
<tr><td><code>Shape.move(x,y,z)</code></td><td>Supported CSG shapes</td><td>Local geometry transform</td></tr>
<tr><td><code>placement=Placement(...)</code></td><td>Component occurrences</td><td>Absolute parent-frame pose at create/copy time</td></tr>
<tr><td><code>rotation=(axis,degrees)</code></td><td>Placement</td><td>One absolute axis-angle orientation</td></tr>
</tbody></table>""",
    },
    {
        "slug": "features",
        "title": "Features and references",
        "summary": "Native holes, fillets, shells and relative positioning.",
        "body": """
<h2 id="features">A feature changes an existing body</h2>
<p>A native feature is different from subtracting arbitrary CSG geometry.
SCPF can retain named sketches and operations in SolidCraft history.
For exact results, supported body types and selection constraints matter.</p>
<h2 id="hole">Holes</h2>
""" + code("""from scpf import Box, Hole, Depth, Faces

plate = Box(100, 60, 10)
hole = Hole(d=8, depth=Depth.THROUGH_ALL)
plate = plate + hole.on(plate, face=Faces.TOP)""") + """
<p>A <code>Hole</code> is a native hole feature: adding it to the shape
means adding the operation that <em>removes</em> material.
<a href="../../reference/Faces/"><code>Faces.TOP</code></a> selects its entry face. Simple feature placement
uses <code>on()</code>; assembly attachment uses explicit anchors.</p>
<h2 id="fillet">Fillets and chamfers</h2>
""" + code("""from scpf import Box, Edges
body = Box(80, 50, 15)
rounded = body.fillet(3, edges=Edges.VERTICAL)""") + """
<p>Edge selection can use supported named selectors or explicit pick
coordinates. Named profile segment IDs are available for
<code>Polygon2D</code> workflows. A topological edge cannot
always be inferred reliably from a visual camera position.</p>
<h2 id="shell">Shells</h2>
""" + code("""from scpf import Box, Faces
case = Box(80, 50, 30).shell(2, open=Faces.TOP)""") + """
<p><a href="../../reference/Faces/"><code>Faces.TOP</code></a> chooses the face to open and is also the same
surface-selection vocabulary used by <code>feature.on(...)</code>.
<a href="../../reference/Anchor/"><code>Anchor</code></a> is reserved for explicit component attachment in
assemblies. See the source and regression tests for supported feature chains.</p>
<h2 id="anchors">Feature placement without hard-coded global offsets</h2>
""" + code("""from scpf import X, Y, Boss, Anchor

boss = Boss(d=7, h=12, hole_d=2.5).attach(
    case, parent=Anchor.INNER_BOTTOM,
    offset=(X.MIN + 10, Y.MAX - 10),
)""") + """
<p><code>X.MIN</code> and <code>Y.MAX</code> refer to the parent
bounds and are not rotation-axis constants. Anchoring support
currently focuses on rectangular bases and a documented set of faces.
Do not assume every curved or lofted surface supports it.</p>""",
    },
    {
        "slug": "components",
        "title": "Components and assemblies",
        "summary": "Reusable definitions, occurrence transforms, grouping and attachments.",
        "body": """
<h2 id="definition">One definition, several occurrences</h2>
""" + code("""from scpf import Box, assembly, component

@component
class Beam:
    length = 100.0

    def build(self):
        return Box(self.length, 20, 20)

@assembly
class BeamPair:
    spacing = 120.0

    def build(self):
        left = Beam()
        right = left.copy(placement=Placement(x=self.spacing))
        return (left + right).group("Beams")

pair = BeamPair()""") + """
<p><code>@component</code> marks one reusable physical part. Its
<code>build()</code> returns the complete geometry/feature tree for that part;
that tree may be made from many primitives and features. <code>@assembly</code>
marks a class whose <code>build()</code> composes separate component occurrences. Both decorators
return callable model objects, so normal model code stays readable as
<code>Beam()</code> and <code>BeamPair()</code>.</p>
<p>SolidCraft receives one reusable definition and multiple occurrences.
A group is a native parent component in the browser, not a Boolean
fusion of its children.</p>
<h2 id="component-parameters">Component parameter visibility</h2>
<p>Reusable component defaults are fixed by default. Publish selected child
parameters explicitly with <code>include=</code>:</p>
""" + code("""@component(include=("inside_corner_radius",))
class CornerBracket:
    width = 24.0
    inside_corner_radius = 4.0

    def build(self):
        ...""") + """
<p>When a parent <code>Parameter</code> or expression is passed into a child
input, that existing dependency stays symbolic. For example,
<code>CornerBracket(inside_corner_radius=self.corner_radius)</code> reuses the
parent design's <code>corner_radius</code>; it does not create a separate
<code>CornerBracket_inside_corner_radius</code> parameter.</p>
<h2 id="placement">Occurrence placement</h2>
<p><code>copy()</code> retains the source Placement when no override is
supplied. <code>copy(placement=Placement(...))</code> creates the new occurrence
with the supplied absolute pose in the parent coordinate frame. The compiler
uses creation-time copy translation where SolidCraft can represent it and a
native fallback only where required.</p>
""" + code("""center = BeamComponent()
array = center
for x in (-240, -120, 120, 240):
    array = array + center.copy(placement=Placement(x=x))""") + """
<h2 id="attach">Component attachment</h2>
""" + code("""right = BeamComponent().attach(
    left, parent=Anchor.RIGHT, child=Anchor.LEFT
)

marker = Marker().attach(
    frame,
    parent=Anchor.FRONT_TOP_RIGHT,
    child=Anchor.BACK_TOP_RIGHT,
)""") + """
<p><code>attach()</code> is the public Forge relationship between reusable
components. <a href="../../reference/Anchor/"><code>Anchor</code></a> selects the attachment reference: a supported
face, or one of the eight rectangular corners such as
<code>FRONT_TOP_RIGHT</code>. Corner anchors compile to native SolidCraft
edge/corner origins, so they follow dimension changes in a saved design.</p>
<h2 id="attach-offset">Associative in-plane attachment offset</h2>
<p><code>attach(offset=(u, v))</code> moves the child within the attachment
plane. Numeric values and parameter expressions are both supported. Forge
lowers a non-zero or symbolic in-plane offset to a native planar joint and
keeps <code>u</code> and <code>v</code> as SolidCraft joint values, so they are
re-evaluated when their parameters change.</p>
""" + code("""wood = Parameter("wood_thickness", 18)

bracket = Bracket().attach(
    side,
    parent=Anchor.FRONT_TOP_LEFT,
    child=mount,
    offset=(0, -wood + 12),
    gap=-12,
)""") + """
<p><code>offset</code> is independent of <code>gap</code>: the two offset
values move in the attachment plane, while <code>gap</code> remains the normal
distance between the two references. On a rectangular corner origin, the
second planar value follows the selected vertical corner edge; its sign is
defined by that corner frame rather than by world Z.</p>
<h2 id="assembly-anchor">Assembly-owned named anchors</h2>
<p>When a datum belongs to the meaning of an assembly rather than to a generic
component, keep it on the assembly with <code>with_anchor()</code>. The anchor
stores the target occurrence plus its attachment reference. Consumers resolve
it by name with <code>anchor()</code>.</p>
""" + code("""frame = (left + right + bottom).with_anchor(
    "front_top_left",
    left,
    AnchorTopology(
        edge=(-6, 0, 181),
        on=(0, 0, 181),
        corner=(-6, 0, 362),
        z=(0, 0, -1),
        x=(1, 0, 0),
    ),
)

parent = frame.anchor("front_top_left")
bracket = CornerBracket().attach(
    parent.target,
    parent=parent.reference,
    child=bracket_reference,
)""") + """
<p>This keeps a generic <code>Board</code> or <code>CornerBracket</code> free
of application-specific anchor names while a higher-level frame can expose
semantic datums such as <code>front_top_left</code>.</p>
<p>An assembly anchor may also carry its own symbolic
<code>offset=(u, v)</code>. Consumers can combine that semantic offset with a
fixed local correction and pass the result to <code>attach(offset=...)</code>.
This is useful when an assembly datum follows a frame parameter such as wall
thickness while the reusable part keeps a fixed mounting correction.</p>
<h2 id="anchor-frame">AnchorFrame: point plus orientation</h2>
<p>An <a href="../../reference/attachment-references/#AnchorFrame"><code>AnchorFrame</code></a> describes one local attachment coordinate frame.
<code>origin</code> gives the local point; <code>z</code> gives the attachment
normal and <code>x</code> fixes the rotation around that normal. Use it when a
single point or rectangular <code>Anchor</code> is not enough to describe how
the occurrence must be oriented.</p>
""" + code("""from scpf import Anchor, AnchorFrame

mount = AnchorFrame(
    origin=(0, 0, -12),
    z=(0, 1, 0),
    x=(0, 0, -1),
)

bracket = CornerBracket().attach(
    side_board,
    parent=Anchor.FRONT_TOP_LEFT,
    child=mount,
)""") + """
<p>There are two ownership patterns. If the datum is an intrinsic part of a
reusable component, expose it with <code>anchors()</code> and refer to it by
name. If the frame exists only because of a particular assembly or mounting
choice, construct the <a href="../../reference/attachment-references/#AnchorFrame"><code>AnchorFrame</code></a> in that assembly and pass it
directly to <code>attach()</code>. This keeps application knowledge out of the
generic component definition.</p>
""" + code("""@component
class Sensor:
    def anchors(self):
        return {
            "connector": AnchorFrame(
                origin=(12, 0, 4),
                z=(1, 0, 0),
                x=(0, 0, 1),
            )
        }

    def build(self):
        return Box(24, 12, 8)

sensor = Sensor().attach(panel, child="connector")""") + """
<p>For an unrotated occurrence, Forge lowers an <a href="../../reference/attachment-references/#AnchorFrame"><code>AnchorFrame</code></a>
directly into the native <code>joint.create</code> reference as
<code>point</code>, <code>z</code> and <code>x</code>; it does not create a
persistent visible <code>joint.origin</code>. Named frames on explicitly
rotated occurrences currently use the native origin fallback so SolidCraft
owns the transform. A direct <code>AnchorFrame</code> on an explicitly rotated
occurrence is not supported yet.</p>
<h2 id="anchor-topology">AnchorTopology: follow an edge or corner</h2>
<p><code>AnchorTopology</code> is a named component datum that stays attached to native SolidCraft topology. <code>edge</code> picks an edge, <code>on</code> selects its adjacent planar face and <code>corner</code> optionally chooses one endpoint. The coordinates are selection picks; SolidCraft keeps the selected edge, face and endpoint by topology name as the design changes.</p>
""" + code("""from scpf import AnchorTopology, Box, component

@component
class Board:
    def anchors(self):
        return {
            "mount": AnchorTopology(
                edge=(-20, 50, 5),
                on=(-20, 50, 10),
                corner=(-20, 0, 5),
                z=(0, 1, 0),
                x=(0, 0, 1),
            )
        }

    def build(self):
        return Box(40, 100, 20)""") + """
<p>This is useful for references such as the straight tangent edge beside a fillet: if dimensions move that edge, the joint can follow it without freezing the original XYZ point. The current implementation supports named or direct <code>AnchorTopology</code> values on non-rotated occurrences. A direct topology anchor is useful when the datum belongs only to one assembly rather than to the reusable component. SCPF deliberately does not transform topology picks itself.</p>
<p>SolidCraft joints remain an internal implementation detail; Forge does not
expose a separate public Joint object.</p>
<h2 id="verify">What to test in an assembly</h2>
<p>Check the native command list for one <code>component.create</code>
per shared definition, expected <code>occurrence.copy</code> counts,
and native <code>translate</code>, <code>axis</code> and <code>angle</code>
parameters for rotated occurrences. Separately verify native SolidCraft
geometry and its bounding dimensions before trusting an assembly image.</p>""",
    },
    {
        "slug": "verification",
        "title": "Verification and API boundaries",
        "summary": "Python unit tests, native JSON plans and mechanical evidence.",
        "body": """
<h2 id="unit">Unit tests for Python behavior</h2>
<p>The library's tests under <code>scpf/tests/</code> cover model
objects, feature compilation, reusable components and rotation validation.
For example, an occurrence rotation test checks that the compiler emits
one <code>occurrence.move</code> with the expected native parameters.</p>
""" + code("""python -m unittest discover -s scpf/tests -v""") + """
<h2 id="json">Test compiled native commands</h2>
<p>Compare the generated command structure with explicit expectations,
not only with a count of operations. Tests should check component names,
requested positions, the orientation axis and angle, and feature ordering.
A regression can preserve a known good JSON fixture when command ordering
is part of the contract.</p>
<h2 id="native">Native geometric verification</h2>
<p>The CAD model repository runs a separate SolidCraft CLI workflow for
native geometry, editable history, STEP output, measurements and screenshots.
Read the <strong>saved SolidCraft occurrence transforms</strong>, not just
whether a command ran successfully. A valid Python object or syntactically valid command plan is not evidence
that the final solid occupies the correct plane or has no collision.</p>
<h2 id="changes">Keep implementation and docs in sync</h2>
<p>When placement syntax changes, add tests for the exact generated native
commands before documenting it as supported. Named principal-axis rotation
is supported; chained rotations are still not.</p>
<p>For a plain-language explanation of the implementation and its
boundaries, read
<a href="https://github.com/brainboxemb/lib.py.solidcraft.forge/blob/main/scpf/docs/architecture.md">How SCPF works (without building a second CAD engine)</a>.</p>""",
    },
]

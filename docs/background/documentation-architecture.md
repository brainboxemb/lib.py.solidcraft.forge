> Historical/background record. The current documentation structure is defined in [../development.md](../development.md).

# Documentation architecture

Forge documentation has one source for each kind of information. Generated
reference pages must not become a second API specification.

## What is the source of truth?

| Information | Source of truth | Published form |
| --- | --- | --- |
| Public names, signatures, defaults, enums and types | Python implementation in `scpf/scpf/` | Generated API Reference |
| Short API meaning and usage constraints | Structured public docstrings next to that implementation | Generated API Reference |
| Cross-object design rules that cannot sensibly live on one Python object | `docs/05-cad-api-design.md` | API design/contract page |
| How to solve a modelling task | `site/guides.py` and executable examples | API Guide and examples |
| Example command verification | `examples/<example>/tests/` + generated `solidcraft.json` | CAD-CI item result |
| Native model verification | `examples/<example>/verification/` | CAD-CI `model_verify` result |
| Repository architecture summary | `AGENTS.md` | Repository instructions |

Do not manually copy signatures, enum-member lists, defaults or supported
values into hand-maintained guide text. Guide pages may and should show relevant
API facts inline when that material is generated from the same Python
objects/docstrings as the reference. The reader should not have to click away
for every small detail.

## Reference pages must still teach enough to be usable

Generated does not mean unexplained. A reader who lands on an API reference
page should be able to answer these questions without searching the repository:

1. What is this object or method for?
2. When would I normally use it?
3. What is its current Python signature or complete set of values?
4. What important limitation applies?
5. Where is the nearest worked example or guide section?

The first four answers come from the implementation and its structured
docstrings. The fifth is navigation metadata only; the worked explanation
remains in the guide/example and is not duplicated into the reference source.

For example, a `Faces` page should not merely list `TOP`, `BOTTOM`, and the
other members. It should say that `Faces` selects planar surfaces for
within-component feature operations, show the complete generated member table,
state which operations currently accept which faces, and link directly to a
small feature example.

## Reference navigation

Completeness does not require one page per public symbol. Related public
constructors and helpers may be rendered together on generated group pages such
as geometry constructors, feature constructors, parameters/positioning and
attachment references.

Grouping is navigation metadata only. Every member's signature, enum values,
description, intended use and limits still come from the real Python object and
its docstring.

The reference index should present task-oriented groups before the detailed
alphabetic/method lookup. The guide remains the preferred entry point when the
reader is still deciding which concept to use.

Every name exported through `scpf.__all__` must resolve to either a direct
generated reference, a generated group member, or a generated alias. CI treats
an unmapped public export as a documentation error.

## Guide pages

The guide is task-oriented rather than an alphabetic API dump. It should
explain concepts in normal language and show complete small examples.

A guide may use `Faces.TOP` and should show the complete `Faces` choices
nearby when those choices help the task. That list must be injected from the
generated API data rather than maintained by hand. The symbol can still link to
the full `Faces` reference page for deeper lookup.

This keeps the two views complementary without creating a click maze:

- **Guide:** “How do I put a hole on the top of this plate?” plus the relevant
  generated `Faces` choices and current `Shape.on()` signature inline.
- **Reference:** complete lookup for `Faces` and `Shape.on()`, including the
  same generated facts and links back to worked usage.

## SolidCraft runtime evidence

Forge API facts come from Forge code and docstrings. Native SolidCraft behaviour
is verified by example-owned `model_verify` checks in the immutable
`solidcraft_runtime`.

The former generated SolidCraft command snapshot was removed during the CAD-CI
cleanup because it no longer had an active verification path.

## Agent documentation

Agents use the same sources as humans. Do not maintain a second handwritten API
manual for agents.

The preferred lookup order is:

1. `docs/agent/forge-api.json`, a compact generated machine-readable API
   index derived from the same Python objects/docstrings as the human reference;
2. the relevant local guide/example when modelling intent is needed;
3. the implementation or API design document for deeper detail;
4. external documentation only when the local version-pinned sources are
   insufficient.

The local machine-readable index is deliberately compact: it contains routing,
current signatures/enum values and a short summary, while detailed use/limit
prose stays in the docstrings and full website reference. It is generated
output and must not be edited by hand.
After changing public API objects/docstrings, regenerate the local snapshot with:

```text
python site/api_reference.py --agent > docs/agent/forge-api.json
```

The site test compares that committed snapshot with the live generator output,
so drift is a CI failure.

## Generation rule

The API-reference generator may contain grouping, ordering and navigation
metadata. It must not independently redefine:

- signatures or defaults;
- enum members;
- public values;
- support constraints;
- semantic API descriptions that belong on a public object.

Those belong with the public implementation/docstring or, for a genuinely
cross-cutting rule, in the API design document.

## Migration status

The public API migration is complete for the current Forge surface. Exact public
names, signatures, defaults, enum members and object-local semantics come from
the implementation/docstrings; the generator retains only grouping, ordering
and navigation metadata.

Changing one public API fact now requires changing one authoritative source.
The generated human reference, inline guide facts and compact agent index are
checked against that source in CI. Any future public export must be mapped into
the generated reference before CI can pass.

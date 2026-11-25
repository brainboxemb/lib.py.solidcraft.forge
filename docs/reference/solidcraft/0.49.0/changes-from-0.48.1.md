# SolidCraft 0.49.0 changes from 0.48.1

This diff is derived from the two checked canonical command registries:

- 0.48.1: 866 commands, runtime v0.3.5;
- 0.49.0: 886 commands, runtime v0.3.6.

The 0.49.0 registry adds **20** command ids, removes **0**, and changes
**35** existing definitions. Existing-definition changes are limited to
`params` text/contracts and keyboard `shortcut` metadata; no existing command
id disappeared.

## Added commands

- `body.collision`
- `body.remove_history`
- `component.physical_override`
- `construct.point.average`
- `doc.info`
- `file.export_urdf_options`
- `file.revert_saved`
- `frame.gusset`
- `frame.trim`
- `inspect.hole_stacks`
- `joint.dynamics`
- `joint.origin_frame`
- `layout.delete`
- `sheet.bead`
- `sketch.export_svg`
- `sketch.spline3d.control_point`
- `timeline.roll_to_end`
- `timeline.roll_to_start`
- `timeline.step_back`
- `timeline.step_forward`

## Existing command definitions changed

- `assembly.constraint.create`
- `component.break_link`
- `component.insert_design`
- `component.paste_from_design`
- `component.update_links`
- `doc.open`
- `doc.recover`
- `drawing.dimension.add`
- `drawing.dimension.edit`
- `drawing.dimension.inspect`
- `drawing.dimension.repair`
- `drawing.sheet.set`
- `file.export`
- `file.export_3mf`
- `file.export_obj`
- `file.export_stl`
- `file.export_urdf`
- `file.insert_step`
- `file.save`
- `file.save_as`
- `frame.member`
- `inspect.clearance`
- `joint.origin`
- `parts.fastener`
- `parts.insert`
- `sheet.export_dxf`
- `sketch.move`
- `sketch.move3d`
- `sketch.replace`
- `solid.extrude`
- `solid.move`
- `surface.loft`
- `surface.revolve`
- `view.fit`
- `view.home`

## Forge-relevant review

- `sheet.fold` has no registry-contract change between 0.48.1 and 0.49.0.
  Forge #74 therefore continues to use the same native `sketch` + `curve`
  associative fold input that was qualified on the 0.49 candidate.
- `solid.extrude` gains the documented `to_body_apart` option; existing
  Forge extrusion inputs remain present.
- `sheet.export_dxf` documents formed-bead output in addition to the existing
  roles.
- `surface.loft` and `surface.revolve` gain explicit facing controls.
- Shortcut metadata changes include Sketch Move (`M`), Fit (`End`) and Home
  (`Home`).

The complete machine-readable diff remains the pair of checked
`commands.json` files. This note records review conclusions; it is not a
replacement for canonical registry evidence.

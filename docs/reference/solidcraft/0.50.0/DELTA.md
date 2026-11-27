# SolidCraft 0.49.0 → 0.50.0 command-registry delta

Canonical snapshots:

- 0.49.0: 886 registered commands;
- 0.50.0: 930 registered commands;
- added: 44;
- removed: 0.

The delta was computed from the normalized canonical `commands.json` snapshots
captured from immutable runtime releases v0.3.6 and v0.3.8.

## Added command ids

- `browser.isolate`
- `browser.unisolate`
- `drawing.auto_center_mark.exclude`
- `drawing.auto_center_mark.include`
- `drawing.auto_center_mark.inspect`
- `drawing.auto_center_mark.set`
- `drawing.balloon.delete`
- `drawing.center_line.add`
- `drawing.center_line.edit`
- `drawing.center_line.inspect`
- `drawing.center_line.remove`
- `drawing.center_mark.add`
- `drawing.center_mark.edit`
- `drawing.center_mark.inspect`
- `drawing.center_mark.remove`
- `drawing.note.delete`
- `file.export_mjcf`
- `inspect.section.delete`
- `inspect.section.list`
- `inspect.section.rename`
- `inspect.section.save`
- `inspect.section.show`
- `pulley.insert`
- `select.boundary`
- `select.edge_loop`
- `sketch.create3d`
- `sketch.freeze_link`
- `sketch.link_visibility`
- `sketch.merge_lines`
- `sketch.references`
- `sketch.remove_link`
- `sketch.repair_link`
- `sketch.resume_link`
- `sketch.spline.control_polygon`
- `sketch.update_references`
- `solid.dome`
- `surface.midsurface`
- `surface.midsurface_analyze`
- `view.isolate_others`
- `view.parts_library`
- `view.plane_size`
- `view.reset_home`
- `view.scale_bar`
- `view.set_home`

## Compatibility conclusion

No previously registered command id disappeared. Forge therefore retains its
existing lowering vocabulary while moving the tested runtime baseline to
SolidCraft 0.50.0. Newly available native capabilities are evidence for future
consumer-driven API work; this runtime adoption does not expose new Forge
authoring solely because the engine registry grew.

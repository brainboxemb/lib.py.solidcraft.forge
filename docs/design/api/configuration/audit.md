# Configuration API audit

Status: active cleanup  
Tracking: #444, #669

The configuration surface stays limited to semantic CAD concepts.

## Keep

### model.configure(...)

Configuration owns:

- named rows;
- one active row;
- Parameter value columns;
- authored-feature suppression columns.

### Parameter

An existing Parameter is already the configuration target. No Param wrapper is
needed.

### authored feature handles

A handle returned by `feature(...)`, an authored feature Shape, or an exported
component feature is the direct suppression target. No Suppress wrapper is
needed.

### feature(name, suppressed=...)

This remains the consumer contract for one real later CAD history operation
with stable semantic identity.

## Installed state correction

Issue #669 confirms that Installed does not require another public state or rule
abstraction.

One normal row with one direct suppression column is sufficient:

~~~text
Configuration     Suppress: Installed
Normal                    [x]
~~~

The checkbox is the stored suppression cell.

Do not insert a Configuration Rule, drive_suppression, condition/effect
objects or a second Free/Installed row axis.

## Remove / do not restore

Do not restore the retired broad public wrappers solely for this use case:

~~~text
Configure(...)
Param(...)
Suppress(...)
ConfigRule(...)
Always(...)
DriveParameter(...)
DriveSuppression(...)
~~~

The credible public surface remains:

~~~text
Parameter
feature(name, suppressed=...)
authored feature handle
occurrence.feature(name)
model.configure(...)
~~~

Any future abstraction must be justified by a separate CAD requirement.
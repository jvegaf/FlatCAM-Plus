---
name: flatcam-tcl-command
description: "Trigger: Tcl command, tclCommands, shell command, scripting API. Add or modify a FlatCAM Plus Tcl shell command."
license: Apache-2.0
metadata:
  author: "th3g3ntl3man"
  version: "1.0"
---

# FlatCAM Plus Tcl Command

## Activation Contract

Load when adding or editing a module in `tclCommands/`, exposing a tool through the Tcl shell, or changing an existing command alias, option, or help text.

## Hard Rules

- Create `tclCommands/TclCommand<Name>.py` with a class of exactly the same name, subclassing `TclCommand` from `tclCommands.TclCommand`.
- Subclass `TclCommandSignaled` instead of `TclCommand` for long-running or blocking operations; it runs the command through the worker and supports timeouts.
- Define the command surface as class attributes: `aliases` (list, include old names), `description`, `arg_names` and `option_types` (`OrderedDict`), `required` (list), and `help` (`main`, `args`, `examples`).
- Implement `execute(self, args, unnamed_args)`. Return a result value on success and `"fail"` on a handled error.
- Report invalid input through `self.app.shell.raise_tcl_error(...)` or `self.log`; do not raise raw exceptions for user errors.
- Append the import to the explicit alphabetical list in `tclCommands/__init__.py`. Discovery uses loaded `sys.modules`, so an unimported module is invisible.

## Decision Gates

| Command kind | Base |
| --- | --- |
| Fast geometry/object operation | `TclCommand` |
| CNC job, export, or other long task | `TclCommandSignaled` |
| New name for an existing command | Add an alias; do not duplicate logic |

## Execution Steps

1. Copy the closest existing command, such as `TclCommandCutout.py`.
2. Rename the module and class; keep them identical.
3. Fill `aliases`, `arg_names`, `option_types`, `required`, and `help`.
4. Implement `execute()` using `self.app.collection`, `self.app.new_object`, or `camlib` helpers.
5. Import the module in `tclCommands/__init__.py` in alphabetical position.
6. Exercise the command through the Tcl shell or a targeted script.

## Output Contract

Report: module and class name, aliases, arguments and options, registration line added, and the invocation used to verify it.

## References

- `tclCommands/TclCommand.py` — base and signaled command contracts.
- `tclCommands/TclCommandCutout.py` — complete command example.
- `tclCommands/__init__.py` — alphabetical import list and registration.

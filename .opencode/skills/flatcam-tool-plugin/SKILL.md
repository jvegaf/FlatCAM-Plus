---
name: flatcam-tool-plugin
description: "Trigger: add tool, plugin, menu action, AppTool, tool panel. Create or modify a FlatCAM Plus tool plugin and register it correctly."
license: Apache-2.0
metadata:
  author: "th3g3ntl3man"
  version: "1.0"
---

# FlatCAM Plus Tool Plugin

## Activation Contract

Load when adding or changing a tool/plugin under `flatcam_plus/appPlugins/`, its menu action, its panel, or its registration in `flatcam_plus/appMain.py`.

## Hard Rules

- Subclass `AppTool` for panels; subclass `AppToolEditor` for editing tools. Import from `flatcam_plus.appTool`.
- Keep the tool class and its `...UI` class in one `flatcam_plus/appPlugins/Tool<Name>.py` file. Build the UI on `self.layout` using widgets from `flatcam_plus.appGUI.GUIElements`.
- Override `install()` and call `AppTool.install(self, icon, separator, shortcut=..., **kwargs)`; pass menu placement through `pos=`, `before=`, `separator=`, `icon=`, `shortcut=`.
- Register the instance in BOTH `App.install_tools` (instantiate + `install()`) and the `self.app_plugins` list in `flatcam_plus/appMain.py`. `App.init_tools` rebuilds tools after layout changes by calling `install_tools`.
- Persist user-editable values as `tools_<tool>_*` keys in `flatcam_plus/defaults.py`; read them via `self.app.options[...]`. Use `self.default_data` for per-job parameters.
- Report to the user with `self.app.inform.emit(...)` using `[success]`, `[warning]`, or `[ERROR]` prefixes; log with `self.app.log`.
- Never run heavy geometry or file work in a UI slot; dispatch through `self.app.worker_task` or `FCProcess`.

## Decision Gates

| Need | Action |
| --- | --- |
| New panel or wizard | New `AppTool` subclass + UI class |
| Modify existing tool behavior | Edit the existing `Tool*.py` |
| Editor integrated in the canvas | `AppToolEditor` subclass |
| Menu-only action | `install()` with the correct menu `pos` |

## Execution Steps

1. Copy the closest sibling plugin (for example `ToolDistance.py` for a simple panel).
2. Define the tool class, then the UI class; set `self.pluginName`.
3. Implement `install()` with the requested menu position, icon, and shortcut.
4. Instantiate and install it in `App.install_tools`; append it to `self.app_plugins`.
5. Add defaults under `tools_<tool>_*`; wire option reads/writes.
6. Run the focused check from `flatcam-testing` and smoke-test the panel when a display is available.

## Output Contract

Report: new or edited files, class names, menu placement, defaults added, registration points, and verification evidence.

## References

- `flatcam_plus/appTool.py` — `AppTool` and `AppToolEditor` contracts.
- `flatcam_plus/appPlugins/ToolDistance.py` — minimal panel plus UI example.
- `flatcam_plus/appMain.py` — `install_tools` registration and `app_plugins` list.
- `flatcam_plus/defaults.py` — option key naming.

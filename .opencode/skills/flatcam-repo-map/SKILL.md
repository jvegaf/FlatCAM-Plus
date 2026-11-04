---
name: flatcam-repo-map
description: "Trigger: FlatCAM architecture, repo map, where is X, layer boundaries, new feature. Navigate the legacy FlatCAM Plus codebase and choose the right layer."
license: Apache-2.0
metadata:
  author: "th3g3ntl3man"
  version: "1.0"
---

# FlatCAM Plus Repository Map

## Activation Contract

Load for any non-trivial change, code-location question, architecture decision, or when deciding which layer or file to modify.

## Hard Rules

- The runtime entrypoint is `flatcam.py`; the app is one process-wide `App`. The repository root IS the application (legacy layout). There is no installable package and no `src/` tree: `pyproject.toml` sets `[tool.uv] package = false`.
- All implementation follows ODD (`AGENTS.md` § Development workflow). Load `flatcam-odd-workflow`; for tracked work, read the feature document before editing.
- Python is `3.14` via `uv`. Use `uv sync`, then `.venv/bin/python flatcam.py`. There is no `flatcam-plus` console script to launch.
- `appMain.py`, `flatcam_plus/camlib.py`, and `flatcam_plus/appDatabase.py` are 160–350 KB. Never read them whole; grep exact symbols or use CodeGraph.
- PyQt6 widgets stay on the GUI thread. Move long work to `self.app.worker_task.emit({'fcn': ..., 'params': [...]})` or `FCProcess`; never block the event loop.
- Do not sync `flatcam_plus/version.py` (`APP_VERSION`) with `flatcam_plus/defaults.py` `version` (the preferences-file format).
- User state: QSettings `"Open Source"/"FlatCAM_Plus"`; data and `log.txt` live in `~/.FlatCAM` on Linux/macOS. `config/configuration.txt` is read only on Windows.

## Decision Gates

| Change | Layer |
| --- | --- |
| Menu tool, wizard, tool panel | `flatcam_plus/appPlugins/Tool*.py` |
| Document type, serialization, plotting | `flatcam_plus/appObjects/` |
| Geometry / CNC algorithms | `flatcam_plus/camlib.py` |
| Shared helpers, logging, updater, recent projects | `flatcam_plus/appCommon/` |
| G-code post-processing | `preprocessors/` |
| Scripting command | `flatcam_plus/tclCommands/` |
| Parser (Gerber, Excellon, DXF, SVG, HPGL2) | `flatcam_plus/appParsers/` |
| Widgets, canvas, themes, preferences UI | `appGUI/` |
| Persisted defaults | `flatcam_plus/defaults.py` |
| App wiring, menus, tool registration | `appMain.py` |

## Execution Steps

1. Read `AGENTS.md` and the `EVO-*` entries in `.kiro/steering/flatcam-evolution-log.md`.
2. Locate the owning symbol with CodeGraph or targeted grep; read only the relevant functions.
3. Find the closest sibling implementation and reuse its helpers, naming, and registration pattern.
4. Check `flatcam_plus/defaults.py` for option keys and `appMain.py` for registration.
5. Apply the change and verify with the `flatcam-testing` skill.

## Output Contract

Report: layer chosen, files and functions touched, any registration or defaults update, verification run, and the `EVO-*` constraint that applied.

## References

- `AGENTS.md` — run/test commands and repo gotchas.
- `.kiro/steering/flatcam-evolution-log.md` — verified behavior differences.

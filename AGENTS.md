# FlatCAM Plus — Agent Guide

Legacy PyQt6 desktop CAM application for PCB/CNC manufacturing. The working
application lives at the repository root (legacy layout), not in `src/`.

## Run and test

```bash
uv sync                                   # environment from uv.lock / .python-version
.venv/bin/python flatcam.py               # launch the app (needs a display)
uv run --with pytest pytest tests -q      # run the test suite
uv run --with pytest pytest tests/test_classify_contours.py -v
```

- `python flatcam.py` is the real entrypoint; the app is one process-wide
  `App` object created in `flatcam.py`.
- Do **not** use `flatcam-plus` / `uv run flatcam-plus`: `[project.scripts]`
  points at `src/flatcam_plus/__init__.py`, which only prints a hello message.
  `uv build` likewise packages only that stub, not the application.
- Python is **3.14** (`.python-version`, `pyproject.toml`, `uv.lock`). Version
  claims in `README.md` (3.11), `requirements.txt`, and `Makefile` (3.8) are stale.
- `pytest` is not a project dependency; use the `--with pytest` form above.
  Tests are standalone (currently only contour classification, shapely-only).
- No CI, lint, formatter, or type-check configuration exists. Do not assume or
  invent one.

## Development workflow — Organic Driven Development (ODD)

All development in this repository follows ODD. Do not ask whether to use it.

1. **Authorize.** Investigation, explanation, and review stay read-only until a
   change is explicitly requested.
2. **Explore before writing.** Use CodeGraph or targeted grep; never read
   `appMain.py`, `camlib.py`, or `appDatabase.py` whole.
3. **Resolve uncertainty.** Ask one focused question only for a real product or
   design decision, then wait.
4. **Classify.** Small work (understood, contained risk, resumable from the
   diff) runs inline with no task artifacts. Large work is tracked.
5. **Track before the first source write.** Create
   `odd/tasks/<feature-name>.md` with a header, `## Specs` (`S#`), `## Tasks`
   (`T#` with linked `S#`), and `## Log` (`L1` = the original request verbatim).
   Keep the Engram mirror at topic `odd/<feature-name>/tasks`.
6. **Implement task by task.** Cite the document, task, and specs when
   delegating; read the document until `## Log`; report which `S#` were covered.
7. **Test first.** Observe RED, implement GREEN, then refactor. Run the focused
   test and the full suite once each. A behavior change with no runnable RED
   needs a stated exception and a proportionate check.
8. **Close honestly.** Report the verified outcome, every failed or skipped
   check, and `Risk: item N (reason)` or `Risk: none`.

Commit reviewable work units of about 400 authored changed lines, with tests and
docs alongside the behavior, using Conventional Commits. Branch first when on
the default branch. Push, pull request creation, and merge remain human
decisions. Receipt-driven review is a separate, user-owned switch; when enabled,
follow its native lifecycle without treating it as delivery approval.

## Where things live

| Area | Entry point |
| --- | --- |
| Application controller, menus, tool registration | `appMain.py` (`class App`) |
| Geometry/CNC algorithms | `camlib.py` |
| Tool plugins (Cutout, Isolation, Drilling, …) | `appPlugins/Tool*.py` |
| Document objects (Gerber, Excellon, Geometry, CNCJob) | `appObjects/` |
| Parsers (Gerber, Excellon, DXF, SVG, HPGL2) | `appParsers/` |
| GUI, plot canvases, themes, preferences | `appGUI/` |
| Object editors and their plugins | `appEditors/` |
| G-code preprocessors | `preprocessors/` |
| Tcl shell commands | `tclCommands/` |
| Persisted defaults/preferences | `defaults.py` |

`appMain.py`, `camlib.py`, and `appDatabase.py` are very large (~160–350 KB).
Search targeted symbols instead of reading them whole.

## Conventions and gotchas

- **Tool plugins**: subclass `AppTool`/`AppToolEditor` (`appTool.py`), implement
  `install()`, then instantiate and add the tool to `App.app_plugins` in
  `appMain.py` (~line 1958). The tool UI class usually lives in the same file.
- **G-code preprocessors**: every `.py` file in `preprocessors/` is imported at
  startup and each `PreProc` subclass registers itself by class name. No central
  registry edit is required.
- **Tcl commands**: after adding a command module, append its import to the
  explicit alphabetical list in `tclCommands/__init__.py` (it is not autodiscovered).
- **Two unrelated versions**: `appVersion.py` holds the application version
  (`APP_VERSION = "1.2.0"`). `defaults.py`'s `version` (`8.992`) is the
  preferences-file format version; it is not the app version. Do not sync them.
- **Persisted state**: QSettings organization/application is
  `"Open Source"` / `"FlatCAM_Plus"`. User data and `log.txt` go to `~/.FlatCAM`
  on Linux/macOS and `%APPDATA%\FlatCAM` on Windows.
- **`config/configuration.txt`** (`portable`, `headless`) is read only on Windows;
  Linux/macOS ignore it and always use `~/.FlatCAM`.
- **Windows-first code**: `flatcam.py` contains a PyQt6 DLL bootstrap, and some
  path handling hardcodes backslashes. Verify Linux behavior instead of assuming
  it works when touching startup/config code.
- **Translations**: source strings use `_()` (gettext domain `strings`) and live
  in `locale/<lang>/LC_MESSAGES/strings.po`. No `.mo` files are committed, so
  translations are inactive until compiled:
  `find locale -name "strings.po" -exec sh -c 'msgfmt "$1" -o "${1%.po}.mo"' sh {} \;`
- **Packaging**: follow `PACKAGING.md` and the platform scripts under
  `packaging/`. Build on the target OS; the scripts use `--collect-all` for PyQt6,
  vispy, shapely, rasterio, OpenGL, and matplotlib (plus ortools in the platform
  scripts, and `google.protobuf`/`certifi` in `build_standalone.ps1`).
- **Repo knowledge log**: `.kiro/steering/flatcam-evolution-log.md` records
  verified behavior differences and workarounds (`EVO-*` entries). Append there
  when a user confirms a new difference; feature specs live in `.kiro/specs/`.

## Project skills

Load the matching skill from `.opencode/skills/<name>/SKILL.md` before working:

| Skill | Use when |
| --- | --- |
| `flatcam-odd-workflow` | Every authorized change; read before implementing or delegating |
| `flatcam-repo-map` | Locating code, choosing a layer, or any non-trivial change |
| `flatcam-tool-plugin` | Adding or changing a tool under `appPlugins/` |
| `flatcam-object-model` | Adding or changing a document object under `appObjects/` |
| `flatcam-preprocessor` | Changing G-code output under `preprocessors/` |
| `flatcam-tcl-command` | Adding or changing a Tcl shell command |
| `flatcam-testing` | Running or adding tests |
| `flatcam-plotter-workflow` | PCB Plotter, pen plotter G-code, or physical tests |

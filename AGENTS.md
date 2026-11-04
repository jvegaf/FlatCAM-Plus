# FlatCAM Plus — Agent Guide

Legacy PyQt6 desktop CAM application for PCB/CNC manufacturing. The working
application lives at the repository root (legacy layout); it is not an
installable package.

## Run and test

```bash
uv sync                                   # environment from uv.lock / .python-version
.venv/bin/python flatcam.py               # launch the app (needs a display)
uv run --with pytest pytest tests -q      # run the test suite
uv run --with pytest pytest tests/test_classify_contours.py -v
```

- `python flatcam.py` is the real entrypoint; the app is one process-wide
  `App` object created in `flatcam.py`.
- There is **no** `flatcam-plus` package or console script. `pyproject.toml`
  declares `[tool.uv] package = false`, so `uv sync` installs dependencies only:
  `uv build` has nothing to package and `uv run flatcam-plus` does not exist.
- Python is **3.14** (`.python-version`, `pyproject.toml`, `uv.lock`, and the
  `Makefile` guard). `pyproject.toml` is the only authoritative dependency list:
  `uv.lock` pins the resolved set, and `requirements.txt` mirrors its
  pip-installable subset for virtualenv remediation. There is no conda
  environment file.
- `pytest` is not a project dependency; use the `--with pytest` form above.
  Most tests are shapely-only. `tests/conftest.py` provides a session-scoped
  `fc_app` fixture that boots the real application headless
  (`QT_QPA_PLATFORM=offscreen`) under a throwaway `HOME`, so the suite never
  reads or writes `~/.FlatCAM`. Because the app builds a `multiprocessing.Pool`
  whose forkserver child re-imports the main module, any boot driver must keep
  top-level work behind `if __name__ == "__main__"`. The repository root reaches
  `sys.path` through `pythonpath = ["."]` in `pyproject.toml`, not through an
  insert in `tests/conftest.py`, because the application packages stay at the root.
- `flatcam_plus.appMain.App` parses `sys.argv` with getopt at import time and exits on
  unknown options; `tests/conftest.py` replaces `sys.argv` so pytest's own flags
  cannot reach it.
- CI is `.github/workflows/tests.yml`: `uv sync --frozen` plus the suite on Ubuntu
  with the offscreen Qt platform. There is no lint, formatter, or type-check
  configuration. Do not assume or invent one.

## Development workflow — Organic Driven Development (ODD)

All development in this repository follows ODD. Do not ask whether to use it.

1. **Authorize.** Investigation, explanation, and review stay read-only until a
   change is explicitly requested.
2. **Explore before writing.** Use CodeGraph or targeted grep; never read
   `flatcam_plus/appMain.py`, `flatcam_plus/camlib.py`, or `flatcam_plus/appDatabase.py` whole.
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
| Application controller, menus, tool registration | `flatcam_plus/appMain.py` (`class App`) |
| Geometry/CNC algorithms | `flatcam_plus/camlib.py` |
| Tool plugins (Cutout, Isolation, Drilling, …) | `appPlugins/Tool*.py` |
| Document objects (Gerber, Excellon, Geometry, CNCJob) | `appObjects/` |
| Parsers (Gerber, Excellon, DXF, SVG, HPGL2) | `appParsers/` |
| GUI, plot canvases, themes, preferences | `appGUI/` |
| Object editors and their plugins | `appEditors/` |
| G-code preprocessors | `preprocessors/` |
| Tcl shell commands | `tclCommands/` |
| Persisted defaults/preferences | `flatcam_plus/defaults.py` |
| Test suite and headless app fixture | `tests/`, `tests/conftest.py` |
| CI workflow | `.github/workflows/tests.yml` |

`flatcam_plus/appMain.py`, `flatcam_plus/camlib.py`, and `flatcam_plus/appDatabase.py` are very large
(~160–350 KB).
Search targeted symbols instead of reading them whole.

The runnable entry point stays at the repository root: `flatcam.py` imports
`flatcam_plus.appMain` and owns the `if __name__ == '__main__'` block. `App.app_home`
(and therefore `os.chdir`, `assets/`, `locale/` and `preprocessors/`) is anchored to that
root directory, not to the package.

## Conventions and gotchas

- **Tool plugins**: subclass `AppTool`/`AppToolEditor` (`flatcam_plus/appTool.py`), implement
  `install()`, then instantiate and add the tool to `App.app_plugins` in
  `flatcam_plus/appMain.py` (~line 1965). The tool UI class usually lives in the same file.
- **G-code preprocessors**: every `.py` file in `preprocessors/` is imported at
  startup and each `PreProc` subclass registers itself by class name. No central
  registry edit is required.
- **Tcl commands**: after adding a command module, append its import to the
  explicit alphabetical list in `tclCommands/__init__.py` (it is not autodiscovered).
- **Two unrelated versions**: `flatcam_plus/version.py` holds the application
  version (`APP_VERSION = "1.2.0"`). `flatcam_plus/defaults.py`'s `version` (`8.992`) is the
  preferences-file format version; it is not the app version. Do not sync them.
  The build scripts extract `APP_VERSION` from that file by path, so it must stay
  a single-line assignment at `flatcam_plus/version.py`.
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
  vispy, shapely, rasterio, OpenGL, and matplotlib, plus ortools via
  `$ortoolsBinaryArgs`.
- **Root build wrappers**: `FlatCAMPlus_linux_portable_generator.sh`,
  `FlatCAMPlus_macos_dmg_generator.command`, `FlatCAMPlus_x32_installer_generator.bat`,
  `FlatCAMPlus_x64_installer_generator.bat` and `run_flatcam.bat` are the
  double-click entry points. They resolve `dirname $0` and delegate into
  `packaging/`, so they must stay at the repository root. Build logic belongs in
  `packaging/<os>/`, never in these wrappers.
- **Legacy packaging**: `build_standalone.ps1` is a superseded single-architecture
  variant of `packaging/windows/build_windows_installer.ps1`. It pins a
  `c:\temp\fcvenv` virtualenv created with `py -3.13` against this project's
  Python 3.14. Keep it only for the `google.protobuf`/`certifi` PyInstaller
  collection it documents.
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

# Repo structure cleanup

Staged cleanup of the FlatCAM Plus file and directory structure, driven by L1 and split into
phases by explicit user choices in L2 and L4. Phases 0 and 1 are complete and committed;
phases 2 and 3 remain.

This document was written at handoff time (L5). Phases 0 and 1 ran inline as a bounded change
before it existed; everything from phase 2 on is multi-session and tracked here.

## Specs

- **S1 — Phase 0: limpieza de artefactos y duplicados.** Authorized scope, verbatim from L2:
  "Borrar docs/error.txt, unificar doc/, mover generadores a packaging/, resolver el stub
  src/flatcam_plus. Sin tocar imports ni código de la app. Riesgo casi nulo, arregla el
  empaquetado que hoy miente."
- **S2 — Phase 1: unificar manifiestos de dependencias.** Authorized scope, verbatim from L4:
  "pyproject.toml como fuente única; podar requirements.txt, environment.yml y Makefile. Mata
  las instrucciones contradictorias de Python 3.11/3.8/3.14."
- **S3 — Phase 2: red de seguridad (authorized in L10).** Target, verbatim from this document's
  phase-2 next step: "a headless startup smoke test, one test per critical domain, and a CI
  workflow that runs `uv sync` plus the suite." Authored scope that decides it: "Tests y CI para el
  arranque de la app y los dominios críticos, como prerequisito de cualquier reorganización de
  ficheros." The critical domains, fixed here so the net is defensible: (a) application startup
  wiring, (b) Gerber input, (c) Excellon input, (d) G-code output through a preprocessor.
- **S4 — Phase 3: migrar el layout plano (proposed, not yet authorized, blocked on S3).** Move
  the root modules into a package. 210 files import root-level modules today, so every one is
  a call site.

### Deviations from the literal authorized text

- S1 asked to "mover generadores a packaging/". Evidence refuted the move; it was not done. See D1.
- S2 asked to "podar requirements.txt". Evidence refuted both deletion and generation; it was
  reconciled instead. See D3.

## Tasks

- **T1 (S1)** — Remove the fictional package path and the dead artifacts. Route: inline.
  Status: done in `aedf5e7`. Covers S1 except the generator move (D1).
- **T2 (S2)** — One dependency source of truth. Route: inline. Status: done in `aedf5e7`
  (both stages landed in one commit because `AGENTS.md` carried edits from both, and the two
  together stay well under one review slice). Covers S2 except the requirements.txt pruning (D3).
- **T3 (S3)** — Add a startup smoke test, one test per critical domain, and a CI workflow.
  Route: inline. Status: done in `dbf3c1a` (tests) and `1e890ea` (CI and `AGENTS.md`).
  Covers S3 in full.
- **T4 (S4)** — Move the root modules into a package. Route: pending, unblocked now that T3
  landed.

## Decisions

- **D1 — Root build wrappers stay at the repository root.** `FlatCAMPlus_linux_portable_generator.sh`,
  `FlatCAMPlus_macos_dmg_generator.command`, `FlatCAMPlus_x32_installer_generator.bat`,
  `FlatCAMPlus_x64_installer_generator.bat` and `run_flatcam.bat` are double-click entry points
  that resolve `dirname $0` and delegate into `packaging/`. Moving them breaks the delegation,
  and `README.md` and `PACKAGING.md` document them at the root. Build logic belongs in
  `packaging/<os>/`.
- **D2 — `build_standalone.ps1` is kept and marked LEGACY, not deleted.** It pins a hardcoded
  `c:\temp\fcvenv` created with `py -3.13` against a Python 3.14 project, and
  `packaging/windows/build_windows_installer.ps1` supersedes it. It survives because it is the
  only script that collects `google.protobuf` and `certifi` for PyInstaller.
- **D3 — `requirements.txt` is kept and reconciled, neither deleted nor generated.** It is
  advisory-only, but `flatcam.py:56` (the PyQt6 DLL failure hint) and three packaging scripts
  tell the user to run `pip install -r requirements.txt`; deleting it breaks that remediation
  path. Generating it with `uv export` is worse: the full export pins `gdal==...`, and the file
  exists as the pip-installable subset precisely because GDAL wheels are painful on Windows.
  It is now 1:1 with pyproject's 33 direct dependencies.
- **D4 — `environment.yml` is deleted.** `gdal>=3.13.3` and `rasterio>=1.5.2` resolve from
  PyPI in `uv.lock`, so the conda path was redundant; the file also contradicted pyproject
  (`numpy==1.26.4` against `numpy>=1.16`) and carried `pre-commit`, which is not a project
  dependency.
- **D5 — `[tool.uv] package = false`; `[build-system]` and `[project.scripts]` removed.** The
  project is an application, not a library. `uv sync` installs dependencies only, and `uv build`
  fails loudly instead of emitting a wheel containing `print("Hello from flatcam-plus!")`.

## Slice boundary and delivery state

This feature's slices are T1+T2 (14 files, 84 insertions, 137 deletions, `aedf5e7`) and T3
(7 files, 214 insertions in `dbf3c1a` plus 49 insertions and 3 deletions in `1e890ea`).

`dev` is 17 commits ahead of `origin/main` with 3291 added and 434 deleted lines
(`git diff --numstat origin/main..dev`, lock files excluded), which is well past one review
slice. That backlog predates this work. Push, pull request creation and merge remain human
decisions and must account for it.

## Known follow-ups

- `packaging/windows/build_windows_installer.ps1` does not collect `certifi` or
  `google.protobuf`; only the legacy `build_standalone.ps1` does. Verify whether the canonical
  Windows build needs them.
- `requirements.txt` remains a hand-maintained mirror of `pyproject.toml` and can drift again.
  A platform-aware generator would be the durable fix; `uv export` cannot express it today.
- `appPreProcessor.load_preprocessors` uses the deprecated `importlib` `SourceFileLoader.load_module()`,
  which emits a `DeprecationWarning` in the suite and is scheduled for removal in Python 3.15.
  Moving it to `exec_module()` is a prerequisite for that interpreter bump.
- The latent defects recorded in L12 (`generate_from_multitool_geometry` reading four missing
  `geometry_*` options, and `preprocessors/default.py` crashing on the default empty `xy_end`)
  still need a decision; neither is covered by a test that would fail on purpose.

## Next step

T3 is done: the suite boots the real application headless, covers the four critical domains and
runs in CI. T4 (moving the root modules into a package) is unblocked but not authorized; it
still touches 210 import sites and needs an explicit go-ahead first.

## Log

- **L1 — Original request (verbatim)**: "creo que el proyecto necesita un repaso a nivel de estructura de ficheros/directorios. como lo ves?"
- **L2 — User selected (verbatim option text)**: "Fase 0: limpieza de artefactos y duplicados — Borrar docs/error.txt, unificar doc/, mover generadores a packaging/, resolver el stub src/flatcam_plus. Sin tocar imports ni código de la app. Riesgo casi nulo, arregla el empaquetado que hoy miente."
- **L3 — User (verbatim)**: "sigue con la fase 1"
- **L4 — User selected (verbatim option text)**: "Fase 1: unificar manifiestos de dependencias — pyproject.toml como fuente única; podar requirements.txt, environment.yml y Makefile. Mata las instrucciones contradictorias de Python 3.11/3.8/3.14."
- **L5 — User (verbatim)**: "haz commit primero y dejalo todo preparado para continuar en la siguiente sesion"
- **L6 — Evidence that changed S1**: the four root `FlatCAMPlus_*_generator.*` files are 20 to
  112 line wrappers that compute `ROOT_DIR` from their own directory and delegate to
  `packaging/`. Relocating them breaks the path; `README.md:355-357` and
  `PACKAGING.md:76-261` document them at the root.
- **L7 — Evidence that changed S2**: `flatcam.py:56`,
  `packaging/linux/build_linux_portable.sh:126`, `packaging/macos/build_macos_dmg.sh:133` and
  `packaging/windows/build_windows_installer.ps1:124` all instruct `pip install -r
  requirements.txt`. `uv lock` resolves `gdal` and `rasterio` from PyPI, which makes
  `environment.yml` redundant.
- **L8 — Verification for T1+T2**: `uv run --with pytest pytest tests -q` reports 22 passed;
  `uv lock --check` is clean; `import flatcam, appMain, camlib, appDatabase, defaults` succeeds;
  `requirements.txt` matches pyproject's 33 direct dependencies with no missing, extra or
  duplicate entries, and every line parses as PEP 508; `make -n install` evaluates the new 3.14
  guard; the four root wrappers resolve to existing files under `packaging/`.
- **L9 — Unavailable check**: the independent verifier (`gentle-ai-verify`) refused both
  launches because the harness requires a recognized `Risk: item N` declaration at launch and
  then instructs not to retry. The checks in L8 were run by the parent instead, so no second
  pair of eyes covered this change.
- **L10 — User (verbatim)**: "arranca T3". This authorizes S3 as written above and nothing else:
  T4 stays blocked.
- **L11 — Evidence that shaped the T3 tests**: `appMain.App.__init__` builds a
  `multiprocessing.Pool`, so any boot driver must guard top-level code behind
  `if __name__ == "__main__"`; the forkserver child re-imports the main module. `App` reads
  `os.path.expanduser('~')` and `QSettings("Open Source", "FlatCAM_Plus")` during construction,
  so a test can isolate it by setting `HOME` and `XDG_CONFIG_HOME` to a temporary directory
  before creating the `QApplication`. With `QT_QPA_PLATFORM=offscreen` the app boots in about
  6 seconds, registers 28 plugins and 28 preprocessors, and exits cleanly through
  `quit_application()`.
- **L12 — Defect found while building the net, not fixed here** (outside S3's authorized scope):
  `camlib.CNCjob.generate_from_multitool_geometry` reads `geometry_dwelltime`,
  `geometry_startz`, `geometry_endz` and `geometry_endxy` from `app.options`, and none of those
  keys exists in `defaults.py`, so it raises `KeyError`. `preprocessors/default.py:start_code`
  also raises `IndexError` when `xy_end` is the empty string that `CNCjob.__init__` defaults to
  (`endxy=''`); `camlib.CNCjob.doformat2` swallows the exception and emits an empty header. The
  T3 output test therefore drives a real `CNCjobObject` with an explicit end coordinate and the
  `GRBL_11` preprocessor, and leaves both defects for a separate decision.
- **L13 — Pass criteria for the net**: the startup test asserts the wiring the file move would
  break (main window, plugin count, preprocessor registry, isolated data directory); the Gerber
  and Excellon tests assert parsed geometry, not internal storage; the output test asserts
  emitted G-code text. Because these are characterization tests over behavior that already
  works, there is no runnable RED: the substitute is a mutation check (T3 verification).
- **L14 — Verification for T3**: `uv run --with pytest pytest tests -q` reports 35 passed in
  6.7 s (was 22 passed with no app coverage). Mutation checks, each reverted with
  `git checkout --` or a restored copy: (M1) `load_preprocessors` forced to return `{}` fails
  `test_loads_the_gcode_preprocessors` and errors the three output tests; (M2) `GRBL_11.linear_code`
  emitting `G00` fails `test_emits_a_linear_cut_move`; (M3) the outline drawn 9 mm wide fails
  `test_builds_the_stroked_outline`; (M4) the second drill hit moved to 21 mm fails
  `test_reads_every_drill_hit`. `.github/workflows/tests.yml` parses as YAML with the expected
  one job and five steps; `uv sync --frozen` and `uv lock --check` are clean, so the workflow's
  install step is valid against the committed lockfile. No test writes outside its temporary
  `HOME`: the boot test asserts `data_path` lives inside it.
- **L15 — Unavailable check**: the CI workflow itself was not executed. Running GitHub Actions
  needs a push, which is a human decision, and there is no local runner configured. The YAML
  parse, the `uv sync --frozen` step and the identical pytest command were verified locally on
  Linux with `QT_QPA_PLATFORM=offscreen`; the `apt-get` line for the Qt runtime libraries is the
  one untested part.
- **L16 — Risk for T3**: item 5 (delivery and environment). Adding `.github/workflows/tests.yml`
  creates a new automated pipeline on the remote and changes what a push runs. The test files
  only read application state, but the boot fixture does spawn the app's worker pool and writes
  to a temporary `HOME`. No application behavior changed.

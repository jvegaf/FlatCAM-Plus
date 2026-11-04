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
- **S4 — Phase 3: migrar el layout plano (authorized in L27).** Scope, verbatim from the option
  the user selected: "Mover los módulos de la raíz a un paquete. 210 import sites, riesgo alto,
  requiere tracking ODD completo." Measured surface (L28): 13 root modules, 299 module-to-file
  import edges across ~178 files, plus path-, name- and CWD-based loading that no import rewrite
  reaches. Large: multi-session, sliced in T4.1 to T4.7.

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
- **T4 (S4)** — Move the root modules into a package. Route: inline for the small slices, worker
  for the mechanical import sweeps. Phases:
  - **T4.1** — Anchor the CWD-dependent paths to the app directory, with a test that chdirs
    away. No module moves. Covers S4's prerequisite and the riskiest coupling (L28 #1).
    Status: done in the commit that introduces `tests/test_app_paths.py`; `resource_location` is
    now absolute and the preprocessor glob no longer reads the CWD.
  - **T4.2** — `flatcam_plus/` skeleton and the version pilot: `appVersion` moved to
    `flatcam_plus/version.py`, `appVersion.py` deleted, the three import sites and the five
    build scripts that parsed it by path updated, and `flatcam_plus` added to every
    `--collect-submodules` list. Status: done in the commit that adds
    `tests/test_version_module.py`. The remaining low-fanout modules (`defaults`,
    `appDatabase`, `appProcess`, `appWorker`, `appWorkerStack`, dead `appPool`) move in T4.2b.
  - **T4.2b** — The five remaining low-fanout modules moved under `flatcam_plus/` keeping their
    basenames, the wildcard `from appProcess import *` preserved, `appWorkerStack` switched to a
    relative import of `appWorker`, and the dead `appPool` deleted. Status: done in the commit
    that adds `tests/test_package_layout.py`, which also fails if any file outside the package
    still imports a moved name.
  - **T4.3** — Move `camlib` (35 statements across 35 files). Status: done in the commit that
    adds `camlib` to `tests/test_package_layout.py`. 33 external importers became
    `from flatcam_plus.camlib import ...` and the two package-internal ones (`defaults`,
    `appDatabase`) use `from .camlib import`. No preprocessor imports `camlib`, so the
    path-loaded preprocessors — the one place a broken import would not fail loudly — are not
    involved in this phase at all.
  - **T4.4** — Move `appTool` (53 statements) or `appPreProcessor` (29) and the preprocessor
    discovery with it. Status: `appTool` chosen and done in the commit that adds `appTool` to
    `tests/test_package_layout.py`. All 53 external import sites became
    `from flatcam_plus.appTool import ...`; no package-internal module imports it, and nothing
    loads it by name at runtime, so the phase is a pure rename. The preprocessor half of this
    phase stays open as T4.4b.
  - **T4.4b** — Move `appPreProcessor` (29 statements) together with the preprocessor discovery:
    the `SourceFileLoader` glob, the fixed module name and the metaclass registry are risk
    register item 2, so this slice needs its own verification of the registry. Status: done in
    the commit that adds `appPreProcessor` to `tests/test_package_layout.py`. The 28 preprocessor
    modules and the single `appMain` importer became `from flatcam_plus.appPreProcessor import
    ...`; the discovery itself needed no change because `load_preprocessors` globs
    `app.app_home/preprocessors` and `app.data_path/preprocessors`, never the module's own
    location. The registry was verified by a mutation check, not only by a green suite.
  - **T4.5** — Anchor `locale/` to the application directory and move `appTranslation` (172
    import statements across 173 files). Status: done in the commit that adds
    `tests/test_locale_resolution.py` and `appTranslation` to `tests/test_package_layout.py`.
    `load_languages`, `languages_dir` and the frozen-build candidate now resolve `locale/` from a
    single `_application_dir()` anchored one level above the module, and the silent `parents[1]`
    fallback is gone. All 172 sites became `from flatcam_plus import appTranslation as
    fcTranslate` (167 outside the package) or `from . import appTranslation as fcTranslate` (5
    inside it), and the one `from appTranslation import restart_program` follows the new path.
    One commit, not the two or three the plan predicted: see L37. As with T4.4b, the moved module
    keeps the pre-move name resolvable in `sys.modules` for the out-of-tree user preprocessors,
    and `tests/test_package_layout.py` pins it.
  - **T4.6** — Move `appMain` and keep `.venv/bin/python flatcam.py` working. Status: done in the
    commit that adds `_APP_ROOT` and three anchor tests to `tests/test_app_paths.py` and
    `appMain` to `tests/test_package_layout.py`. `flatcam.py` already was the root launcher, so it
    kept its location, its `__main__` block and its own `base_path`; only its import line moved.
    The whole module now resolves every `__file__`-derived path from one module-level anchor, the
    parent of the package, and `os.chdir` follows it, which disarms risk register item 1. Risk
    register item 5 needed no packaging edit: the four build scripts still name the unchanged root
    `flatcam.py` and already pass `--collect-submodules flatcam_plus`, and `tclCommands` discovery
    keys on the `tclCommands` package, not on `appMain` (101 commands registered after the move).
    The guard's old-name matcher was widened in the same commit, so it now sees the bare
    `import <name>` form that the T4.4 and T4.5 sweeps used, and the two `TYPE_CHECKING` sites it
    would then have flagged were repointed.
  - **T4.7** — Bring the vendored `descartes/` and the `libs/` namespace package inside, and
    retire the `tests/conftest.py` `sys.path` insert.
  Every phase keeps the tree consistent on its own: no shim layer, so nothing is left to remove
  later, and each phase commits its tests, docs and packaging changes together.

## Migration risk register (T4)

From L28, ordered by how likely it is to break silently rather than loudly:

1. **`os.chdir` to the module directory** (was `appMain.py:569,578`) made every `assets/resources`,
   locale and `preprocessors/*.py` lookup CWD-relative, and the preprocessor failure is only
   logged (`flatcam_plus/appPreProcessor.py:155,166-168`). T4.1 removed the CWD dependency;
   T4.6 replaced the module-relative derivation with `_APP_ROOT` and three tests (L41).
2. **Preprocessor discovery** (`flatcam_plus/appPreProcessor.py:10,155-170`):
   `SourceFileLoader` with the fixed module name `FlatCAMPostProcessor` plus metaclass
   registration; a name collision silently
   replaces a preprocessor.
3. **Locale resolution from module location** (`flatcam_plus/appTranslation.py:_application_dir`)
   with a swallowed `StopIteration`: a wrong depth meant an empty language list and an
   English-only UI, no error. Handled in T4.5 (L38).
4. **`descartes` and `libs` as top-level importables** (was `appGUI/PlotCanvasLegacy.py:15`,
   `appMain.py:49-51`, no `libs/__init__.py`): a real PyPI `descartes` could shadow the vendored
   one and theme loading would change without an `ImportError`. Closed in T4.7 (L43): both trees
   live inside the package, neither bare name resolves to this repository, and four layout tests
   pin it.
5. **Tcl discovery keyed on the module-name prefix** (`tclCommands/__init__.py:88-89`, filter
   `:105`): a renamed package path yields an empty command storage with no error; plus the
   build-time hardcodes of `appVersion.py` (`packaging/linux:84`, `packaging/macos:92`,
   `packaging/windows/update_version.ps1:19`) and of `flatcam.py` as entrypoint
   (`packaging/linux:184`, `packaging/macos:209`, `packaging/windows:333`,
   `build_standalone.ps1:83`). Verified in T4.6: discovery keys on the `tclCommands` package and
   none of the four entrypoint hardcodes had to move, because `flatcam.py` stays at the root.
   Item 5 is closed; nothing in `packaging/` referenced `appMain`.

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

This feature's slices are T1+T2 (14 files, 84 insertions, 137 deletions, `aedf5e7`), T3
(7 files, 214 insertions in `dbf3c1a` plus 49 insertions and 3 deletions in `1e890ea`), and the
T4 phase slices: T4.1 `420318b` (paths), T4.2 `c3fccc4` (version pilot), T4.2b `60f72bb`
(low-fanout modules), T4.3 `0424299` (camlib, 43 files, 55 insertions, 49 deletions), T4.4
`367862b` (appTool, 58 files, 99 insertions, 65 deletions), T4.4b `650e83c`
(`appPreProcessor`, 33 files, 64 insertions, 42 deletions) plus its R3-001 shim correction
`91f3165` (3 files, 20 insertions), T4.5 `ef000e5` (`appTranslation`, 176 code and test files with
235 insertions and 186 deletions, where 172 are the same one-line import rewrite repeated and the
moved module is detected as a rename, plus this document's 68/21), T4.6 `b0aac63` (`appMain`,
10 files, 94 insertions, 34 deletions, of which the move is a detected rename and 62 lines are
tests) and T4.7 (this commit; `descartes` and `libs` moved, 57 files, 158 insertions, 94 deletions,
of which 98 are the rename and 49/49 is the mechanical import rewrite).

The T4.5 move and its 172 sites travel together because no shim exists, so splitting that slice
would leave the tree unimportable between commits (L37); every other slice is mechanical in the
same way. Each T4 slice stays under one review slice on its own.

After this commit `dev` is 36 commits ahead of `origin/main` with about 4.1k added and 0.7k
deleted lines (`git diff --numstat origin/main..dev`, lock files and `requirements.txt`
excluded), which is well past one review slice. That backlog predates this work and grows by
one commit per T4 phase. Push, pull request creation and merge remain human decisions and must
account for it: the accumulated branch is not reviewable as a single candidate, so delivery has
to be sliced per phase. `dev` itself is pushed: it is level with `origin/dev` (L37).

## Known follow-ups

- `packaging/windows/build_windows_installer.ps1` does not collect `certifi` or
  `google.protobuf`; only the legacy `build_standalone.ps1` does. Verify whether the canonical
  Windows build needs them.
- `requirements.txt` remains a hand-maintained mirror of `pyproject.toml` and can drift again.
  A platform-aware generator would be the durable fix; `uv export` cannot express it today.
- `appPreProcessor.load_preprocessors` uses the deprecated `importlib` `SourceFileLoader.load_module()`,
  which emits a `DeprecationWarning` in the suite and is scheduled for removal in Python 3.15.
  Moving it to `exec_module()` is a prerequisite for that interpreter bump.
- The HPGL2 parser's own unit assumption (divide by 40) and its inability to read combined pen
  commands such as `PU0,0;` were observed while fixing L49 and left alone: the parser wants a
  standalone `PU;`/`PD;` followed by `PA x,y;`, which is a parser limitation, not a default.
- Almost every `cutz`/`travelz`/`area_*` value `ParseHPGL2` copies into its tool data has no live
  reader left (the readers are commented out in the tool plugins and `camlib` reads the mill keys
  instead). The defaults now exist and are pinned; whether anything consumes them is the older
  question of the commented-out plugin paths, not something this cleanup changed.
- Nothing has verified a packaged build: no PyInstaller bundle was produced in any T4 slice, and
  the three `.ps1` build scripts have not been syntax-checked on a machine with PowerShell. The
  `libs` data-to-code switch in T4.7 (L43) is argued from source and from `PACKAGING.md`, not from
  a bundle. A local Linux portable build is the cheapest way to close it.
- `flatcam_plus/libs/qdarktheme` is vendored and unversioned; that predates this work and no slice
  touched its content.

## Next step

**S1 through S4 are complete.** T1 to T3 delivered the artifact cleanup, the single dependency
manifest and the safety net; T4 moved every root module and both vendored trees into
`flatcam_plus/`, anchored the paths that used to depend on the CWD or on a module's own location,
and replaced the hand-rolled test `sys.path` insert with a declared one. `dev` is level with
`origin/dev`, 96 tests pass, and every phase carries its tests, docs and skills in its own commit:
T4.1 `420318b`, T4.2 `c3fccc4`, T4.2b `60f72bb`, T4.3 `0424299`, T4.4 `367862b`, T4.4b `650e83c`
plus `91f3165`, T4.5 `ef000e5`, T4.6 `b0aac63`, T4.7 (this commit).

What is left is not development work but the human's decision: the branch is 36 commits ahead of
`origin/main` and must be delivered as per-phase slices, never as one candidate. Push, pull request
and merge stay yours. Two recorded defects still wait on a decision and were untouched by T4: the
four missing `geometry_*` options that `CNCjob.generate_from_multitool_geometry` reads, and the
empty-`xy_end` `IndexError` that leaves a G-code header empty (both L12). The first packaged build
is the only remaining verification gap (see Known follow-ups).

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
- **L17 — User (verbatim)**: "levanta los 5 hallazgos". Authorizes fixing the advisory review
  findings on the T3 tests, and nothing else.
- **L18 — Native review outcome**: the harness offered `dev` against `main` (17 commits, ~3.7k
  lines) and the provider stopped on `lens_context_budget_exceeded` without creating authority.
  The scope was reduced to `origin/dev..HEAD` (8 files, 346 lines, tier `high`, correction budget
  173) as lineage `review-0082196c125db361`. Lenses `risk`, `readability` and `reliability` were
  selected; `readability` needed three capture attempts because of two host-relay transport
  failures (`Stream ended without finish_reason`, then `terminated`), each time reoffered by
  STATUS with nothing burned. The review closed `approved` and the acknowledgement burned the
  authority. Five advisory findings, all `informational`, none opening a correction:
  R2-001 `tests/test_gerber_parse.py:12-24`, R2-002 `tests/test_app_boot.py:18-20`,
  R2-003 `tests/test_excellon_parse.py:23-27`, R3-001 `tests/test_gerber_parse.py:19`,
  R3-002 `tests/test_gcode_output.py:17-39`.
- **L19 — The finding text no longer exists**: the closure exposed only id, lens, location and
  severity; the reviewer artifacts (`rart1_...`) are pruned when the authority is consumed.
  Evidence: `.git/gentle-ai/review-transactions/v2/` holds only an unrelated lineage, and
  `.git/gentle-ai/review-transactions/terminal-consumption/v1/9eaae396....json` is the sole
  remainder of this one. A search of the repository, `.git`, `.gentle-ai`, and the Pi session
  transcripts found no artifact body. The fixes below are therefore derived from lens, line
  range and severity, not from the reviewer's literal wording; the user authorized reading the
  native store, and that path was dead.
- **L20 — Defect of my own that the net caught, and the finding that exposed it**: the committed
  `tests/test_gerber_parse.py` shipped `X90000Y0D01*` on the lower vertex. It survived because the
  M3 mutation-check restore copied an already-mutated backup, and because a bounds-only assertion
  cannot see a vertex that still spans the same extent. The file now carries an area assertion
  (11x11 outer minus the 9x9 hole) that M-A proves discriminating.
- **L21 — What each finding produced**: R2-001 and R3-001 (both on the Gerber test) moved the
  sample sources to `tests/data/*.gbr`/`*.drl` behind a `sample_input` fixture, made the parse
  fixtures module-scoped, and replaced the opaque `(object, warning)` tuple with a named tuple;
  the same shape was applied to the Excellon test for R2-003. R2-002 (boot test) replaced a
  vacuous `isdir` assertion with a real isolation proof, `QSettings(...).fileName()` living under
  the session home. R3-002 (G-code test) added a header assertion for the copied bounds and tool
  diameter and derives the expected feedrate from the job instead of hard-coding it. The vacuous
  Excellon "clean file" assertion was deleted rather than kept: `Excellon.parse_lines` always
  returns `None`, so it could never fail.
- **L22 — Isolation bug found while fixing R2-002**: Qt caches its user-scope settings directory
  at first use, so setting `HOME` and `XDG_CONFIG_HOME` inside a fixture is too late once any
  test module imports Qt at collection time; the app wrote into the real `~/.config`. The
  variables are now set at `tests/conftest.py` import time, and the boot test fails if that ever
  regresses.
- **L23 — Verification for L17-L22**: `uv run --with pytest pytest tests -q` reports 36 passed
  (37 before the vacuous test was removed). Mutation checks, all reverted: M-A moves the lower
  vertex to 9 mm and fails `test_builds_the_stroked_outline`; M-B copies `xmax` 99 into the job
  and fails `test_header_reports_the_source_extent_and_tool`; M-C appends a garbage drill line
  and fails `test_reads_every_drill_hit`. The isolation assertion was observed failing before the
  conftest move, which is the only reason it is trusted now.
- **L24 — User (verbatim)**: "1", answering the choice between closing after the second review
  and hardening the new findings blind. This closes the finding work: the second batch stays
  recorded and unfixed.
- **L25 — Native review of the finding fixes (L17-L23)**: offered `main..HEAD` again, reduced to
  `6df9e1b..HEAD` (8 files, 206 lines, tier `medium`, correction budget 103, lenses `readability`
  and `reliability`) as lineage `review-17f2de890ac3f96e`. Both lenses were captured on the first
  attempt, the review closed `approved`, and the acknowledgement burned the authority
  (consumed revision `sha256:ecd80599d84c6a93f3266ac5c67d80b0cf22887ce2f79d350ad21e9998f7a41c`).
- **L26 — Deferred advisory findings from L25** (all `informational`, none opened a correction, so
  the correction budget was never touched):
  - R2-001, readability, `tests/test_gcode_output.py:42-44`, SUGGESTION
  - R2-002, readability, `tests/test_gerber_parse.py:39-41`, WARNING
  - R2-003, readability, `tests/test_app_boot.py:21`, SUGGESTION
  - R3-001, reliability, `tests/test_gcode_output.py:43-44`, WARNING
  - R3-002, reliability, `tests/test_gerber_parse.py:40`, WARNING
  Their text is not recoverable: like L19, the closure reports id, lens, location and severity
  only, and the reviewer artifacts (`rart1_39b13aac...`) are pruned when the authority is
  consumed. That is a limitation of the review integration surface, not of this repository, and
  it is why L24 closed the work instead of guessing at the wording. The two warnings sit on the
  Gerber comment and tolerance that the M-A mutation check already validated by hand.
- **L27 — User authorizations (verbatim option texts)**: "Autorizo device flow con gh" for the
  push attempt, then "Pusheás vos y yo sigo" was not taken: the user pushed `dev` themselves
  ("ya esta pusheado", verified: `origin/dev` at `7a9269f`, 21 commits ahead of `origin/main`).
  T4 was authorized with the option text quoted in S4.
- **L28 — T4 surface, measured before any write** (read-only explorer, evidence per path):
  13 root modules and 299 module-to-file import edges across ~178 files — `appTranslation` 172,
  `appTool` 53, `camlib` 35, `appPreProcessor` 29, `appVersion` 3, `defaults` 2,
  `appDatabase`/`appProcess`/`appWorker`/`appWorkerStack`/`descartes` 1 each, and `appPool` 0
  (dead). Non-static loading: `tclCommands/__init__.py` walks packages and filters module names
  by prefix, `appPlugins/__init__.py` imports explicitly with an optional `ToolImage`,
  `appPreProcessor.load_preprocessors` globs `preprocessors/*.py` from `app.data_path` and from
  the CWD. Path assumptions: `appMain.py:569,578` chdirs to the module directory and the rest of
  the app then reads `assets/`, `locale/` and `preprocessors/` relative to it; `appTranslation`
  derives `locale/` from its own file with a `parents[1]` fallback. Packaging hardcodes
  `appVersion.py` (4 scripts) and `flatcam.py` as the PyInstaller entrypoint (4 scripts).
  7 of the 8 test modules depend on the root being on `sys.path`.
- **L29 — Unavailable check for T4**: no package-layout design was reviewed with anyone but the
  evidence above; the phase order below is the parent's judgement, not a peer-reviewed plan.
- **L30 — T4.4 executed (`appTool`)**: RED first — adding `appTool` to `PACKAGE_MODULES` in
  `tests/test_package_layout.py` failed the three guards (package import, root copy, no root-name
  importer), naming `appEditors/appGerberEditor.py`. Then `git mv appTool.py
  flatcam_plus/appTool.py` and all 53 import sites became `from flatcam_plus.appTool import ...`
  (30 `AppTool`, 21 `AppToolEditor`, 2 both); no `import appTool` form and no multiline import
  existed, so the rewrite was exact. GREEN: `tests/test_package_layout.py` reports 22 passed.
  Nothing imports `appTool` by name at runtime and no package-internal module imports it, so no
  relative import was needed. `AGENTS.md` and `.opencode/skills/flatcam-tool-plugin/SKILL.md`
  (two references) now point at `flatcam_plus/appTool.py`.
- **L31 — The Engram mirror does not exist**: at the start of this session `mem_*` tools were not
  callable and the store at `~/.local/share/gentle-shell/install/home/.engram/engram.db` held 0
  observations and 0 sessions. The task document is therefore the only continuity source, and it
  was missing the log entries for T4.1 to T4.3 too; the Tasks section carried them. Recorded here
  so no later session trusts a mirror that was never written.
- **L32 — T4.4b executed (`appPreProcessor`)**: RED first — adding `appPreProcessor` to
  `PACKAGE_MODULES` failed the same three guards. Then `git mv appPreProcessor.py
  flatcam_plus/appPreProcessor.py` and the 29 import sites became `from
  flatcam_plus.appPreProcessor import ...`: 28 of them are preprocessor modules and one is
  `appMain.py:99`. `load_preprocessors` itself needed no edit because it globs
  `app.app_home/preprocessors` and `app.data_path/preprocessors`, never the module's own file
  location — the T4.1 anchoring is what made that true. Verification beyond the suite: a mutation
  check replaced one preprocessor's import with the old root name and
  `test_loads_the_gcode_preprocessors` failed, which proves the registry assertion is
  discriminating; the file was restored and the suite re-run. `tests/test_package_layout.py`
  reports 25 passed, `tests/test_app_boot.py` plus `tests/test_gcode_output.py` 8 passed.
  `.opencode/skills/flatcam-preprocessor/SKILL.md` points at `flatcam_plus/appPreProcessor.py`.
- **L33 — Git identity was unset**: the T4.4 commit failed with "Author identity unknown"; neither
  the local nor the global config had `user.name`/`user.email`, although every earlier commit is
  authored by `Jose Vega <josevega234@gmail.com>`. Set repository-local only, matching the
  existing history, so no global configuration changed.
- **L34 — Native review of the T4.4/T4.4b slice (lineage `review-6c60462ff0763e44`)**: tier
  `medium`, 91 files, lenses `readability` and `reliability`, both captured first try; the refuter
  confirmed one CRITICAL, deterministic, `introduced` finding. **R3-001**: moving `appPreProcessor`
  without a shim silently breaks the user preprocessors that `load_preprocessors` also loads from
  `app.data_path`, because they import the old root name. Correction, within the frozen budget:
  `flatcam_plus/appPreProcessor.py` keeps the legacy name resolvable in `sys.modules` and
  `tests/test_package_layout.py` pins it; RED (`ModuleNotFoundError`) observed before the fix.
  The finding is a real gap in D-plan: "no shim layer" was right for in-tree imports and wrong for
  the out-of-tree extension point.
- **L35 — Review outcome for the T4.4/T4.4b slice**: the two lenses ran in one group (readability
  102 476 prompt bytes, reliability 102 455), the refuter raised R3-001, the bounded correction
  landed in `91f3165`, and the targeted validator approved it. The acknowledgement burned the
  authority (consumed revision `sha256:28e84312...`, target `sha256:da6c9cf3...`). One advisory
  finding stayed open and is now fixed separately: R2-doc-phase-count, readability, SUGGESTION,
  this document's phase count and commit count.
- **L36 — Review of the whole T4 range (lineage `review-a417c200c19e5786`)**: tier `high` (the
  changed set reaches `appParsers/ParseGerber.py` process spawning and the packaging shell
  scripts), 137 files, lenses `readability` and `reliability`, both captured on the first attempt
  (170 KB prompts each). Approved with no severe finding, so no refuter and no correction; the
  acknowledgement burned the authority (consumed revision `sha256:28fc1b3d...`). Four advisory
  findings, all `informational` and none opening a correction: R2-import-guard-syntax
  (`tests/test_package_layout.py:42-53`, WARNING), R3-001 (`tests/test_app_paths.py:19-22`,
  WARNING), R2-package-doc-stale (`flatcam_plus/__init__.py:1-5`, SUGGESTION) and
  R2-risk-register-stale-path (`odd/tasks/repo-structure-cleanup.md:100`, SUGGESTION). As in L19
  and L26 their text is not recoverable; the two SUGGESTIONS were unambiguous from location and
  are fixed in the commit that records this entry, the two WARNINGs stay deferred with only their
  location.
- **L37 — T4.5 executed (`appTranslation` plus the `locale/` anchoring)**: this session started
  from the task document, not from Engram: the store this session's tools see
  (`…/install/home/.engram/engram.db`) still holds 0 observations (L31), and the real store at
  `~/.engram/engram.db` has the `flatcam-plus` observations only up to 16:01, older than this
  document, so its mirror is stale and the document stayed authoritative. RED first: adding
  `appTranslation` to `PACKAGE_MODULES` failed all three guards, naming
  `appGUI/preferences/general/GeneralGUIPrefGroupUI.py`, and the new
  `tests/test_locale_resolution.py` could not even import (`ModuleNotFoundError:
  flatcam_plus.appTranslation`). Then `git mv appTranslation.py flatcam_plus/appTranslation.py`
  and 172 files rewritten: 167 outside the package to `from flatcam_plus import appTranslation
  as fcTranslate`, the 5 inside it (`defaults`, `appDatabase`, `appProcess`, `appTool`, `camlib`)
  to `from . import appTranslation as fcTranslate`, and the one
  `from appTranslation import restart_program` in `GeneralGUIPrefGroupUI.py` to the package path.
  No other form existed, so the rewrite was exact. Second RED after the move: `languages_dir()`
  returned `flatcam_plus/locale`, which does not exist, and two of the three locale tests failed —
  `load_languages()` still passed, which is precisely why the defect was invisible before: the
  silent `parents[1]` fallback happened to rescue it. Fix: a single `_application_dir()` anchored
  one level above the module now backs `languages_dir()` and the frozen-build candidate, the
  silent fallback is replaced by a `log.error` that names the missing directory, and the now
  unused `pathlib.Path` import is gone. Mutation check: re-anchoring `_application_dir()` to the
  module's own directory fails all three locale tests; restored afterwards. One thing the phase
  did inherit from T4.4b is a `sys.modules` alias for the pre-move name, but the rationale is
  weaker here and the independent verifier refuted the first version of it (L39): nothing in this
  tree imported `appTranslation` from a path-loaded file, so the alias is a compatibility
  allowance for out-of-tree code, not a requirement the tree itself proves. Red observed as
  `ModuleNotFoundError: No module named 'appTranslation'` before the alias, and
  `tests/test_package_layout.py` pins it. `uv run --with pytest pytest tests -q` reports
  76 passed (69 before, plus 3 locale tests, 3 parametrized layout cases and the alias test).
  One commit instead of the two or three the plan predicted: keeping the tree importable at every
  commit means the move and its 172 sites travel together, and the authored diff is one repeated
  one-line rewrite plus a 16/10 rename, so it reviews as a single mechanical unit. The 172
  statements and 173 files quoted in the plan were accurate; what changed is only the commit
  count. `dev` is level with `origin/dev` at the start of the slice, so every earlier T4 commit
  is already pushed; push of this one stays a human decision.
- **L38 — Native review of the T4.5 slice (lineage `review-30a653f091737138`) and its correction**:
  tier `high` (the process-spawn scan in `appGUI/GUIElements.py`), lenses `readability` and
  `reliability`, both captured on the first attempt (191 KB prompts each). The refuter confirmed
  one CRITICAL, inferential, `introduced` finding: **R3-001** — anchoring `locale/` to the parent
  of the package fixed the repository layout and silently dropped the frozen layout, where the
  package is unpacked inside `<app>/lib` and `locale/` stays at `<app>/`; the old
  `Path(__file__).parents[1]` reached it precisely because the module then sat one level higher.
  The finding is real and reproducible: `tests/test_locale_resolution.py` now simulates that layout
  by pointing `__file__` at `<app>/lib/flatcam_plus/appTranslation.py` with `locale/` only under
  `<app>`, and it returned 0 languages before the fix. Correction, inside the frozen budget and
  declared as a 60-line plan: `_locale_candidates()` returns the anchored directory first and the
  frozen-library parent second, `load_languages()` walks them and logs an error only when both are
  empty, and `languages_dir()`/`languages_dir_cx_freeze()` expose the two candidates so
  `apply_language`'s existing two-step `FileNotFoundError` chain is meaningful again. 77 tests
  pass. Risk register item 3 is now handled rather than merely annotated: the silent path is
  covered by two candidates, a logged error and four tests, and the remaining exposure is that no
  frozen build was actually executed in this slice.
- **L39 — Independent verification of the T4.5 slice (`gentle-ai-verify`)**: verdict correct, no
  blocker, with five advisories. It confirmed the importer set is identical to the baseline
  (172 files, both directions of `comm` empty), the relative form is exactly in the five package
  modules, the anchored locale path is used by `languages_dir()` and the frozen candidate, the
  alias resolves and the tests for it discriminate, and 76 tests passed on its own copy. It also
  refuted one claim and one number of mine: **(A1)** the alias rationale was false — no in-tree
  `preprocessors/*.py` ever imported `appTranslation` (`git grep` returns 0 at both `d5282be` and
  HEAD); they import `appPreProcessor` only. The comment and L37 now say that the alias is a
  compatibility allowance for out-of-tree code rather than something this tree requires.
  **(A5)** the slice boundary said 150 repeated import rewrites where the diff has 172; corrected.
  **(A2)** the alias only exists once `flatcam_plus.appTranslation` has been imported, which the
  boot order guarantees (`appMain.py` imports it before `load_preprocessors` runs) but a fresh
  interpreter importing the old name first would still fail. **(A4)** the old-name guard in
  `tests/test_package_layout.py` is a substring search for `from <name> import`, so it cannot see
  the bare `import appTranslation as fcTranslate` form that 168 of the 172 baseline sites used;
  that is the pre-existing `R2-import-guard-syntax` advisory from L36, it is load-bearing for the
  T4.6 and T4.7 sweeps, and it is now a tracked follow-up with a proposed `re`-based matcher rather
  than an unrecorded gap. **(A3)** pid not a defect: the verifier read `848ae36`, before the R3-001
  correction below made `languages_dir_cx_freeze()` the frozen-library candidate instead of a
  duplicate; the frozen layout it could not verify is what that correction now covers with a test.
  Defers honestly: no frozen build was executed, and its scratch directory in `/tmp` was left
  behind (`/tmp/fcverify.ehI1f8`) after tmpfs filled.
- **L40 — Re-review of the corrected slice (lineage `review-6b96d6898e9d63c1`)**: the correction
  produced a candidate whose target identity differed from the frozen one, so the previous
  authority could not close: its targeted-validation slot was rejected by `gentle_review_capture`
  as `missing or stale` on three attempts (object form, exact serialized string, and the group
  tool, which answered that validation is not a reviewer group), all with
  `mutation_performed: false`. `review-30a653f091737138` is therefore left `reviewing` with
  `correction_required` and its correction unvalidated; abandoning it is a human decision, not a
  cleanup step. A fresh ordinary review of `d5282be..HEAD` was started for the corrected tree
  (`review-6b96d6898e9d63c1`, tier `high`, 178 files, 1182 changed lines, lenses `readability` and
  `reliability`, 199 KB prompts each) and closed **approved** with no severe finding, so no refuter
  and no second correction: the R3-001 frozen-layout fix held up on a cold read. The
  acknowledgement burned the authority (consumed revision `sha256:50d0087d...`, target
  `sha256:e0f5361d...`). Four advisory findings, all `informational` and none opening a correction,
  stay recorded by location only because their text is pruned with the burned authority (L19, L26):
  R2-001 (readability, `tests/test_locale_resolution.py:52-54`, WARNING), R2-002 (readability,
  `flatcam_plus/appTranslation.py:22-26`, SUGGESTION), R3-001 (reliability,
  `flatcam_plus/appTranslation.py:23-27`, WARNING) and R3-002 (reliability,
  `tests/test_locale_resolution.py:35-54`, SUGGESTION). Both worth checking first: the alias
  comment block (the same lines the independent verifier flagged as A1, now rewritten) and the
  frozen-layout test body.
- **L41 — T4.6 executed (`appMain`) with the parent past its context backstop**: the phase was
  delegated to `gentle-ai-worker` with the spec by reference and a narrow surface list, because the
  parent session had passed 150k tokens; the worker returned the move, the anchor and the evidence,
  and the parent verified, finished the leftovers, wrote this entry and committed. RED first:
  adding `appMain` to `PACKAGE_MODULES` failed all three guards, naming `flatcam.py`. Then
  `git mv appMain.py flatcam_plus/appMain.py` and the two real importers (`flatcam.py`,
  `tests/conftest.py`) moved to `from flatcam_plus.appMain import App`. The anchor defect showed up
  exactly as risk register item 1 predicted: with the module-relative derivation still in place,
  `app_home` became `flatcam_plus/`, `tests/test_app_paths.py` failed four times and
  `test_app_boot.py` failed with `assert 0 >= 20` on the preprocessor registry — the only assertion
  that noticed, which is why the register called this the silent one. Fix: one module-level
  `_APP_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))` with a comment naming
  the consequence, backing `app_home` and therefore `os.chdir`, `resource_location` and the
  `app_home/preprocessors` glob, plus the five other `__file__`-derived paths in the module (the
  win32 `config/configuration.txt` candidates, the win32 portable `data_path`, the win32 VisPyData
  fallback and the two frozen-build config candidates). Each substitution preserves the pre-move
  value, and `grep -n __file__ flatcam_plus/appMain.py` now returns that definition only. Risk
  register item 5 needed no packaging edit: the four build scripts name the unchanged root
  `flatcam.py` and already pass `--collect-submodules flatcam_plus`, and tcl discovery keys on the
  `tclCommands` package (`tclCommands/__init__.py:88-89,105`), which still registers 101 commands
  after the move. Item 4, the `descartes`/`libs` shadowing risk, is untouched and belongs to T4.7.
- **L42 — The parent-closed gap in the T4.6 evidence**: the worker's surface list did not include
  `appHandlers/appIO.py`, `appCommon/RegisterFileKeywords.py` or `flatcam_plus/appTool.py`, so it
  reported two `TYPE_CHECKING`-only `import appMain` sites and their string annotations as
  unfixable and left them. The parent repointed all three (module name only; the attribute names
  those annotations use were already stale before this work and changing them is not T4.6's
  business), so no source file imports the old root name any more. With that done, the guard could
  finally be widened: `tests/test_package_layout.py` now matches the bare `import <name>` form as
  well as `from <name> import`, with a test that pins both matchers on sample lines, and the
  tracked `R2-import-guard-syntax` advisory from L36 and A4 from L39 is closed. Discriminating
  check: a scratch file containing `import appMain as probe` fails the guard for `appMain`; removed
  afterwards. 84 tests pass. Unverified on this machine: the Windows-only `_APP_ROOT` substitutions
  and any frozen build; CI needs a push.
- **L43 — T4.7 executed (`descartes` and `libs`) and the end of S4**: delegated for the same reason
  as T4.6. Both trees moved under `flatcam_plus/` (40 renames), `flatcam_plus/libs/__init__.py`
  turned the vendored `qdarktheme` from a namespace directory into a real subpackage, and 17
  vendored files plus `appGUI/PlotCanvasLegacy.py` and the five `libs` references in `appMain` were
  repointed at the absolute package path. RED first: the new layout assertions failed ten times and
  named the real defects — neither package importable from inside `flatcam_plus`, both roots still
  present at the repository root, `find_spec('descartes')` resolving to the old tree, and the
  old-name guard naming `appGUI/PlotCanvasLegacy.py` and `libs/qdarktheme/util.py`. Retiring the
  `tests/conftest.py` `sys.path` insert needed a decision the phase text did not spell out: the
  application packages stay at the root, so the root still has to be importable, and the insert was
  replaced by `pythonpath = ["."]` under a new `[tool.pytest.ini_options]` instead of being dropped.
  Mutation check: commenting that setting out produces five collection errors (`appObjects`,
  `appParsers`, `flatcam_plus`, …), so the declaration is load-bearing, not decorative. Risk
  register item 4 is closed: `flatcam_plus.descartes.patch` and `flatcam_plus.libs.qdarktheme`
  import, neither bare name resolves to this repository, and no PyPI `descartes` is installed or
  declared anywhere. The differential check that matters for a vendored theme: the generated CSS is
  byte-identical to `b0aac63` (dark 30120 chars, light 30293, same digests). `libs` was shipped as
  *data* only because it was a top-level package, so `--add-data "libs:libs"` is retired in the
  three PyInstaller scripts and in the legacy one, each of which already collects
  `--collect-submodules flatcam_plus`; `PACKAGING.md`'s two manual snippets had been missing that
  collect flag since T4.2 and now carry it instead. 96 tests pass, and `uv lock --check` stays clean
  because no dependency changed.
- **L44 — Parent-closed leftovers of T4.7**: the worker's surfaces left three things behind that
  the parent finished, since the phase's own purpose was to leave no top-level importable behind:
  the redundant `sys.path.insert` in `tests/test_recent_projects.py` and
  `tests/test_milling_geometry.py` became dead once the insert was declared in `pyproject.toml`
  (removed, with their then-unused `os`/`sys` imports), and the dead comment in
  `flatcam_plus/camlib.py:50` now names the new path. Unverified on this machine, recorded rather
  than papered over: no PyInstaller build, no PowerShell to syntax-check the three `.ps1` scripts,
  and no Windows run for the `_APP_ROOT` substitutions from L41. With L43 the ODD feature that L1
  opened is complete: every module and both vendored trees live in `flatcam_plus/`, and what
  remains is delivery plus the two L12 defects that still need a decision.
- **L45 — Native review of the T4.7 slice (lineage `review-cce224ac06aba6eb`)**: tier `high` (the
  change reaches the three PyInstaller build scripts, so the frozen risk reasons are
  `process_boundary` and `shell_source` on `packaging/linux/build_linux_portable.sh`), lenses
  `readability` and `reliability`, 97 changed paths, both captured on the first attempt at 124 KB
  per prompt. Approved with no severe finding, so no refuter and no correction; the
  acknowledgement burned the authority (consumed revision `sha256:261a6e2a...`, target
  `sha256:e7732c07...`). Two advisories, both unambiguous from their location and fixed in the
  commit that records this entry: **R2-001** (readability,
  `odd/tasks/repo-structure-cleanup.md:199-200`) was this document's Known follow-ups list split in
  two by the two bullets T4.7 added, now one list; **R3-001** (reliability,
  `build_standalone.ps1:94-95`) was the retired `--add-data "libs:libs"` rationale written as a
  comment *inside* the `$pyInstallerArgs` array literal, now above the literal where no argument
  list can be disturbed by it. 96 tests pass.
- **L46 — Deliberate stop before START**: the first two START attempts for this slice were rejected
  by the facade (`graph-v1 START requires lineageId` when the inspect route's lineage was not
  repeated, then `Review controller START supports only "ordinary" or "judgment-day" mode` with
  `input` sent as an object). The third, with `mode: "ordinary"` and `input` as the serialized
  object, created the lineage. Neither rejection performed a mutation, so nothing was left behind.
- **L47 — The two L12 defects fixed on request (verbatim: "arreglalo")**: both were recorded at
  T3 time as needing a separate decision, and the human now asked for them.
  **(1) The missing `geometry_*` options.** The four named keys are added to the geometry options
  block in `flatcam_plus/defaults.py` (`geometry_dwelltime: 1`, `geometry_startz: None`,
  `geometry_endz: 15.0`, `geometry_endxy: None`, mirroring the `tools_mill_*` convention), and
  proving the method actually emits G-code needed seven more keys it reads on the same path
  (`geometry_feedrate`, `_feedrate_z`, `_feedrate_rapid`, `_depthperpass`, `_toolchangez`,
  `_toolchangexy`, `_f_plunge`): with only the four, the `KeyError` simply moved to the next one.
  RED observed in both stages, the second one (`KeyError: 'geometry_f_plunge'`) being the evidence
  that the literal four-key reading of L12 was incomplete. `None` is only used where the code
  tolerates it, which two assertions in the emitted header now pin (`(Z Start: None mm)`,
  `(X,Y End: None mm)`); the keys that are formatted or compared numerically got concrete values.
  **(2) The empty end coordinate.** The preprocessors guard the end move with two flavours of the
  same truthiness test (`is not None` in nineteen of them, `and != ''` in `default.py`), so the
  only value that satisfies both is `None`; `CNCjob.__init__` now normalizes `endxy=''` to `None`
  at the single choke point, and no preprocessor was touched. RED observed as the exact reported
  symptom: the header came back empty with `IndexError: string index out of range` swallowed inside
  `doformat2`. **(3) A third defect found while fixing (1).** The same method raised `TypeError`
  on its own `spindlespeed=None` default, because the storing line compared the argument to `0` and
  then called `int()`; two truthiness characters fix it, and the tests no longer pass the
  `spindlespeed=0` workaround the tool plugins use. G-code for a job that does have an end
  coordinate is unchanged: a differential capture of `start_code`/`lift_code`/`linear_code`/
  `end_code` for the explicit `(1.5, 2.5)` job under both `default` and `GRBL_11` compared empty
  between the previous commit and this one. 96 tests before, 101 after; mutation checks on all
  three fixes fail the tests that pin them and were restored.
- **L48 — Measured, not guessed: the `geometry_*` option gap is bigger than L12 recorded**: a scan
  of every live `app.options["geometry_*"]` read (comment lines excluded) against the keys
  `defaults.py` defines reports 35 read, 24 defined, 12 missing, and after L47 **every** remaining
  reader is `appParsers/ParseHPGL2.py`, which therefore cannot be constructed today. That is
  recorded as a Known follow-up with the exact key list rather than fixed blind: unlike the CNC job
  generator, the right defaults for an HPGL2 import are a product question and there is no HPGL2
  sample in `tests/data/` to verify against.

## Delivery slices

The human chose slices over one candidate. Each slice is a local branch cut at its tip; the base
of each is the previous slice's tip, so the pull requests chain instead of stacking on `main`.
Line counts exclude `uv.lock` and `requirements.txt`.

| slice branch | commits | changed lines | content |
| --- | --- | --- | --- |
| `slice/1-structure` | `aedf5e7`..`a298916` | 276 | S1 artifacts and layout, S2 dependency manifest |
| `slice/2-test-net` | `dbf3c1a`..`7a9269f` | 583 | S3 headless fixture, domain tests, CI, review follow-ups |
| `slice/3-paths-and-core` | `fbf81ba`..`0424299` | 447 | T4 plan, path anchoring, version, low-fanout modules, `camlib` |
| `slice/4-tool-and-preprocessor` | `367862b`..`d5282be` | 570 | `appTool`, `appPreProcessor` and the out-of-tree name shim |
| `slice/5-translation` | `ef000e5`..`1ca9424` | 624 | `appTranslation` with the locale anchoring |
| `slice/6-controller` | `b0aac63` | 217 | `appMain` with `_APP_ROOT` |
| `slice/7-vendored-trees` | `7046492`..`ebceebc` | 378 | `descartes`, `libs`, declared `pythonpath`, build-script data argument |
| `slice/8-defect-fixes` | `d45b6dc` | 187 | the two L12 defects plus the spindle-speed default |

Everything before `aedf5e7` is the branch backlog that predates this feature: it is already on
`origin/dev` and is not part of these slices. `dev` is 6 commits ahead of `origin/dev`
(`ef000e5`..`d45b6dc`); pushing them and opening the chained pull requests are human decisions,
and `gh` is not authenticated in this session, so they were not attempted.
- **L49 — The HPGL2 parser fixed on request (verbatim: "arreglalo")**: `appParsers/ParseHPGL2.py`
  could not be constructed at all, so an HPGL2 import died with `KeyError` before producing
  geometry. Thirteen `geometry_*` options are now defined in the geometry block of `defaults.py`,
  each traced to an existing precedent instead of invented: the cut depth and the area shape from
  the Isolation block (`tools_iso_cutz: -0.05`, `tools_iso_area_shape: "square"`, because the
  parser tags its tools `Iso`), travel, dwell, multidepth, extra cut, tool change, area strategy,
  area over-Z and spindle speed from the Drilling and Milling blocks, and `geometry_ppname_g:
  'default'` naming the preprocessor that exists. The one value where the precedents disagreed is
  the cut depth — the mill block says `-2.4` — and the Isolation value won because an HPGL2 pen
  path is an isolation-style contour; that tie-break is recorded in the code comment so changing it
  is one line. **L48's measurement was off by one**: it reported twelve missing keys because its
  regex counted the `"geometry_multidepth": Geometry` entry of the GUI route map at
  `defaults.py:1084` as a definition, and `geometry_multidepth` is read live by the parser. The
  second half of the fix is the guard that makes the whole class impossible: `tests/
  test_defaults_coverage.py` AST-parses the `factory_defaults` dict and asserts that every live
  `app.options["geometry_*"]` read in the tree (comment lines excluded, `.git`/`.venv`/candidate
  views pruned) is defined, with its own test pinning that commented reads are ignored and that no
  scanned path escapes the repository. RED observed in both halves: the guard listed all thirteen
  keys with their `path:line`, and `tests/test_hpgl2_parse.py` failed with `KeyError:
  'geometry_cutz'` from `HPGL2.__init__`. A real import now parses a nine-statement sample into a
  `LineString (0 0, 25 0, 25 25)` with bounds `0,0,25,25` millimetres and one tool. Mutation check
  on the guard: deleting `geometry_spindlespeed` fails it by name. 101 tests before, 125 after.
- **L50 — Native review of the HPGL2 fix (lineage `review-85d04374fd80d7ab`)**: tier `medium`,
  4 changed paths, lenses `readability` and `reliability` (28 KB prompts), approved with no severe
  finding, so no refuter and no correction; the acknowledgement burned the authority (consumed
  revision `sha256:45cb2dfe...`). Three readability advisories, all informational and all fixed in
  the commit that records this entry because each one was unambiguous from its location:
  **R2-001** (`flatcam_plus/defaults.py:367-369`) was the comment claiming these are parameters "a
  Geometry object reads" when almost every one of them has no live reader left — the comment now
  says the contract is the presence and type of the key and names why (the plugin readers are
  commented out and `camlib` reads the `tools_mill_*` keys); **R2-002**
  (`tests/test_defaults_coverage.py:5`) was the docstring still saying *twelve* keys, which is the
  same off-by-one L49 corrects; **R2-003** (`tests/test_defaults_coverage.py:47-49`) was a real
  weakness in the guard, which skipped only lines that *start* with `#`, so a read behind a
  trailing comment would have counted as live. The scan now tokenises each file with
  `tokenize.generate_tokens`, drops comment tokens and concatenates the rest per line: a trailing
  comment cannot invent a read and a `#` inside a string literal cannot truncate one. The
  synthetic-line test pins both cases, and the scan stays a per-file walk (the guard file's five
  tests take ~3.5 s, up from ~0.4 s: the price of tokenising 300 files).

# Package consolidation: the eight app packages join `flatcam_plus`

The repo-structure cleanup moved the thirteen root *modules* into `flatcam_plus/` but left the eight
application *packages* at the repository root. This feature finishes the job: each package becomes a
subpackage of `flatcam_plus`, one package per commit, with the tree importable at every commit.
`src/` is explicitly out of scope (L2).

## Specs

- **S1 — Goal and layout.** Verbatim from the selected option (L2): "B — consolidar en flatcam_plus/
  sin src/" — "Mitad del camino: los 8 paquetes pasan a subpaquetes. 1206 imports, sin tocar el
  modelo de instalación." The target shape, also from that option's preview:

  ```
  flatcam_plus/
    appMain.py camlib.py …
    appGUI/ appObjects/ appPlugins/ tclCommands/ …
    descartes/ libs/
  flatcam.py
  tests/
  ```

- **S2 — Scope, measured before any write** (L3, corrected in L5): `appCommon` (5 files, 16
  import statements), `appHandlers` (3, 2), `appParsers` (8, 26), `appObjects` (10, 32),
  `appEditors` (31, 41), `appPlugins` (47, 48), `tclCommands` (76, 149), `appGUI` (86, 290).
  266 files and 604 import statements in total. Import forms are the absolute ones
  (`from appGUI.MainGUI import App`), so every rewrites to
  `from flatcam_plus.appGUI.MainGUI import App`.

- **S3 — `tclCommands` discovery keeps working, provably.** `tclCommands/__init__.py:110` filters
  `sys.modules` by the literal prefix `'tclCommands.TclCommand'` and then takes
  `key.split('.')[1]` as the class name. After the move both halves are wrong, and the failure mode
  is an empty Tcl command storage with no error (migration risk register item 5). The move has to
  make the prefix derive from `__name__` instead of a literal, and a test has to fail if the
  registry comes back empty.

- **S4 — Packaging stays consistent per commit.** Each of the four build scripts lists the eight
  packages individually under `--collect-submodules`; once a package lives inside `flatcam_plus`,
  its own entry is redundant. Each slice retires the entry for the package it moved, so no script
  ever collects a package that no longer exists at the root.

- **S5 — Everything else keeps resolving.** `flatcam.py` stays the root entry point, the data
  directories (`assets`, `config`, `locale`, `preprocessors`) stay at the root and keep resolving
  through `_APP_ROOT`, the suite keeps a single declared `pythonpath`, and no `sys.modules` shim is
  added: the import rewrites travel with the move.

## Tasks

- **T1 (S1, S2)** — Move `appCommon` to `flatcam_plus/appCommon/`, rewrite its importers, retire its
  `--collect-submodules` entry in the four build scripts, update the layout guards. Status: done in
  the commit that adds `APP_PACKAGES` to `tests/test_package_layout.py`; `appCommon` already had an
  `__init__.py`, so unlike `libs` it needed no new one.
- **T2 (S1, S2)** — `appHandlers` (3 files, 2 importers). Status: done in the commit that adds
  it to `APP_PACKAGES`/`APP_MODULES`; its only importers were the two `appMain` lines.
- **T3 (S1, S2)** — `appParsers` (8 files, 26 importers). Status: done in the commit that adds it
  to `APP_PACKAGES`/`APP_MODULES`; 26 import statements rewritten, no preprocessor imports it.
- **T4 (S1, S2)** — `appObjects` (10 files, 32 importers). Status: done in the commit that adds
  it to `APP_PACKAGES`/`APP_MODULES`; 19 of the rewrites are inside the moved package.
- **T5 (S1, S2)** — `appEditors` (31 files, 82 importers).
- **T6 (S1, S2)** — `appPlugins` (47 files, 48 importers). Status: done in the commit that adds
  it to `APP_PACKAGES` with its three subpackages; one dynamic
  `importlib.import_module("appPlugins.ToolMilling")` target in a test came along.
- **T7 (S1, S2, S3)** — `tclCommands` (76 files, 149 import statements) with the discovery prefix
  derived from `__name__` and a registry test that fails when it comes back empty. Status: done
  in the commit that adds `tests/test_tcl_registry.py`; 101 registered aliases before and after.
- **T8 (S1, S2)** — `appGUI` (86 files, 290 importers), the largest slice, last so it lands on a
  tree where every other package already moved. Status: done in the commit that adds it to
  `APP_PACKAGES`; it needed one non-import edit, the VisPyData path in `appMain`.
- **T9 (S4, S5)** — Documentation and skills pass: `AGENTS.md`, `PACKAGING.md`,
  `.opencode/skills/*`, and the repo map, for paths that kept the old root names.

Each task commits its tests, docs and packaging edits together, and the tree is importable and
green at every commit.

## Log

- **L1 — Original request (verbatim)**: "yo pensaba que ibamos a tener una estructura tipo dos
  carpetas, src y test y dentro de ellas los modulos y demas...."
- **L2 — User selected (verbatim option text)**: "B — consolidar en flatcam_plus/ sin src/" with the
  description "Mitad del camino: los 8 paquetes pasan a subpaquetes. 1206 imports, sin tocar el
  modelo de instalación." and the preview showing `flatcam_plus/` holding `appGUI/`, `appObjects/`,
  `appPlugins/`, `tclCommands/`, `descartes/` and `libs/`, with `flatcam.py` and `tests/` at the
  root. This supersedes the "modules only" reading of S4 that T4.1–T4.7 implemented.
- **L3 — Surface measured before any write**: see S2. The two non-mechanical points are
  `tclCommands/__init__.py:110` (literal prefix and `split('.')[1]`) and the per-package
  `--collect-submodules` entries in `packaging/linux/build_linux_portable.sh`,
  `packaging/macos/build_macos_dmg.sh`, `packaging/windows/build_windows_installer.ps1` and the
  legacy `build_standalone.ps1`.
- **L4 — Why `src/` was not chosen**: it needs an installable package (it reverses D5,
  `[tool.uv] package = false`), `pythonpath`/`--paths` for `src`, and a resource root for the data
  directories; the human picked the half step, so none of that is in scope.
- **L5 — L3's measurement was inflated, and T1 is done**: L3 counted import statements with a
  repository-wide grep, which also matched the `.git/gentle-ai/candidate-views` snapshot copies;
  the real worktree counts are the ones now in S2, roughly half of what L3 recorded (`appCommon`
  was 16, not 32). T1 moved the package (five staged renames, no new `__init__.py` needed) and
  rewrote its 16 live import statements plus one commented one, retired the `appCommon` entry from
  the four build scripts and both `PACKAGING.md` blocks, and extended the layout guard with an
  `APP_PACKAGES`/`APP_MODULES` pin. RED: seven guard cases failed, naming `flatcam.py` as the
  last old-name importer; GREEN: 53 in that file. Mutation check: pointing
  `appObjects/AppObjectTemplate.py` back at `from appCommon.Common import LoudDict` fails the guard
  by path. 125 tests before, 132 after; no statement outside an import line changed.
- **L6 — T2 done and done inline**: `appHandlers` is small enough that a worker handoff would have
  cost more than the change: `git mv appHandlers flatcam_plus/appHandlers`, two import lines in
  `flatcam_plus/appMain.py`, the `--collect-submodules appHandlers` entry retired from the four
  build scripts and from both `PACKAGING.md` snippets, and the guard extended. RED: five guard
  cases failed. Mutation check: pointing `appMain`'s `appIO` import back at `appHandlers` fails the
  guard by path and makes `flatcam_plus.appMain` unimportable, which is the intended loud failure.
  132 tests before, 137 after.
- **L7 — T3 done**: `git mv appParsers flatcam_plus/appParsers` (seven modules plus the empty
  `__init__.py` it already had), 26 import statements rewritten across 22 files, the
  `--collect-submodules appParsers` entry retired in the four build scripts and both `PACKAGING.md`
  snippets, and `AGENTS.md` plus the repo-map skill repointed. RED: ten guard cases failed, naming
  `tests/test_excellon_parse.py` as a root-name importer; GREEN: 68 in that file, and the boot,
  Gerber, Excellon and HPGL2 tests together. Mutation check: pointing `ToolIsolation.py` back at
  `from appParsers.ParseGerber import Gerber` fails the guard by path and makes `appMain`
  unimportable. 137 tests before, 147 after. Two honest leftovers, both pre-existing and out of
  this slice's surfaces: the modules still log their old dotted names (`appParsers.ParseExcellon`,
  four in `ParseGerber`), and `pyproject.toml`'s comment plus the `locale/*.po` source references
  still name the root path.
- **L8 — T4 done, no cycle**: `appObjects` moved with its existing empty `__init__.py`; 32 import
  statements rewritten (19 of them inside the package itself), the build-script entry retired in
  the four scripts and both `PACKAGING.md` snippets, and four skill files plus the `AGENTS.md` row
  repointed. The cycle risk the spec warned about did not materialise: `camlib` imports no
  `appObjects` module, and each of the nine modules imports cleanly in a fresh interpreter. RED:
  twelve guard cases; GREEN: 80 in that file. Mutation check: reverting one intra-package import in
  `ObjectCollection.py` fails five guard cases by path and makes the boot test fail collection with
  `ModuleNotFoundError`. 147 tests before, 159 after. Leftovers recorded, not fixed: two prose
  references to the old path (`ToolNCC.py` docstring, a `test_gcode_output.py` comment) and the
  pre-existing `.po` source references and one log string.
- **L9 — T5 done after a failed worker report**: the worker that executed this slice reported an
  error after finishing the work, so the slice was verified before it was trusted rather than
  rerun: `git status` showed the 31 staged renames plus the import rewrites, `grep` found zero
  old-name importers and zero `--collect-submodules appEditors` entries, the guard carried the
  package and its three subpackages, and the suite was green. Diffs sampled on two application
  files change one import line each; `appEditors` moved with its `__init__.py` and each of the
  three plugin subpackages too. 159 tests before, 165 after. The lesson is recorded rather than
  acted on: a failed worker is not evidence that its side effects are partial, and the checks that
  prove the tree consistent (grep for the old name, grep for the collect entry, the layout guard,
  the suite) are the same ones the slice needed anyway.
- **L10 — T6 done**: `appPlugins` moved with its three subpackages and its LICENSE files; 48
  import statements rewritten, including the 29 in the package's own `__init__.py` and the
  `try/except ImportError` wrapper around `ToolImage`, plus one dynamic
  `importlib.import_module("appPlugins.ToolMilling")` target in a test that no import rewrite would
  have caught on its own. The build-script entry is retired in all six places and the prose
  repointed in `AGENTS.md` and four skill files. RED: six guard cases, naming
  `MachinePrefGroupUI.py`; GREEN: 92 in that file, and the boot test with its plugin-count and
  preprocessor-registry assertions. Mutation check fails the guard by path and makes `appMain`
  unimportable. 165 tests before, 171 after. Leftovers recorded: `README.md`, `CHANGELOG.md`,
  `.kiro/**`, `locale/**/*.po`, the `pyproject.toml` comment and one preprocessor comment still
  name the old path in prose, which is the T9 pass's job.
- **L11 — T7 done, and the silent failure was reproduced before it was fixed**: the discovery now
  derives its prefix as `'{}.TclCommand'.format(__name__)` and takes the class name with
  `key.rsplit('.', 1)[-1]`. The registry test was written before the fix and against the real
  post-move state, where it failed with `assert 0 >= 100` while the application logged "TCL Shell
  has been initialized." and booted normally: exactly the failure mode S3 predicted, and one the
  layout guard never sees. Mutation B (reverting both halves of the discovery) fails all eleven
  registry cases and leaves the layout guard green, which is why the second test exists. Registered
  aliases through `app.shell.tcl_commands_storage`: 101 before the move, 101 after. One import
  needed more than a path rewrite: `ToolShell.py` used `import tclCommands` and called
  `tclCommands.register_all_commands`, so it became `from flatcam_plus import tclCommands` to keep
  the call site verbatim instead of rebinding `flatcam_plus`. 171 tests before, 186 after.
- **L12 — T8 done, and it caught a path that only the move could break**: `appGUI` moved with its
  eleven `__init__.py` files and its three tracked VisPy data files; 290 import statements were
  rewritten in 149 files, 130 of them inside the moved package. The slice is the one that needed a
  non-import edit: `appMain`'s VisPyData fallback built its path as `_APP_ROOT/appGUI/VisPyData/data`
  and the directory now sits inside the package, so the fallback would have re-raised
  `FileNotFoundError`. It now resolves through `flatcam_plus/appGUI/VisPyData/data`. The worker also
  replayed the rewrite over `git show HEAD:appGUI/<file>` for all 86 modules and diffed the result
  against the new files to prove no line beyond the import moved (`checked=86 unexpected_diffs=0`).
  RED: four guard cases, naming `flatcam.py`; GREEN: 100 in that file, plus the boot, locale, path
  and recent-project tests. Mutation check fails the guard by path. 186 tests before, 190 after.
  With this slice no build script collects a package that lives inside `flatcam_plus`: the four
  scripts and both `PACKAGING.md` snippets now name only `flatcam_plus`.
  **This slice did not land as one commit.** A single commit for it measures 179 changed paths and
  145 KB of diff, and the native reviewer refused it in preflight with `lens_context_budget_exceeded`
  twice: once from the session that opened it and once from a fresh session that retried the exact
  recipe. Neither attempt created authority, so nothing was left `reviewing`. It is split in two.
  `e7713b2` moved the `preferences` subtree first, because it is the leaf of the package's import
  graph: its imports of the core widgets (`appGUI.GUIElements`, `appGUI.PanelStyles`,
  `appGUI.ColumnarFlowLayout`) keep resolving against the root copy that this commit moves, so both
  commits leave the application importable and the suite green (75 paths and 64 KB of diff in the
  first, the rest here). The first commit also fixed the guard artefact that made the split painful
  and that had already forced four hand cleanups during L15: the root-copy guards now ignore a
  leftover directory that holds nothing but `__pycache__`.

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
  tree where every other package already moved. Status: done in three commits (`e7713b2`,
  `c47338e`, `01a51b5`) because the single-commit form exceeds the reviewer budget (L17); each
  lands its own part of `APP_PACKAGES`, and the last one pins `appGUI` with its `preferences`
  subpackage. It needed one non-import edit, the VisPyData path in `appMain`.
- **T9 (S4, S5)** — Documentation and skills pass: `AGENTS.md`, `PACKAGING.md`,
  `.opencode/skills/*`, and the repo map, for paths that kept the old root names. Status: done
  in the commit that repoints `README.md`, the `pyproject.toml` comment, the four prose lines
  left in code, and the per-package comment above `--collect-submodules flatcam_plus`.

Each task commits its tests, docs and packaging edits together, and the tree is importable and
green at every commit.

## Final state

All nine tasks are done, and the tree was importable and green at every commit. T1 to T7 and T9 are
one commit each; T8 is three, because a single commit for it exceeded the reviewer's lens context
budget (L17):

```
flatcam.py                    launcher, unchanged location (PyInstaller entry point)
flatcam_plus/                 307 .py
  appCommon/ appEditors/ appGUI/ appHandlers/ appObjects/
  appParsers/ appPlugins/ tclCommands/     the eight application packages
  appMain.py appTranslation.py appTool.py appPreProcessor.py
  camlib.py defaults.py appDatabase.py appProcess.py appWorker.py appWorkerStack.py version.py
  descartes/ libs/                        the vendored trees
assets/ config/ locale/ preprocessors/     data, still at the root, resolved through _APP_ROOT
tests/ odd/ packaging/ scripts/ doc/
```

No `app*` directory is left at the root, no build script collects a package that no longer exists
there, and no `sys.modules` shim was added anywhere: the import rewrites travelled with each move.
The suite went from 125 to 190 tests, and the two new guard families are the durable part:
`tests/test_package_layout.py` pins every package and its modules, and `tests/test_tcl_registry.py`
pins the one registration path that fails silently.

What is still unverified, in the same terms the previous feature recorded: **no packaged build was
produced**. The four build scripts lost a `--collect-submodules` line each and the Windows ones
were never parsed by PowerShell; that the app still runs from source is proven by the boot test on
every commit, that it still runs from a bundle is not.


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
- **L13 — T9 done, and the line drawn through the remaining old-path references**: the pass
  repointed `README.md` (twelve references), the `pyproject.toml` comment that still claimed the
  application packages were root directories, the vacuous "appCommon is a subpackage now" comment
  above `--collect-submodules flatcam_plus` in two build scripts and `PACKAGING.md`, and the four
  prose lines left in code (`tests/test_defaults_coverage.py`, `tests/test_gcode_output.py`,
  `preprocessors/GRBL_11_pen_plotter.py`, `flatcam_plus/defaults.py`). It deliberately left
  `CHANGELOG.md`, `.kiro/**` and `locale/**/*.po`: the first two are historical records where the
  old paths describe what was true when they were written, and the `.po` `#:` lines are xgettext
  source references that the next extraction regenerates. Every current, user-facing or executable
  reference now names `flatcam_plus/<package>/`. 190 tests still pass; the pass touches no import.
- **L14 — Native review of the documentation slice, and why the feature cannot be one candidate**:
  `assess` over the whole feature (`7e8721e..a6fe2ea`) reports **579 changed paths and 318 211
  changed lines** at tier high. A candidate that size cannot be captured: the lens prompt is built
  from the frozen trees, and the previous feature already hit ~199 KB per lens at 178 paths, so one
  transaction for all eight moves would end in `lens_context_budget_exceeded`. The review therefore
  ran on the last unit, `48bb3c8..a6fe2ea` (the documentation and prose pass, 10 files, 87 lines).
  The provider rated it **high** because the pass touches `packaging/linux/build_linux_portable.sh`
  and picked all four lenses by default; the four runs were cheap (≈29.7 KB prompts) and the review
  closed **approved with no finding at all**, acknowledged and burned
  (`review-9dfb095a62e5d124`, consumed revision `sha256:89be42f7...`). One facade note for the next
  session: the first group submission was rejected as "not the complete distinct group" because the
  bindings had been retyped from the status output; resubmitting them byte-identical from a fresh
  STATUS worked. **The eight code slices of this feature were not natively reviewed as individual
  candidates**: they were verified per slice by a worker with RED/GREEN, a mutation check and the
  layout guard, and by the parent on the combined tree (190 tests, the boot test, the Tcl registry
  test). Whether to spend eight more review transactions on them is the human's call, and it is the
  only outstanding question this feature leaves.
- **L15 — The eight slices reviewed one by one, seven approved and the last one pending**: because a
  native review always compares base..HEAD of the *current worktree*, each slice had to be reviewed
  with its own tip checked out (detached), in order. Seven of the eight closed **approved** with no
  severe finding, so no slice needed a refuter or a correction; the advisories are all
  informational and none was fixed, because every one of them points at the task document or at a
  test threshold rather than at code: T1 `review-59bee28f11872d09` (R2-001, this document's S2
  block), T2 `review-0306909096bf363e` (none), T3 `review-6e8a2da0caf5d695` (R2-001, this
  document's T3 line), T4 `review-fdf7f1b887f70ad7` (R2-001, this document's T4 line), T5
  `review-671d7a047c3f0281` (none), T6 `review-8fd6d486289a04b3` (R2-001 the `try/except ImportError`
  block in `appPlugins/__init__.py`, R2-002 this document's T6 line) and T7
  `review-0f5b918982c5ea47` (R2-001 and R3-001 on `tests/test_tcl_registry.py:35`, the `>= 100`
  lower bound, and R2-002 on the guard entries). **T8 (`appGUI`) was not reviewed in that session**:
  it reached its context budget before the transaction, and a half-run review would have left the
  authority `reviewing` instead of closing it. It was reviewed later, in three slices (L17).
- **L16 — A guard artefact worth fixing**: `tests/test_package_layout.py`'s
  `test_no_root_copy_of_the_app_package_is_left_behind` asserts the root directory is gone, and a
  `git checkout` back to an older commit leaves the moved directory behind as soon as it holds
  nothing but an ignored `__pycache__`. That false failure hit four of the eight checkouts and had
  to be cleared by hand with `rm -rf <package>` before the suite was green. The assertion should
  ignore a directory that contains no tracked file, which is a one-test change.
- **L17 — T8 split in three commits because the reviewer budget refused it, and reviewed slice by
  slice**: the single T8 commit (`48bb3c8`, base `d5ba3f0`) measures 179 changed paths and 145 KB of
  diff, and the provider refused it in preflight with `lens_context_budget_exceeded` twice, once
  from the session that opened it and once from a fresh session that retried the exact recipe.
  Neither attempt created authority, so nothing was left `reviewing` and nothing needed repair.
  The scope cannot be reduced inside one candidate: it is a single commit, so no smaller committed
  range covers part of it, and there is no path filter. It was therefore split into three commits
  whose trees are identical to the single one at the end (the only additions are the guard fix of
  L18 and this record):
  - `e7713b2` moves the `preferences` subtree. It is the leaf of the package's import graph, so its
    imports of the core widgets keep resolving against the root copy the next commit moves. 75
    paths, 64 KB of diff, 188 tests green. Reviewed as `review-0906de9d8c737362`, tier medium,
    lenses `readability` and `reliability`, **approved** with one advisory: R3-001 (reliability,
    `tests/test_package_layout.py:164-167`, WARNING) on the root-copy guard; acknowledged and
    burned.
  - `c47338e` moves the three widget modules (`GUIElements`, `PanelStyles`, `ColumnarFlowLayout`)
    and rewrites the 140 import sites that name them in the same commit. 141 paths, 96 KB. Reviewed
    as `review-59a25978393746f5`, tier high (a preferences module trips the process scan), lenses
    `readability` and `reliability`, **approved with no finding**; the first group submission was
    refused at admission because a reviewer payload carried two JSON objects, the slot was not
    consumed, and the reoffered slot produced a clean result; acknowledged and burned.
  - `01a51b5` moves the remaining core modules, the `themes` subpackage, the VisPy data files and
    the package `__init__`, repoints the last root-name sites, and pins `appGUI` in the layout
    guard. 42 paths, 32 KB. Reviewed as `review-b7d8875515475323`, tier high (the packaging scripts),
    lenses `readability` and `reliability`, **approved** with one advisory: R2-001 (readability,
    `odd/tasks/package-consolidation.md:66`, SUGGESTION) on this document's T8 line; acknowledged
    and burned. `git diff 48bb3c8 01a51b5` showed only the L18 guard fix and this document.
  Only T8's code needed slicing: it is the only slice near the budget. The eight slices before it
  fitted as single commits, and the documentation pass (10 files, 87 lines) was reviewed in L14.
- **L18 — The guard artefact of L16 fixed, and it earned its keep during the split**:
  `tests/test_package_layout.py` now decides through `holds_no_package_files`, which walks the
  leftover path and treats a `__pycache__` directory and `.pyc`/`.pyo` files as something a fresh
  interpreter regenerates rather than as a copy of the package. Both root-copy guards (application
  packages and vendored packages) use it, and two `tmp_path` cases pin the rule in both directions
  so a later simplification back to `os.path.exists` fails. RED was the real artefact, not a
  contrived one, and it also bit the split itself: checking out `d5ba3f0` left `__pycache__`
  directories occupying the destination paths of `flatcam_plus/appGUI/`, so the first `git mv`
  nested the tree one level too deep and had to be undone. Mutation check: adding
  `appGUI/MainGUI.py` fails the guard. The full suite is green at all three commits.

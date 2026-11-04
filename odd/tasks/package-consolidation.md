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
- **T2 (S1, S2)** — `appHandlers` (3 files, 4 importers).
- **T3 (S1, S2)** — `appParsers` (8 files, 51 importers).
- **T4 (S1, S2)** — `appObjects` (10 files, 63 importers).
- **T5 (S1, S2)** — `appEditors` (31 files, 82 importers).
- **T6 (S1, S2)** — `appPlugins` (47 files, 96 importers).
- **T7 (S1, S2, S3)** — `tclCommands` (76 files, 298 importers) with the discovery prefix derived
  from `__name__` and a registry test that fails when it comes back empty.
- **T8 (S1, S2)** — `appGUI` (86 files, 580 importers), the largest slice, last so it lands on a
  tree where every other package already moved.
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

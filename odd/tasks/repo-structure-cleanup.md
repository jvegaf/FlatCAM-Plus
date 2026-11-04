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
- **S3 — Phase 2: red de seguridad (proposed, not yet authorized).** "Tests y CI para el
  arranque de la app y los dominios críticos, como prerequisito de cualquier reorganización de
  ficheros."
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
- **T3 (S3)** — Add a startup smoke test and a CI workflow. Route: pending.
- **T4 (S4)** — Move the root modules into a package. Route: pending, blocked on T3.

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

This feature's slice is T1+T2: 14 files, 84 insertions, 137 deletions, committed as
`aedf5e7`.

`dev` is 13 commits and roughly 4726 authored lines ahead of `origin/main` (lock files
excluded), which is well past one review slice. That backlog predates this work. Push, pull
request creation and merge remain human decisions and must account for it.

## Known follow-ups

- `packaging/windows/build_windows_installer.ps1` does not collect `certifi` or
  `google.protobuf`; only the legacy `build_standalone.ps1` does. Verify whether the canonical
  Windows build needs them.
- `requirements.txt` remains a hand-maintained mirror of `pyproject.toml` and can drift again.
  A platform-aware generator would be the durable fix; `uv export` cannot express it today.
- No CI, lint, formatter or type-check configuration exists. T3 is where that starts.

## Next step

Start T3, not T4. With 3 test files and no CI, moving 210 import sites is the unhedged bet this
cleanup was designed to avoid. T3 deliverables: a headless startup smoke test, one test per
critical domain, and a CI workflow that runs `uv sync` plus the suite.

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

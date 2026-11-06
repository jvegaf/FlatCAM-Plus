# Package homogenization: launcher and runtime data inside `flatcam_plus/`

Move the root launcher and every runtime data directory into the `flatcam_plus/`
package, make the project a real installable package, then release as `1.3.2`.

## Specs

- **S1 — One tree.** The repository root holds no runtime artifact: `flatcam.py`,
  `assets/`, `config/`, `locale/` and `preprocessors/` all live under
  `flatcam_plus/`. Root keeps only `flatcam_plus/`, `tests/`, `packaging/`,
  `odd/`, `scripts/`, `doc/`, `build/`, `dist/` and the project files
  (`pyproject.toml`, `uv.lock`, `README.md`, `AGENTS.md`, `PACKAGING.md`,
  `Makefile`, `requirements.txt`, `.python-version`, the platform wrappers).
- **S2 — No root launcher, no shim.** `flatcam.py` is deleted. The launcher
  becomes `flatcam_plus/launcher.py` exposing `main()`, and
  `flatcam_plus/__main__.py` invokes it. There is exactly one way to start the
  application from source.
- **S3 — Installable package.** `[build-system]` is restored with the `uv_build`
  backend, `[tool.uv] package = false` is removed, and
  `[project.scripts]` declares `flatcam-plus = "flatcam_plus.launcher:main"`.
- **S4 — Data ships in the package.** A wheel built with `uv build` contains
  `flatcam_plus/assets`, `flatcam_plus/config`, `flatcam_plus/locale` and
  `flatcam_plus/preprocessors`, and the installed application resolves all four
  from the package directory.
- **S5 — Version resolves in every mode.** `APP_VERSION` is correct in three
  modes — editable checkout, installed wheel, PyInstaller bundle — without
  requiring a `pyproject.toml` that sits beside the package. Installed mode reads
  distribution metadata; the checkout and frozen fallbacks keep working.
- **S6 — Build scripts follow the package.** Every PyInstaller invocation uses
  `flatcam_plus/launcher.py` as entry and ships the data to
  `flatcam_plus/{assets,config,locale,preprocessors}`:
  `packaging/linux/build_linux_portable.sh`,
  `packaging/macos/build_macos_dmg.sh`,
  `packaging/windows/build_windows_installer.ps1`,
  `build/pyinstaller/linux/FlatCAM-Plus.spec`, and `run_flatcam.bat`.
- **S7 — Both entry points work.** `python -m flatcam_plus` and the
  `flatcam-plus` console script both start the application.
- **S8 — Suite green.** `uv run --with pytest pytest tests -q` passes, including
  the app boot fixture, the frozen-layout guards and the CLI option tests, all
  updated to the new layout.
- **S9 — Release 1.3.2.** `pyproject.toml` `[project] version` is `1.3.2`,
  `packaging/aur/PKGBUILD` `pkgver=1.3.2`, `APP_VERSION_DATE` matches, an
  annotated tag `v1.3.2` exists and is pushed to `origin`.
- **S10 — Documentation matches reality.** `AGENTS.md`, `PACKAGING.md`,
  `.opencode/skills/*`, `flatcam_plus/__init__.py` and the `pyproject.toml`
  comments describe `python -m flatcam_plus` / `flatcam-plus` and never instruct
  `python flatcam.py`.
- **S12 — macOS is not a target.** macOS is not supported. The repository ships
  no macOS packaging script or wrapper, and no document advertises macOS as a
  delivery target. Runtime comments and code branches that mention macOS stay,
  because they describe shared Unix behaviour rather than a support promise.
- **S11 — Observable paths unchanged.** Icons, translations, preprocessors,
  shipped examples and the Windows `config/configuration.txt` lookup resolve to
  the same files as before the move. `App.app_home` becomes the package
  directory; that is the only intended semantic change and it is documented.

## Tasks

| ID | Task | Specs | Route | Status | Commit |
| --- | --- | --- | --- | --- | --- |
| T1 | Move `assets/`, `config/`, `locale/`, `preprocessors/` into `flatcam_plus/` and re-anchor `_APP_ROOT`, `appTranslation` and the Windows config paths | S1, S4, S11 | inline | done | `1e4ae8f` |
| T2 | Move the launcher to `flatcam_plus/launcher.py` + `__main__.py`, delete root `flatcam.py` | S2, S7, S11 | inline | done | `defdd5f` |
| T3 | Restore `[build-system]`, drop `package = false`, add `[project.scripts]` and package data | S3, S4 | inline | done | `a367ea2` |
| T4 | Resolve `APP_VERSION` through distribution metadata with checkout/frozen fallbacks | S5 | inline | done | `a367ea2` |
| T5 | Point the four build scripts, the spec and `run_flatcam.bat` at the package entry and destinations | S6, S11 | inline | done | `274119f` |
| T6 | Update the suite: boot fixture, path guards, frozen layout, CLI options, package layout | S8 | inline | done | `a367ea2`, `274119f`, `9c01ea9` |
| T7 | Update `AGENTS.md`, `PACKAGING.md`, the project skills and package docstrings | S10 | inline | done | `9c01ea9` |
| T8 | Bump to 1.3.2, run the full suite and `uv build` proof | S9, S4 | inline | done | `669a3b9` |
| T9 | Create the annotated `v1.3.2` tag; the human pushed `dev` and the tag after the agent could not authenticate | S9 | inline | done | `669a3b9` |
| T10 | Close the native review lineage: refuter, bounded correction, targeted-validator retry, acknowledgement | S8 | inline | done | none (authority burned) |
| T11 | Remove the unsupported macOS packaging surface and document the supported targets | S12 | inline | done | `0146dbc` |

## Log

- **L1 — Original request (verbatim):** "pues debemos meter tanto flatcam.py como
  las cosas que sean necesarias (preprocessors, locale....) dentro de flatcam_plus
  para que sea homogeneo. y cuando este todo funcionando, subimos la version a
  1.3.2 y creamos tag"
- **L2 — Decision, entrypoint model:** the project becomes an installable package
  with a `flatcam-plus` console script (option A of the questionnaire). Explicitly
  reverses D5 from `repo-structure-cleanup.md`; `uv build` must be proven before
  the release, because D5 was reversed once when `uv_build` packaged only a stub.
- **L3 — Decision, root launcher:** `flatcam.py` is deleted outright. No
  compatibility shim, so the build scripts and `run_flatcam.bat` must be updated
  (option A, "Borrar del todo").
- **L4 — Decision, tag:** the annotated tag `v1.3.2` is created **and pushed**,
  which triggers `.github/workflows/release.yml` (`tags: ["v*"]`). Authorized in
  the questionnaire; gated on T8 being green so publish is never the debugging
  step.
- **L5 — Measurement, `_APP_ROOT`:** `flatcam_plus/appMain.py:130` is
  `os.path.dirname(os.path.dirname(os.path.realpath(__file__)))` and
  `flatcam_plus/appTranslation.py:70` uses the same depth, so both collapse to
  `dirname(realpath(__file__))` once the data directories move inside the package.
- **L6 — Measurement, `app_home` consumers:** `app_home` feeds `os.chdir`
  (`appMain.py:590`), `resource_location` (`:636,638,642`), the preprocessor glob
  (`appPreProcessor.py:160`) and `options["root_folder_path"]` (`:1116`). In an
  installed wheel there is no data directory beside the package, so `app_home`
  must become the package directory; S11 records that as the intended change.
- **L7 — Measurement, packaging surface:** data arguments live at
  `packaging/linux/build_linux_portable.sh:193-197`,
  `packaging/macos/build_macos_dmg.sh:218-222`,
  `packaging/windows/build_windows_installer.ps1:342-346` and
  `build/pyinstaller/linux/FlatCAM-Plus.spec:5`.
- **L8 — Measurement, path guards:** `tests/test_app_paths.py:32-42`,
  `tests/test_locale_resolution.py:15,19,35-55`,
  `tests/test_frozen_layout.py:36-40,62-90`,
  `tests/test_cli_options.py:20-21` and `tests/test_app_boot.py:33-36` pin the
  current layout and must move with it.
- **L9 — Evidence, wheel contents (S4).** `uv build --wheel` with the `uv_build`
  backend produced a 1149-entry wheel carrying `flatcam_plus/assets/resources` (694 files),
  `flatcam_plus/assets/examples` (12), `flatcam_plus/config` (1),
  `flatcam_plus/locale` (31) and `flatcam_plus/preprocessors` (30), with no
  `__pycache__` and no `pyproject.toml`. The absent manifest is why S5 needed
  the distribution-metadata fallback.
- **L10 — Evidence, frozen entry script (S2, S11).** PyInstaller runs the entry
  script as `__main__`, so a launcher that anchors on its own `__file__` would
  resolve `_MEIPASS` instead of `_MEIPASS/flatcam_plus`. `flatcam_plus/launcher.py`
  therefore anchors `_PACKAGE_DIR` on `flatcam_plus.__file__`, which is correct in
  a checkout, an installed wheel and a frozen bundle.
- **L11 — Evidence, T5 guard discriminates.** The updated
  `tests/test_frozen_layout.py` destination rule rejects the pre-change scripts:
  running it against `git show HEAD:packaging/{linux,macos}/...` flags four
  destinations per script (`assets`, `config`, `locale`, `preprocessors`).
- **L12 — Evidence, T1 RED/GREEN.** RED: `tests/test_app_paths.py` and
  `tests/test_locale_resolution.py` updated first, 4 failures for exactly the new
  expectations. GREEN after the move and the anchor changes: 16 passed including
  `tests/test_app_boot.py`. Committed as `1e4ae8f`.
- **L13 — Evidence, T2 RED/GREEN.** `tests/test_cli_options.py` repointed at
  `python -m flatcam_plus` with `PYTHONPATH` on the repository root; 2 passed.
  Committed as `defdd5f`, together with the removal of the root launcher.
- **L14 — Evidence, T3/T4.** `uv sync` builds and installs `flatcam-plus==1.3.1`
  in editable mode; `importlib.metadata.version("flatcam-plus")` answers, and the
  15 cases in `tests/test_version_module.py` pass, including the new
  installed-distribution fallback and the neither-source-answers error.
- **L15 — Review lineage opened (S6–S8 evidence).** Full suite green at 255 passed.
  `review.start` created lineage `review-f9e25ded857d6f61` (tier high, 382 changed
  lines, correction budget 191) with lenses risk, resilience, readability and
  reliability. The group forecast was 4 model runs; the refuter forecast was 1.
- **L16 — CRITICAL finding R1-001, accepted as correct.**
  `flatcam_plus/assets/linux/flatcam-beta:8` ran `python3 -m flatcam_plus` from the
  caller's cwd, so a same-named package in that directory shadowed the application
  through `sys.path[0]`. Reproduced: without `-P` the cwd package wins; with `-P`
  the real package resolves. Corrected with `python3 -P -m flatcam_plus`.
- **L17 — Self-reported discrepancy.** The correction plan declared 3 diff lines;
  the delivered correction is 4 diff lines (3 insertions, 1 deletion), because the
  two explanatory comment lines were not counted. Still far inside the frozen
  budget of 191, but the plan was under-declared by one line.
- **L18 — Blocker, validator capture rejected.** After the correction, STATUS moved
  to `targeted_validation_required` and issued one `provider_targeted_validator`
  collect input. `gentle_review_capture` rejected it three times as
  "collectBinding is missing or stale for current STATUS": once as the parsed inner
  binding, once as the provider-serialized string, once as the complete entry
  including `validationRequest`. The STATUS is stable across queries (same
  request_hash, expected_revision and correction target), so the binding is not
  being regenerated. No provider token was altered and no fourth attempt was made.
  The validator produced no verdict, so the lineage cannot close without a human
  decision.
- **L19 — Review closed approved.** After the group relay died on `review-risk`
  (transport failure), the sanctioned continuation was one-slot captures: risk,
  resilience and readability were admitted first try, reliability failed once and
  passed on the single reoffered retry. Final state `approved`, authority burned
  (`gentle-ai.review-acknowledged/v1`). Six advisory findings, all informational:
  R2-001/R2-002/R2-003 (SUGGESTION) on `tests/test_frozen_layout.py:20`,
  `:106` and `flatcam_plus/assets/linux/flatcam-beta:7`; R3-001 (WARNING) on
  `tests/test_frozen_layout.py:106-109`; R3-002 (SUGGESTION) on
  `tests/test_version_module.py:143-144`; R4-001 (WARNING) on
  `tests/test_frozen_layout.py:106`. None opens a correction.
- **L20 — Orphaned first lineage explained.** `inspect` on the corrected tree
  reported `applicability: unrelated` with `repair.counts.lineages: 0`, so
  `review-f9e25ded857d6f61` was invisible to the target-scoped authority store.
  That, not a transcription error, is why its validator binding read as "missing
  or stale".
- **L21 — Release verified.** `uv sync` installs `flatcam-plus==1.3.2`;
  `APP_VERSION` and `APP_VERSION_DATE` read `1.3.2` / `2026.11.06`; the full suite
  is 255 passed; `uv build` produces `flatcam_plus-1.3.2-py3-none-any.whl` with
  1149 entries including `assets/resources` (694), `config/configuration.txt`,
  `locale` (31), `preprocessors` (30), `launcher.py` and `__main__.py`.
- **L22 — Blocker, push unauthenticated.** `git push origin dev` and
  `git push origin v1.3.2` both fail with `could not read Username for
  'https://github.com'`. There is no `credential.helper`, `gh auth status` reports
  no logged-in host, and there is no `~/.ssh`. The annotated tag `v1.3.2` exists
  locally on `669a3b9`. Publishing needs the human to authenticate; no workaround
  was attempted and no credential was requested in chat.
- **L23 — Release closed.** Run `42278173633` finished `completed success` in
  18m 9s and published five assets for `v1.3.2`: the Windows installer, the Linux
  portable tarball, the `.deb`, the `.rpm` and the Flatpak bundle. No `.dmg`.
  Checked against `v1.3.1`, which has the same five, and against
  `.github/workflows/release.yml`, which has only `ubuntu-24.04` and
  `windows-latest` jobs: macOS was never in CI, so the missing `.dmg` is not a
  regression.
- **L24 — Push needed the human.** `git push` failed twice from the agent with
  `could not read Username for 'https://github.com'`. The agent process runs with
  `HOME` and `XDG_CONFIG_HOME` under the Gentle Shell install tree and without
  `DBUS_SESSION_BUS_ADDRESS`, `XDG_RUNTIME_DIR` or an SSH agent, so it cannot read
  the keyring where `gh` stores the token. No credential was requested in chat and
  no workaround was attempted; the human pushed both the branch and the tag.
- **L25 — Decision, GitHub MCP rejected as a fix (L24 follow-up).** A GitHub MCP
  server would not unblock `git push`: it speaks the REST API, `push` is a git
  protocol operation, the API commit path synthesises new objects (which would
  desynchronise the local history and the annotated tag), and its `env`/`headers`
  token sources execute inside the same credential-starved process. Recorded so
  the idea is not re-proposed as a solution to this specific blocker.
- **L26 — Decision, macOS dropped.** The human stated macOS is not supported.
  `packaging/macos/build_macos_dmg.sh`, `FlatCAMPlus_macos_dmg_generator.command`,
  the whole DMG recipe in `PACKAGING.md`, the README bullet, the AGENTS.md wrapper
  entry and the two guard entries were removed (`0146dbc`, −450/+7). The full
  suite passed afterwards: 255. Runtime comments and the shared Unix branch stayed.
- **L27 — Follow-up, advisory findings.** The approved review left six
  informational findings, none blocking. Three of them (R2-002, R3-001, R4-001)
  point at the same place, `tests/test_frozen_layout.py:106`, which is the guard
  that now decides bundle destinations. Worth a look before that guard grows.
- **L28 — Known deviation, published artifacts.** The `v1.3.2` tag points at
  `669a3b9`, which still contained `packaging/macos/`. The release artifacts
  therefore ship a script the tree no longer has. A `1.3.3` is required to reflect
  the removal; re-tagging `v1.3.2` is not an option because that tag is consumed.

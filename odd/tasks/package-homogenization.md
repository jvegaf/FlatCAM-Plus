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
- **S11 — Observable paths unchanged.** Icons, translations, preprocessors,
  shipped examples and the Windows `config/configuration.txt` lookup resolve to
  the same files as before the move. `App.app_home` becomes the package
  directory; that is the only intended semantic change and it is documented.

## Tasks

| ID | Task | Specs | Route | Commit |
| --- | --- | --- | --- | --- |
| T1 | Move `assets/`, `config/`, `locale/`, `preprocessors/` into `flatcam_plus/` and re-anchor `_APP_ROOT`, `appTranslation` and the Windows config paths | S1, S4, S11 | inline | |
| T2 | Move the launcher to `flatcam_plus/launcher.py` + `__main__.py`, delete root `flatcam.py` | S2, S7, S11 | inline | |
| T3 | Restore `[build-system]`, drop `package = false`, add `[project.scripts]` and package data | S3, S4 | inline | |
| T4 | Resolve `APP_VERSION` through distribution metadata with checkout/frozen fallbacks | S5 | inline | |
| T5 | Point the four build scripts, the spec and `run_flatcam.bat` at the package entry and destinations | S6 | inline | |
| T6 | Update the suite: boot fixture, path guards, frozen layout, CLI options, package layout | S8 | inline | |
| T7 | Update `AGENTS.md`, `PACKAGING.md`, the project skills and package docstrings | S10 | inline | |
| T8 | Bump to 1.3.2, run the full suite and `uv build` proof | S9, S4 | inline | |
| T9 | Commit work units, create and push the annotated `v1.3.2` tag | S9 | inline | |

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

# Release pipeline and Linux packaging

Turns the repository from "build it yourself" into a tagged release with installable artifacts, and
gives the version a single source on the way. Written at sync time, after `v1.3.1` shipped; the Log
carries the requests verbatim and the evidence that shaped each decision.

## Specs

- **S1 — Targets (verbatim, L1):** "windows con instalador, y en linux debemos de tener deb, rpm,
  flatpak y aur", compatible with GitHub Actions so releases can be automated later.
- **S2 — Flatpak scope (verbatim, L2):** "flatpak de momento se generara el artefacto y lo
  meteremos la release." Self-hosted bundle, not a Flathub submission.
- **S3 — Windows verification (verbatim, L3):** "windows lo probaremos directamente disparando el
  workflow en el repositorio." No local Windows harness.
- **S4 — Efficiency (verbatim, L4):** "optimiza el workflow de github actions todo lo que puedas
  mediante caches o lo que sea."
- **S5 — Version policy (verbatim, earlier request):** the only source of truth for the version is
  `pyproject.toml`; patch bumps go through it and reach every artifact.

## Tasks

- **T1 (S5)** — Version single-sourcing: `pyproject.toml` owns it, `flatcam_plus/version.py` reads
  it at import time, the build scripts read the same file. Commit `c922651`.
- **T2 (S5)** — Ship the manifest in every bundle and in the documented manual recipes; the release
  helper stopped writing a slash date. Commits `225a7c7`, later corrected by `6ea84ca`.
- **T3** — Packaging prerequisites in code: `--version` (and `-h` exiting 0), the updater disabled
  when frozen, and a probe of the frozen layout. Commit `b3c372a`, corrected by `6b11b3f`.
- **T4 (S1)** — Linux packages: one `nfpm.yaml`, a launcher, desktop entry, AppStream metadata, a
  glibc floor gate, and the tag-driven release workflow. Commit `57ba41b`.
- **T5 (S2)** — Flatpak manifest and build script, published as an artifact. Commits `98bd9fa`,
  `f24b55d`, and the runner fixes `4c5a93d`, `9f96b7f`, `c4e9b80`.
- **T6 (S1)** — AUR `flatcam-plus-bin` PKGBUILD plus `update_aur.sh`. Commit `9b2fdc9`.
- **T7 (S4)** — Workflow cost: bounded jobs, prose-only commits skipped, superseded runs cancelled,
  wheel and runtime caches, no re-compression of already-compressed artifacts. Commits `81384af`,
  `ff82e2e`.
- **T8** — The release run itself: nine runner-only failures fixed (see the Log), ending in the
  published `v1.3.1` with five artifacts. Commits `3518a5e`, `3faf275`, `ac0eb26`, `60bd055`,
  `c95f5d1`, and the guard fix `f6d600b`.

## Decisions

- **D1 — A `-bin` AUR package, not a source build.** Arch's packaged `python-*` modules cannot
  satisfy `pyqt6==6.11.0`, `ortools` and `rasterio` for Python 3.14, so a source PKGBUILD would
  never resolve.
- **D2 — Flatpak wraps the same payload, self-hosted.** Flathub forbids shipping a prebuilt binary
  payload; a native port is a separate, larger project.
- **D3 — `gdal` removed.** Nothing imports it and it exists only as an sdist, so every clean
  `uv sync` tried to compile it and died on `gdal-config`; `rasterio` ships its own GDAL.
- **D4 — The glibc floor is 2.34.** It is dictated by the only x86_64 `pyqt6-qt6` wheel, not by
  preference, and it is exactly RHEL/Alma/Rocky 9.
- **D5 — Flatpak is not debug-stripped.** The payload is frozen; stripping it buys nothing and the
  `.Debug` runtime is never published.

## Log

- **L1 — Original request (verbatim)**: "tenemos que darle una vuelta a los builders, los targets a
  los que vamos a crear los instaladores son: windows con instalador, y en linux debemos de tener
  deb, rpm, flatpak y aur.Investiga una posible solucion, y que sea compatible con github actions,
  para que en un futuro generemos las releases automaticamente"
- **L2 — User (verbatim)**: "flatpak de momento se generara el artefacto y lo meteremos la release.
  Referente a la preferencia de check for updates, cuando ya tengamos todo el CI montado nos ponemos
  con ello"
- **L3 — User (verbatim)**: "windows lo probaremos directamente disparando el workflow en el
  repositorio"
- **L4 — User (verbatim)**: "y optimiza el workflow de github actiosn todo lo que puedas mediante
  caches o lo que sea, para que sea lo mas eficiente posible"
- **L5 — User (verbatim)**: "sube la patch version, comitea, crea el tag y te autorizo a que hagas
  push de todo"
- **L6 — Verification before release, all local**: the bundle builds inside
  `quay.io/pypa/manylinux_2_34_x86_64` with a managed interpreter (874 MB), the glibc gate reports
  `GLIBC_2.34 (promised 2.34)`, `nfpm` produces both packages from the real bundle, the `.deb`
  installs on Debian 12 and `flatcam-plus --version` answers `FlatCAM Plus 1.3.1`, and
  `flatpak-builder` produces a 213 MB `.flatpak` in a privileged container. `actionlint` and
  `shellcheck` are clean throughout.
- **L7 — The failures only the runner showed**, each one a fix: the runner's CPython has no Tk
  bindings while `appMain` imports tkinter (`3518a5e`); a uv cache bind-mounted from `$HOME` is
  created by docker as root and is unwritable to the unprivileged container (`3faf275`); ISCC
  defines must not carry their own quotes under PowerShell 7 (`ac0eb26`); Flatpak 1.14 has no
  `--yes` (`60bd055`), needs user namespaces so the build runs privileged (`4c5a93d`), does not
  expand shell variables inside single quotes (`4c5a93d`), refuses a `--user` installation as root
  (`c4e9b80`), and `flatpak-builder` cannot strip a frozen payload without `elfutils`
  (`9f96b7f`); `gh` had no repository because the publish job never checks out (`c95f5d1`).
- **L8 — Two defects of my own that the process caught**: the guard that looks for root-name
  imports walked build outputs and reported twenty failures in any worktree with a bundle
  (`f6d600b`), and chaining `pytest … | tail -1 &&` discarded the test exit status, which let two
  red commits through before it was noticed.
- **L9 — Outcome**: `v1.3.1` published 2026-11-06 with five artifacts totalling 1349 MB:
  `flatcam-plus_1.3.1_amd64.deb` (319 MB), `flatcam-plus-1.3.1-1.x86_64.rpm` (331 MB),
  `FlatCAMPlus-1.3.1-linux-x86_64.flatpak` (213 MB), `FlatCAMPlus-1.3.1-linux-x86_64.tar.gz`
  (313 MB) and `FlatCAMPlus-Setup-1.3.1-x64.exe` (173 MB).
- **L10 — Still open**: publishing the AUR package needs a manual first submission with the
  maintainer account (then `update_aur.sh` plus a push automates bumps); the native review of these
  commits is blocked by a review-facade defect, recorded in Engram as
  `flatcam/review-integration-defects`; the "Check for Updates" preference is a silent no-op in a
  packaged build and stays deferred by L2.

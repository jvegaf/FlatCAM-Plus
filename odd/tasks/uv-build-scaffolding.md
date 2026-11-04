# uv build scaffolding

Objective: add Python/uv project scaffolding (interpreter pin, `pyproject.toml`, package stub and lockfile) without changing the real application entrypoint.
Branch: `dev` | Delivery: one direct commit on `dev` | Test runner: `uv run --with pytest pytest tests -q`

## Specs

- **S1 — Interpreter pin**: `.python-version` pins Python `3.14`.
- **S2 — Project metadata**: `pyproject.toml` declares `name = "flatcam-plus"`, `version = "0.1.0"`, `requires-python = ">=3.14"` and the runtime dependency list.
- **S3 — Console script**: `[project.scripts] flatcam-plus = "flatcam_plus:main"`.
- **S4 — Build backend**: `[build-system]` uses `uv_build` (`uv_build>=0.13.6,<0.14.0`).
- **S5 — Package stub**: `src/flatcam_plus/__init__.py` defines `main()` printing `"Hello from flatcam-plus!"`.
- **S6 — Lockfile**: `uv.lock` (revision 5) is generated and committed.
- **S7 — Known limitation**: the real application entrypoint remains `python flatcam.py`; the `flatcam-plus` console script and `uv build` package only the stub, not the legacy application at the repository root.

### Acceptance criteria

| Spec | Check |
| --- | --- |
| S1-S6 | Files present with the specified values; `uv run --with pytest pytest tests -q` resolves the uv environment → 18 passed (2026-11-04) |
| S7 | `src/flatcam_plus/__init__.py` contains only the stub; `AGENTS.md` documents the limitation |
| S1-S7 | `uv build` is not a valid packaging path for the application; per-OS packaging remains under `packaging/` |

## Tasks

- **T1 — Python/uv scaffolding** (`S1`-`S6`): `.python-version`, `pyproject.toml`, `src/flatcam_plus/__init__.py`, `uv.lock`. Route: inline. Status: done in `0e5f185` (4 files, +1552).
- **T2 — Document the limitation** (`S7`): `AGENTS.md`. Route: inline. Status: done in `95a1bc9`.

## Log

- **L1 — Original request (not preserved)**: Engram session summary #138 records the request as producing eight Conventional Commit messages for a staged change adding Python/uv scaffolding to flatcam-plus. The verbatim user prompt was not captured.
- **L2 — Analysis**: the staged change was purely additive scaffolding: `.python-version` (3.14), `pyproject.toml` (33 runtime dependencies, console script, `uv_build` backend), a two-line `src/flatcam_plus/__init__.py` stub, and `uv.lock` (1498 lines, revision 5).
- **L3 — Classification**: `feat` was a weak fit because the only code is a stub; `build`/`chore` fit the dependency and tooling nature better. Committed as `0e5f185`.
- **L4 — Later discovery**: `uv build` and the `flatcam-plus` script package only the stub; the working application is still launched with `python flatcam.py`. Documented in `AGENTS.md`.
- **L5 — Verification**: no explicit `uv sync`/`uv build` result was recorded in Engram. On 2026-11-04 `uv run --with pytest pytest tests -q` resolved the environment and passed 18 tests.
- **L6 — Reconstruction note**: this document was generated from Engram observation #138 on 2026-11-04 because no ODD log existed when the work was implemented.
- **L7 — Retired (structure cleanup)**: `[project.scripts]`, `[build-system]` and `src/flatcam_plus/` were removed in favour of `[tool.uv] package = false`, so `uv sync` installs dependencies only and `uv build` no longer emits a wheel that packages a hello-world stub. S3, S5 and S7 are superseded; the limitation they documented is gone because the fictional package no longer exists. Verified: `uv lock --check` passes (one lock line, `editable` -> `virtual`), `uv sync` uninstalls the stub, `import flatcam, appMain, camlib, appDatabase, defaults` succeeds, and `uv run --with pytest pytest tests -q` reports 22 passed.

Next step: none. Distribution still targets the legacy root application, not a package; if a wheel is ever wanted, it needs a real ODD feature, not this scaffolding.

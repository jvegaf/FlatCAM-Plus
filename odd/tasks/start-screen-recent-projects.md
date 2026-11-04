# Start screen recent projects

Objective: reopen recent projects from the FlatCAM Plus start screen while keeping the existing Open Project button.
Branch: `dev` | Delivery: direct commits on `dev` | Test runner: `uv run --with pytest pytest tests -q`

## Specs

- **S1 — Recent Projects list**: the start screen shows a "Recent Projects" list under "Create New Project" / "Open Project". A single click opens the selected project. Both original buttons remain available.
- **S2 — Entry format**: each entry displays "name — folder" and exposes the full path as a tooltip.
- **S3 — Filtering and order**: only existing files are listed; records whose `kind` is not `project` are ignored; duplicate paths are removed; order is newest first.
- **S4 — Refresh**: the list refreshes when the user returns to the start workspace.
- **S5 — Robust loader**: a missing recent-projects file, malformed JSON, or a non-list payload returns an empty list instead of raising.
- **S6 — Single loader**: `StartupProjectLauncher` in `flatcam.py` reuses the same loader as the start screen instead of duplicating record parsing.

### Acceptance criteria

| Spec | Check |
| --- | --- |
| S1-S4 | Manual/offscreen launch of the start screen; list appears with the original buttons and opens a project on click |
| S3, S5 | `tests/test_recent_projects.py`: existing-first/deduped, limit, missing file, malformed JSON, non-list payload |
| S6 | `appCommon/recent_projects.load_recent_project_paths` imported by `flatcam.py` |
| All | `uv run --with pytest pytest tests -q` → 18 passed (2026-11-04) |

## Tasks

- **T1 — Loader + tests** (`S3`, `S5`): `appCommon/recent_projects.py`, `tests/test_recent_projects.py`. Route: inline. Status: done in `aaca0cc`.
- **T2 — Start screen UI** (`S1`, `S2`, `S4`): `appGUI/MainGUI.py` (`build_project_start_widget`, `refresh_start_recent_projects`, `on_start_recent_clicked`). Route: inline. Status: done in `aaca0cc`.
- **T3 — Reuse loader** (`S6`): `flatcam.py`. Route: inline. Status: done in `aaca0cc`.

## Log

- **L1 — Original request (as recorded by Engram; truncated preview)**: "podriamos agregarle al StartupProjectLauncher una lista con los ultimos proyectos? para que sea mas rapido que tener que darle al boton de abrir, etc ..... pero mantenemos el boton, porque puede que q..." — Engram did not retain the full text.
- **L2 — Decision**: `StartupProjectLauncher` is never instantiated; the visible startup screen is `MainGUI.build_project_start_widget`. The feature was implemented on the real start screen, keeping the Open button and sharing the loader with the dead launcher code.
- **L3 — Verification**: `uv run --with pytest pytest tests -q` → 18 passed (2026-11-04). Committed as `aaca0cc` on `dev` (4 files, +201/−19).
- **L4 — Reconstruction note**: this document was generated from Engram observation #149 on 2026-11-04 because no ODD log existed when the feature was implemented.

Next step: none.

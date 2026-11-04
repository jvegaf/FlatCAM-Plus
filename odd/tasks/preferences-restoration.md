# Preferences restoration

Objective: restore the preferences that upstream FlatCAM exposed but FlatCAM Plus hid or removed, and give machine profiles their own visible tab with an inline editor.
Branch: `dev` | Delivery: two direct commits on `dev` | Test runner: `uv run --with pytest pytest tests -q`

## Specs

- **S1 — Unhide wired groups**: remove the `.hide()` calls that suppress preference groups still backed by settings and application code: CNC-Job, Gerber, Excellon and Geometry advanced/editor/postprocessor groups, per-document optimization/fuse/colors frames, and general app parameters, app level, startup, save, PDF, font, mouse and activity settings.
- **S2 — Keep justified exceptions hidden**: theme, dark canvas, selection, axis and cursor colors stay hidden because `FIXED_LIGHT_UI_DEFAULTS` enforces the light UI; Send Statistics, Show Shell and the Bookmarks limit stay hidden because they have no backing usage.
- **S3 — Machine tab**: Machine Profiles moves out of the hidden Processing tab into a new visible Machine preferences tab.
- **S4 — Inline editor**: the Machine tab embeds the full profile editor inline instead of opening a modal.
- **S5 — Shared widget**: `appPlugins/cnc_control/machine_profile_editor.py::MachineProfilesEditor` is shared by the preferences tab and by `MachineProfileDialog`; the dialog remains a thin wrapper exposing `.profiles` and `.active_name` for CNC Control.
- **S6 — Persistence**: the group persists every change to the existing `cnc_machine_profiles` and `cnc_active_machine_profile` QSettings keys and reloads the CNC Control tool.
- **S7 — Tab order**: visible tabs are General, GERBER, EXCELLON, GEOMETRY, CNC-JOB, MACHINE.
- **S8 — Removed plugins out of scope**: ToolMarkers, ToolSub, ToolOptimal, ToolQRCode, ToolLevelling, ToolTransform, ToolReport, ToolPcbWizard, ToolEtchCompensation and ToolPdf are not restored by unhiding; their defaults keys no longer exist. Restoring them would require porting the plugins.

### Acceptance criteria

| Spec | Check |
| --- | --- |
| S1, S2 | Preference groups visible/hidden as specified; offscreen app launch |
| S1-S7 | 26/26 visibility harness recorded in the audit session |
| S5, S6 | Machine tab edits persist to QSettings and reload CNC Control; `MachineProfileDialog` still exposes `.profiles`/`.active_name` |
| All | `py_compile` on touched files; `uv run --with pytest pytest tests -q` → 13 passed at audit time (18 passed on 2026-11-04) |

## Tasks

- **T1 — Restore hidden advanced groups** (`S1`, `S2`): `appGUI/preferences/{cncjob,excellon,gerber,geometry,general}/*`. Route: inline. Status: done in `6624b1d` (11 files, +2/−62).
- **T2 — Machine tab and shared editor** (`S3`-`S7`): `appGUI/preferences/machine/*`, `appGUI/preferences/PreferencesUIManager.py`, `appGUI/MainGUI.py`, `appGUI/PanelStyles.py`, `appPlugins/cnc_control/dialogs.py`, `appPlugins/cnc_control/machine_profile_editor.py`. Route: inline. Status: done in `ac24c43` (9 files, +348/−249).

## Log

- **L1 — Original request (as recorded by Engram; truncated preview)**: "tengo una duda, en el proyecto del cual nacio este, flatcam, el area de settings era mucho mas completo que el de flatcam plus, averigua si podemos reimplementar aquellos settings en este. tengo el re..." — Engram did not retain the full text.
- **L2 — Audit finding**: the missing settings have two causes: (a) whole groups still exist and are wired but hidden with `.hide()`; (b) several tool plugins were removed along with their defaults keys. Group files are byte-identical to upstream FlatCAM (dwrobel fork, HEAD `b6e87dbf`, 2024-01-05).
- **L3 — Tier decision (verbatim)**: "si vamos con el 1 de momento". Tier 1 = remove the `hide()` calls; Tier 2 = autolevel and theme/layout; Tier 3 = port ~7.6k lines of removed plugins.
- **L4 — Follow-up request (verbatim)**: "queda muy bien, ahora creo que deberiamos pasar los settings de la maquina tambien a otra tab de los settings en lugar de estar separado".
- **L5 — Correction (verbatim)**: "hay que cambiarlo porque el contenido de la tab debe ser el que sale cuando haces click en manage profiles, no que ahora sale en un modal".
- **L6 — Verification**: `py_compile`, 13 tests passing at audit time, offscreen application launch, and a 26/26 visibility harness. Later full run on 2026-11-04: 18 passed.
- **L7 — Reconstruction note**: this document was generated from Engram observation #147 on 2026-11-04 because no ODD log existed when the work was implemented.

Next step: none for Tier 1. Optional future work: autolevel preferences UI and theme/layout policy review (Tier 2); porting removed plugins (Tier 3, not authorized).

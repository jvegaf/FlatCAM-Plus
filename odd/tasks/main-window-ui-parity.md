# Main window UI parity with artboard 01

Close the three visual gaps left between the chosen artboard
(`design/main-window-restyle/01-dense-cad-dark.html`) and the real window. Ordered by risk, as
the user asked; each is its own work unit.

## Specs

**S1 — Toolbar actions show icon *and* label.** The artboard shows `Open`, `Save`, `Isolation`,
`Drilling`, `Cutout`, `CNC Job` with a glyph to the left of the text. Today
`configure_toolbar` hardcodes `ToolButtonIconOnly` (MainGUI.py:1114, :1120), `show_text_under_action()`
(:4455-4465) exists and works, but startup **overwrites the preference**: `show_text_state = "false"`
plus `q_settings.setValue('menu_show_text', ...)` at :3745-3747, before honoring it at :3769 and :3778.
The label mode must be a persisted choice that startup honours, and the default must leave the labels
visible, because that is what the artboard specifies. It must not widen the toolbar past the window
and break the centered toolbar host.

**S2 — The bottom dock offers Log / CNC console / Tcl shell.** The artboard shows three tabs. Today
`shell_dock` (`FCDock`, MainGUI.py:3008-3016) is hidden by default and holds a single `FCShell`
(`appPlugins/ToolShell.py:297`). A `cnc_console` QTextEdit already exists inside the CNC-control
plugin (`appPlugins/cnc_control/ui.py:1346`) and the application log only goes to a file. The dock must
gain tabs without reparenting plugin widgets, which is where the editors break
(`appTool.py:92-105`, `appGeoEditor.py:379-381`).

**S3 — A mm/in unit toggle in the toolbar.** The artboard shows a segmented `mm | in`. Today
`units_label` is a static `FCLabel("[mm]")` (MainGUI.py:3634) and the `Q` shortcut handler is a
`pass` (:5161). **This is a behaviour change, not a decoration:** `app.app_units` feeds coordinate
display, geometry and G-code. It needs its own decision on whether existing objects are converted or
only the display, what happens to an open project, and what the exported G-code does. It must not
land without that decision recorded here first.

**Non-goals.** No layout restructuring, no new toolbar, no reparenting of editor or plugin containers,
no change to the plotting engine.

## Tasks

| ID | Spec | Route | Unit |
| --- | --- | --- | --- |
| T1 | S1 | inline | Toolbar label mode: persisted, honoured at startup, visible by default |
| T2 | S2 | inline | Bottom dock tabs: Log / CNC console / Tcl shell |
| T3 | S3 | blocked | mm/in toggle — waits on the convert-or-display decision |

## Log

**L1** (user, verbatim): *"ya he pusheado, continua con el cambio de la ui"* — followed by the choice
of all three remaining artboard gaps, *"Los tres, por orden de riesgo"*.

**L2** (context): the three gaps were declared non-goals when the two-theme work closed
(`odd/tasks/two-theme-main-window.md`, L4). The user has now authorised them.

**L3** (evidence): startup forces the icon-only toolbar (`show_text_state = "false"`, MainGUI.py:3745)
using the same overwrite pattern that forced the light theme, which `two-theme-main-window` L3 already
had to remove once. S3 is blocked on a product decision, not on code.

## T1 result

Done: the toolbar label mode is a persisted choice that startup honours
(`show_text_state` now reads `menu_show_text` instead of overwriting it), and `configure_toolbar`
reads `_toolbar_label_style()` instead of hardcoding `ToolButtonIconOnly`. That hardcode was why the
toggle did nothing: the centered host is torn down and rebuilt (`MainGUI.py:1099-1107`), so every
toolbar was re-configured after the preference had been applied once. `_labelled_toolbars()` scopes the
mode to the command toolbars in the host, leaving the coordinate, snap and delta readouts icon-only.

Verified offscreen: at boot the 8 command toolbars report `ToolButtonTextBesideIcon` while
`Coords_TB`, `Snap_TB` and `Delta_Coords_TB` stay `ToolButtonIconOnly`, and the host renders
`Editor`, `Ruler` and `PCB Plotter` with labels.

**Gap, measured not estimated:** of 65 actions in the hosted toolbars, 48 carry text and are now
labelled; **17 are plain `QToolButton`s added as widgets with no action text**, so they still paint
icon+chevron. Full parity with the artboard needs a per-button text audit across the File, Edit, View,
Plugins and Shell toolbars. That is its own unit (T4), not a loose end of this one.

| ID | Spec | Route | Unit |
| --- | --- | --- | --- |
| T4 | S1 | pending | Give the 17 widget-based toolbar buttons label text, or decide menu groups stay icon-only |

**L4** (user decision, standing): native review is **declined for every candidate on `dev`** while the
branch's base stays at `6e4e7e33`. The user chose this over invoking `inspect` again or pausing the
feature. Not re-asked per commit.

Why it is structural, verified rather than assumed: `git merge-base HEAD origin/main` is `6e4e7e33`,
so the provider's candidate spans 1170 files and 13314 insertions, and the lens context budget cannot
hold it. **Correction to earlier advice:** rebasing this work onto `origin/main` is *not* a way out,
because `origin/main` has no `flatcam_plus/` package — this work references paths that only exist on
`dev` after the 100-commit restructure. Review becomes usable again when that base moves, i.e. when the
restructure reaches `main`.


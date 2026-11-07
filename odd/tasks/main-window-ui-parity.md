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


## T2 first slice

Done: the bottom dock hosts a `QTabWidget` instead of one widget. `FCShell` registers itself
through `MainGUI.add_shell_tab()`, which replaces a tab carrying the same label, so reopening the Tcl
tool cannot leave a stale second shell behind. The old focus path
`shell_dock.widget()._edit.setFocus()` (MainGUI.py:4724) assumed the dock's widget *was* the shell and
would have raised once tabs existed; it now goes through `shell_focus_terminal()`, which finds the
shell among the tabs.

Verified offscreen: dock widget is `QTabWidget`, one tab `Tcl Shell`, `shell_terminal()` returns the
`FCShell`, show/hide still toggles, and re-registering keeps the count at one.

**Open decision on the CNC console (S2).** The plugin's console is not a loose widget: it is
`self.console`, added to the plugin's own layout (`appPlugins/cnc_control/ui.py:1353`) and the reason
its terminal panel sets a 450px minimum (`:1355-1357`). Only `append()` and `moveCursor()` use it
(`:1866-1870`). Moving it into the dock therefore leaves a hole in the plugin's layout and invalidates
that minimum height — the user chose "move it" without that evidence, so this waits on a re-decision:
keep the plugin console where it is, mirror its lines into a dock-owned console, or accept the
plugin panel changing shape.


## T2 second slice

Done: the dock's **Log** tab. `AppLogView` (GUIElements.py) is a bounded read-only view
(`setMaximumBlockCount(2000)`) fed by `AppLogHandler`, which attaches to `logging.getLogger('base')`
— the logger `AppLogging` already writes to — at INFO and above. Records cross threads through a queued
signal, because worker threads produce them and a handler must never touch a widget directly.

Verified offscreen: tabs are `['Log', 'Tcl Shell']`, a record sent through `logging` reaches the view,
the view grows, DEBUG is filtered by the handler level, and `shell_terminal()` still finds the FCShell.

Both are now pinned by the existing subprocess boot probe, so a regression in the dock wiring or in the
log attachment fails a test rather than waiting to be noticed.


## T2 closed

The user chose **B′** for the CNC console after seeing the evidence: the dock gets its own view and the
plugin keeps the console its panel is sized around. `CncConsoleView` (GUIElements.py) accepts entries the
plugin has **already formatted** (`append_console` builds the HTML once and appends it to both), so the
two cannot drift and the plugin's colour rules are not duplicated.

Dock tab order at boot is now `['Log', 'CNC console', 'Tcl Shell']`, which is the artboard's order.

Verified offscreen and pinned by the subprocess probe: the dock widget is a `QTabWidget`, all three tabs
exist, a record written through `logging` reaches the Log tab, the mirror accepts an entry, and the Tcl
shell is still reachable through `shell_terminal()`. `CNCControlUI` sets `self.app` (ui.py:34), so the
mirror call is not a silent no-op.


## T4 closed: no action, the premise was wrong

The user asked to give text to "the 17 toolbar buttons without text". That count was **my measurement
error**: it included widget-based toolbar entries that are not buttons at all. Measured properly on the
laid-out window (`widgetForAction` + `isVisible` + class):

- several are **0x0 `QWidget` spacers**, with nothing to label;
- several more are **invisible**, belonging to the disabled editor toolbars;
- the visible remainder is **6-9 `QToolButton`s with `InstantPopup`**, i.e. menu launchers that already
  carry tooltips (`Main menu`, `Plugins`, `Align`, `CNC Control`, `AI Assistant`, `Rotate`, `Skew`,
  `Flip`).

Labelling a menu launcher adds width and no information, so T4 is closed with no code change. This is
the second time in this feature that measuring replaced a plausible assumption (the first was the CNC
console), which is itself the argument for measuring before deciding.

**Toolbar width, measured on the real window at 1440x900 with the project workspace active:** the
centered host is 436px wide, and every command toolbar is clipped (`qt_toolbar_ext_button` visible).
That is **pre-existing**, not introduced here: with icons only the toolbars already need 1384px;
labelling them raises it to 1468px, about 6% more. So the labels neither caused the overflow nor fixed
it, and the commands were already behind the overflow menu before this change.


## T1 default confirmed

With the toolbar already clipped before the change, the user chose to **keep labels on by default**:
the artboard governs, and anyone who wants icons turns them off. No code change; `c077ef9` stands as it
is.

## T3 plan (not started)

Decision on record: the toggle **converts objects and output**, not just the display.

Explicitly forbidden half-state: shipping the toggle so that `app.app_units` and `units_label` change
while the geometry stays put. That silently reinterprets every existing coordinate — a 25.4x error the
user cannot see — and it is worse than having no toggle at all. So T3 lands in two slices and the first
one may not leave the app in that state either:

1. **Slice A — the control exists but is safe.** Toggle, label, `app_units`, `decimals`, and a guard that
   refuses to switch while the project holds objects, with a message saying why. Nothing is
   reinterpreted because nothing switches mid-project yet.
2. **Slice B — conversion.** Converting every object's geometry plus the exported G-code, behind an
   explicit confirmation, with tests for both directions and for a round trip that must return the
   original coordinates within precision.

T3 is the only item left in this feature, and the only one that can corrupt user work. It needs its own
review attention even though native review is stood down on `dev`.


## T3 slice A (done, 34f1850)

The `Q` shortcut, which was a `pass`, now calls `on_toggle_units()`. It flips `app_units`, the `units`
option and the status label **only when the project holds no objects**; otherwise it emits a warning and
changes nothing. `_project_object_count()` counts objects under the kind groups, because
`project_item`'s children are the six always-present groups and counting those would always report a
full project.

The label is now built from `app_units` rather than a hardcoded `[mm]`, so it cannot disagree with the
state it reports.

**Guard verified in red, not assumed:** disabling the refusal makes
`test_units_toggle_is_refused_while_the_project_holds_objects` fail with `assert True is False`.

**Process note, recorded because it nearly cost the work:** the red check was performed by editing the
guard, running the test, and restoring the file with `git checkout -- MainGUI.py` — which reverted to
the last commit and discarded the uncommitted slice A edits. They were re-applied and committed, and
nothing was lost, but the correct order is to commit the unit before sabotaging it. Slice B must not
repeat this.


## T3 slice B: what the object model already gives us

Discovery changed the plan: **each object class already owns `convert_units(units)`** and does its own
bookkeeping, so project conversion reuses it instead of reimplementing a per-type traversal.

| Type | Entry point | What it converts |
| --- | --- | --- |
| Gerber | `GerberObject.py:887` -> `ParseGerber.py:1954` | `solid_geometry`, `follow_geometry`, per-aperture `geometry` plus `width/height/diam/size`, `file_units_factor` |
| Excellon | `ExcellonObject.py:1193` -> `ParseExcellon.py:1168` | each tool's `drills`/`slots`/`solid_geometry`, **plus `tooldia`** (`scale()` alone does not), then `create_geometry()`, Z/feed options and `toolchangexy` |
| Geometry | `GeometryObject.py:1378` -> `camlib.py:2281` | `solid_geometry` (and per-tool geometry when multigeo), then `cutz/depthperpass/travelz/feedrate*/endz/toolchangez` |
| CNCJob | `CNCJobObject.py:1515` -> `camlib.py:2914` | Z/feed/rapid/tooldia, `xy_toolchange`, `xy_end`, and the `tools_mill_*`/`tools_drill_*` options |

Post-mutation sequence, taken from `ToolMove.move_handler` (`ToolMove.py:204-254`): `replotApertures` for
Gerber, then recompute `obj_options['xmin'/'ymin'/'xmax'/'ymax']` from `bounds()`, then `replot_signal`,
then `inform`; `AppObject.on_object_changed` (`:383-407`) also sets `should_we_save`.

### The two hazards

**A silent refusal.** `Gerber.convert_units` returns early when `self.conversion_done` is set, i.e. when
the file declared its own units. One object can therefore refuse while the rest convert, leaving a
project half in millimetres while the application reports inches. `units.convert_objects` now
fingerprints each object's geometry around the call and rolls everything back on the first refusal.

**CNCJob keeps no source.** It stores generated G-code as text (`self.gcode`, and per tool for multitool
jobs), with no reference to the object that produced it — only `obj_options['type']` as a string. Its
`scale` rewrites that text by regex (`camlib.py:7620-7637`) using the configured decimals, so the rewrite
is formatting-bound and lossy. Regeneration is only possible from the producing tool plugin, which is not
reachable from the object's stored state.

**Open product decision:** when the units change, does an existing CNCJob have its G-code text rewritten,
or is it marked stale so the user regenerates it? The conservative answer (never rewrite generated text)
would skip CNCJobs and report them, which is a behaviour change the user must choose. Wiring the UI waits
on that.


## T3 closed

The toggle now converts instead of refusing. Order of operations, chosen so the application can
never report a unit it is not in: confirmation with the object count, then
`units.convert_objects` (all-or-nothing, with rollback), and only on success `app_units`, the option,
the defaults and the label. A refusal leaves the application in its old unit and names the offenders.

Post-mutation bookkeeping follows `ToolMove.move_handler`: aperture markers, `obj_options` bounds
recomputed from `bounds()`, `should_we_save`, then `replot_signal`. CNCJobs convert by rewriting their
generated G-code text, which the user chose over marking them stale.

**Verified on a real file, not only on stubs** (`tests/test_units_real_objects.py`): a parsed
`square_outline.gbr` reports MM, converts to inches with bounds scaled by 1/25.4, and a round trip
returns the original bounds within 1e-6. The declared-units case is covered too: whether the parser
converts anyway or refuses, the test requires the outcome to be visible rather than silent.

**Red checks, both real:** ignoring refusals makes the abort test fail (`assert True is False`), and the
first implementation forced `obj.units` after conversion, marking a refusing object as converted —
caught by the rollback test. The second red check was done with a file backup rather than `git checkout`,
after an earlier checkout discarded uncommitted work.


## Verification

Full suite: **315 passed, exit code 0** (`PYTEST_EXIT=0`, captured from pytest rather than from a pipe).

An earlier run of the same suite reported "exit code 0" while four tests had failed, because the
command ended in `| tail`, whose exit status masked pytest's. The rerun writes to a file and reports the
real code. Worth remembering: a green number is only as good as what produced it.

That failing run was useful: it exposed that `test_object_collection_columns` left fifteen stub rows in
the session-scoped project tree, which then broke the units tests. Fixed at the polluter with an autouse
fixture, and the same failure exposed that `convert_objects` crashed on an object without
`convert_units`; that now counts as a refusal with rollback.


## Delivery

The user performed the review themselves and pushed. `origin/dev` matched `HEAD` at `766af8a` with zero
divergence, and `05f44f8` (the CNC warning) followed locally.

Recorded precisely, because the difference matters: this work was **reviewed by a human, not by the
native provider**. Native review remains stood down on `dev` per `L4` of this document — the candidate
base is still the branch's divergence from `origin/main`, so it cannot fit the lens context budget. A
future reader must not mistake the human review for a provider approval, and `Risk: item 1` stands on its
own merits: converting units rewrites user geometry, and CNC job G-code by regex at the configured
decimals. The confirmation now says so before anything is touched.


## Layout: the toolbar spans the window

The user pointed out the real discrepancy: in the artboard the toolbar runs the full window width and the
sidebars start level with the central view. In the app the host lived inside `right_widget`, i.e. inside the
center column, between the panes.

Change: the central widget is now a container holding `[toolbar_center_host][splitter]`, so the host sits
above everything and the left sidebar, the notebook and the properties sidebar all begin below it.
`create_centered_toolbar_host()` inserts the host into that layout when it builds it, because the host is
created after the splitter and the order must not matter.

**Corrections to earlier claims in this document, both from bad measurement:**

1. "Host is 436px in a 1440 window" was wrong. 436px was measured in the window restored from
   QSettings, which is 800px wide, not 1440.
2. "All five toolbars clipped" came from summing each toolbar's `sizeHint()`, which includes stretch
   slack and overstates what is needed. The 1440 render shows no overflow chevron at all.

Measured truth at 1440x900 after the change: host width **1412px** (was inside the center column), and the
rendered toolbar shows its full set with no `»` button.


## Startup layout opens the panels

The user chose to open with the panels visible, as the artboard shows. Implemented through the
mechanisms the app already has, not by forcing sizes:

- `set_properties_sidebar_visible(True)` is called after the window is built, which is the same path
  the sidebar's own toggle uses. It sets the pane to 360px and makes it visible.
- `global_shell_at_startup` now defaults to `True` (`defaults.py:112`). The dock's startup visibility
  already belonged to that option; forcing the dock open in `MainGUI` would have ignored the preference.

Measured on a 1440x900 window: splitter `[320, 986, 340]`, properties panel visible at 340px, dock
visible at 269px with the `Log | CNC console | Tcl Shell` tabs. The window now matches the artboard's
structure: full-width toolbar, left tree, centre view, right panel and bottom dock all open.

**Process note:** my first attempt forced a `DEFAULT_PROPERTIES_WIDTH` constant into the splitter sizes and
deleted `self.shell_dock.hide()`. Both were wrong for the same reason as earlier in this feature — the
values have owners. Worse, an edit replaced the `def _toolbar_label_style` line instead of inserting
before it, leaving the method headless; the parser accepted it and `test_app_boot` passed, so only reading
the file caught it. Reverted to the existing APIs.


## The mm/in control is now visible

The artboard shows a segmented `mm | in` in the toolbar; only the `Q` shortcut and the status label
existed. `create_units_toggle()` adds two exclusive checkable tool buttons next to the CNC status button,
driven by the same conversion path (`on_units_segment_clicked` calls `on_toggle_units`).

The checked state is refreshed from `app_units` rather than from the click, because a conversion can be
declined or rolled back: the control must never claim a unit the project is not in. Pinned both ways —
clicking a segment converts and the check follows, and a refused conversion leaves the control showing
the real unit.


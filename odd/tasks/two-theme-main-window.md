# Two-theme main window (artboard 01)

Restyle the FlatCAM Plus main window after `design/main-window-restyle/01-dense-cad-dark.html`
and make light and dark themes both real, selectable and persisted. The artboard is a
**visual** spec only; the app keeps its existing widget structure.

## Specs

**S1 — Both themes, both real.** The application must offer light and dark, select it, persist it and
honour it on next start. Verb: *"tendremos modo claro y modo oscuro"*. Today `appMain.py:610-618`
forces `FIXED_LIGHT_UI_DEFAULTS` (`defaults.py:7-12`, `global_theme: 'light'`), and
`PreferencesUIManager` re-applies it in `on_save_button`, `on_restore_defaults_preferences` and
`save_defaults`, writing `theme='light'` to QSettings. `GeneralGUIPrefGroupUI.py:39-46` builds the
appearance radio with only `Light` and hides it. Dark must become selectable without silently
reverting to light, and the choice must survive a restart.

**S2 — Artboard is visual spec, not structure.** Verbatim: *"Use the artboard as the visual spec: map
its parts to the project's existing components and styles, and do not copy the artboard HTML
verbatim."* Keep the real containers: `notebook` left panel (`MainGUI.py:2521`), right
`QStackedWidget` `right_sidebar_stack` (`:3131`), `properties_sidebar` (`:3098`), hidden `FCDock`
console (`:3008-3016`), `workspace_status_container` (`:3601`), centered toolbar host (`:518`).
No widget is reparented and no editor/plugin container is restructured.

**S3 — Tokens come from `design/system.md`.** Verbatim: *"Take colors, typography, spacing, radius and
shadows from design/system.md, the project's token source."* Use only values recorded there: panel-dict
colors (`PS:18-54`), radii 3/4/5/6/7/8/10/12, metrics 24/28/32/10/320/82/90/98, 1px borders, **no
shadows** (the token source defines none). Typography has no size or family token, so text sizes stay
as the widgets already set them; only the weight-600 roles are applied where the artboard shows them.

**S4 — Object kind is readable, not icon-only.** The artboard shows a right-aligned per-object kind
column (`Gerber`, `Excellon`, `Geometry`, `CNC Job`). Today `ObjectCollection` is a single-column
`QAbstractItemModel` (`ObjectCollection.py:538-542`, `columnCount` = `len(item_data)`) with the header
hidden (`:53`) and the kind conveyed by icon only (`:571-577`). The kind must become readable text in a
second column without breaking the model: object rows store `None` as `item_data`
(`ObjectCollection.py:690,696`), so `column_count()` on a `None` **raises**, and
`data(index.column())` (`:553`) would `TypeError`.

**S5 — States stay distinguishable in both themes.** Selected, hover, disabled and keyboard focus must be
tellable apart without relying on color alone, in light and dark. The artboard shows an accent bar on
the selected row and an accent focus treatment. Today: focus is a border tint only, because
`outline: 0px` is global (`PS:317`) and light focus is `#b9d1ff` on `#dfe4ec` — **1.15:1**, effectively
invisible; `hint` `#6f7b8e` colors unselected tab labels at **3.97:1** on white, under the AA 4.5:1
floor for that text size.

**S6 — Density from the artboard.** 24px tree rows, item radius 5px, panel radius 8px, 1px borders,
no shadows — as the artboard and the token source agree.

**Non-goals.** No mm/in segmented control (the app has a static `units_label`, `MainGUI.py:3634`, and
no unit toggle; adding one is a feature, not a restyle). No Log / CNC console / Tcl tabs inside the
shell dock (`ToolShell.py:297` is one widget). No layout restructuring, no new toolbar, no reparenting.

## Tasks

| ID | Spec | Route | Unit |
| --- | --- | --- | --- |
| T1 | S1 | writer → verify | Re-enable dark as a selectable, persisted theme; remove the forced-light gate | `3e2e45f` |
| T2 | S4 | writer → verify | Object tree: readable kind column without breaking the model | `442b13a` |
| T3 | S2,S3,S5,S6 | inline | Theme parity: focus ring, hint contrast, colour-independent selection, density | `943dcac`, corrected in `f15f539` |
| T4 | all | inline | Verification: full suite, both-theme offscreen render, contrast audit | evidence only |

Delivery slice for this feature: `943dcac..f15f539` (six commits, docs included). Everything
committed before `943dcac` on `dev` belongs to other features; this feature's slice must be
split from them if the branch is ever delivered as one PR.

## Log

**L1** (user, verbatim):

> Implement the design artboard design/main-window-restyle/01-dense-cad-dark.html
>
> Artboard: design/main-window-restyle/01-dense-cad-dark.html
> Title: Dense CAD dark
> Tradeoff: Keeps the shipped dark palette and the shipped three-dock layout, tightened: 24px tree rows, per-object kind column, orange focus and active state, always-on console. Maximum information per pixel and no relearning for existing users, but brutal for a newcomer and it inherits the app's weak light-theme focus behaviour in reverse (orange focus is strong, everything else competes with it).
>
> Implement it in the project's real stack. Use the artboard as the visual spec: map its parts to the project's existing components and styles, and do not copy the artboard HTML verbatim.
> Take colors, typography, spacing, radius and shadows from design/system.md, the project's token source.
> Report progress with the gentle_design tool: action "handoff", target "main-window-restyle/01-dense-cad-dark.html", status "in_progress" when you start; status "implemented" when it is done, with previewUrl set to the running app's loopback URL (localhost, 127.0.0.1 or [::1]) when one is running, so the canvas can compare it with the artboard.
> This design is not linked to an ODD feature document: size it under the project's ODD rules as usual.
> This handoff itself commits nothing.

**L2** (user, verbatim): *"tendremos modo claro y modo oscuro"* — both themes are required, so the
artboard's dark treatment is not dark-only work; every change needs light/dark parity, and the
contrast/focus defects in the light theme are in scope as parity, not as extras.

**L3** (evidence, explore `mw5expn9-2-l6ji`): dark is force-disabled, not merely unexposed
(`appMain.py:610-618`, `defaults.py:7-12`, `PreferencesUIManager.on_save_button` rewrites
`theme='light'`, `GeneralGUIPrefGroupUI.py:39-46` hides a Light-only appearance radio). The artboard
layout does not match the app: center notebook holds only `Project` with the tab bar hidden
(`MainGUI.py:3048`), `Selected` is `right_sidebar_stack` (`:3131`), the console dock is hidden
(`:3016`) and holds a single `FCShell` widget. No test in `tests/` asserts stylesheet content,
objectNames, tree columns or widget structure, so styling regressions are caught by nothing but a
manual look — which is why each unit gets a boot check.

**L4** (decision): scope is three work units (T1, T2, T3). The mm/in toggle, the console tabs and any
layout restructuring are declared non-goals rather than deferred half-work, because they are features
the artboard merely depicts.

**L5** (verification, 2026-11-05): full suite `285 passed` (exit 0), plus a 31-test focused re-run after
the final edit. Rendering the app offscreen in both themes (`QWidget.grab()`, `QT_QPA_PLATFORM=offscreen`)
confirmed the Kind column renders per object and the header renders muted and right-aligned. It also
caught a defect no test had: `border-left` on `QTreeView::item:selected` painted once per column, giving
a second stray bar before the Kind cell. `f15f539` removes it, keeps font weight as the non-colour cue,
and flips the test to assert its absence.

**L6** (limits, stated not glossed): the offscreen harness switches `global_theme` after `App` is
constructed, so per-widget toolbar and status sheets keep their startup styling — the dark render shows
a light toolbar for that reason, not because of a product bug. The dark theme end-to-end at startup
(persisted theme read before `MainGUI` is built) was therefore **not** rendered and remains visually
unverified, as does every panel the harness did not open. Also corrected here: two contrast figures
quoted earlier were arithmetically wrong — `hint #6f7b8e` is 4.29:1 on white (not 3.97:1) and
`#0081db` is 4.07:1 (not 4.6:1). The AA defect and its fix hold, but `design/system.md` now carries
the right numbers.

**L7** (user-confirmed, 2026-11-05): supersedes L6's "not rendered" gap for the dark theme. The
earlier "nothing changed" report was the stale packaged bundle: `dist/linux/FlatCAM-Plus/FlatCAM-Plus`
was built 2026-11-05 05:43, before this work, and there is no `flatcam-plus` on PATH, no system
install and no desktop entry. Running from the repo, the user confirmed both observables: the
`Object | Kind` header appears, and after Preferences -> Theme -> Dark -> Apply -> restart the app
renders dark, toolbars included. That last part matters, because the offscreen harness switches
`global_theme` after `App` is constructed and therefore never exercised the startup path that styles
the per-widget toolbar and status sheets.

**L8** (process lesson): this feature was declared verified once before the user's report, and the
claim was too strong. Three consecutive "reproductions" of the reported failure were defects in my
throwaway harness rather than in the product: mutating `app.defaults` directly, then calling
`save_defaults` without the `options` update, then asserting on `QSettings`, which is only refreshed at
startup. Only driving `on_save_button` with the modal restart stubbed produced a trustworthy result.
Lesson: reproduce with the real entry point, not with an imitation of it. `bfdcf48` now pins that path.


**L9** (user decision, verbatim: "2"): native review of this candidate is **declined**. The user is
recorded as having explicitly left this candidate unreviewed; no review authority was ever created for
it, so nothing is abandoned, reset or repaired.

Why the review could not run, stated so a future session does not repeat the attempt:
`gentle_review inspect` returns `review.start` with `base-ref=6e4e7e33` — the point where `dev`
diverges from `origin/main` — and **that base-ref is not overridable**. START was attempted three times:
the offered candidate (102 commits, 15 180 lines), with an explicit lens selection (rejected
`lenses-invalid`, no lineage), and with `baseRef=944cbf5` scoped to this feature (2 713 lines). The two
valid attempts both stopped at `lens_context_budget_exceeded`: provider-owned reviewer evidence exceeds
the lens context budget and immutable candidate evidence is never truncated.

A detached worktree at `3e2e45f` was also tried, on the assumption that `baseRef` narrowed the range.
It does not: the worktree's candidate still resolved to base `6e4e7e33` with the whole-repo path
inventory, so the attempt was abandoned and the worktree removed. `dev` is unchanged.

Consequence for delivery: native review of this work requires the feature on its own branch off
`origin/main`, where the base is near and the candidate is ~700 lines. On `dev` it cannot fit, whatever
the local slicing.


**L10** (follow-up, option 3 of the closing decision): added `tests/test_theme_render.py` plus the
`tests/theme_probe.py` helper, to turn the one manual offscreen render into a guard. Two layers,
because they catch different regressions:

- A fast layer hands the generated stylesheets to real Qt widgets and samples painted pixels. Breaking
  a token, selector or rule leaves the strings plausible while the colour stops reaching the screen;
  `test_theme_tokens` cannot see that, painting can.
- A slow layer boots the application in a real subprocess, twice, and asserts a persisted dark theme
  survives the restart and switches the resource set. That is the exact bug class the user hit, and the
  wiring lives in `appMain` before any widget exists, so the session fixture cannot reach it.

The guard was verified by sabotage, not by assumption: forcing the `modernPanelRoot` background to
magenta makes the render test fail with `light panel root painted #ff00ff, expected surface #ffffff`.
The first sabotage attempt missed — it patched an earlier rule with the same text and the test kept
passing — which is exactly why the RED check was worth doing: it distinguishes "the guard works" from
"the guard has the same text in it".


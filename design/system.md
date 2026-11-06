# FlatCAM Plus — design system

Synced from the shipped Qt styling. Every value below is **literally present in the
sources**; nothing was invented. Values that the sources do not define are listed
under [Gaps](#gaps) instead of being filled in.

Sources read:

| Legend | Path | Role |
| --- | --- | --- |
| `PS` | `flatcam_plus/appGUI/PanelStyles.py` | `modern_panel_colors()` dict (PS:18–54) + all panel/dialog/widget QSS |
| `D` | `flatcam_plus/appGUI/themes/dark_style_sheet.py` | vendor qdarktheme dark sheet, `D_STYLE_SHEET` |
| `L` | `flatcam_plus/appGUI/themes/light_style_sheet.py` | vendor qdarktheme light sheet, `L_STYLE_SHEET` |

Theme selection: `PS:4-15` reads `app.options["global_theme"]`, falling back to
QSettings `("Open Source", "FlatCAM_Plus")` key `theme`; `flatcam_plus/defaults.py:10`
ships `'light'`. `'default'` and `'light'` both resolve to the light palette, every
other value to the dark one (`PS:20`, `PS:38`). The two sheets are assigned at
`flatcam_plus/appMain.py:633` and `:637`.

## Two parallel color systems

This is the single most important fact about the current visual language. There are
two independent palettes in the same window:

1. **Panel dict** (`PS:18–54`) — drives every panel, dialog, tab, tree, input and
   button the app builds itself. The same palette is re-hardcoded in
   `appPlugins/cnc_control/ui.py:76-107`.
2. **Vendor sheet** (`D`/`L`) — drives base widgets, toolbars, menus and scrollbars.

They disagree on the accent color, and both are applied. A restyle has to pick one.

## Color tokens — panel dict

| Token | Light | Dark | Usage | Source |
| --- | --- | --- | --- | --- |
| `app_bg` | `#eef0f3` | `#171717` | main window, splitter background | PS:22 / PS:40 |
| `surface` | `#ffffff` | `#262626` | panels, inputs, menus, selected tab | PS:23 / PS:41 |
| `subtle` | `#f8fafc` | `#171717` | buttons, unselected tabs, headers | PS:24 / PS:42 |
| `text` | `#263244` | `#f0f0f0` | body text | PS:25 / PS:43 |
| `selected_text` | `#111827` | `#ffffff` | text on hover/selection | PS:26 / PS:44 |
| `border` | `#dfe4ec` | `#444444` | all 1px borders | PS:27 / PS:45 |
| `separator` | `#e3e8f0` | `#323232` | gridlines, menu separators, scrollbar handle | PS:28 / PS:46 |
| `hover` | `#eef4ff` | `#323232` | hover background, list row selection | PS:29 / PS:47 |
| `hover_border` | `#d9e6fb` | `#444444` | hover border | PS:30 / PS:48 |
| `active` | `#dfeafe` | `#2b2b2b` | pressed/checked background, input selection, tree row selection | PS:31 / PS:49 |
| `active_border` | `#b9d1ff` | `#ff6900` | press/check border, **input focus border**, progress chunk | PS:32 / PS:50 |
| `disabled` | `#a8b2c1` | `#777777` | disabled text | PS:33 / PS:51 |
| `hint` | `#6f7b8e` | `#999999` | unselected tab label, muted text | PS:34 / PS:52 |
| `console_bg` | `#1e1e1e` | `#171717` | CNC console background | PS:35 / PS:53 |
| `console_text` | `#d4d4d4` | `#f0f0f0` | CNC console text | PS:36 / PS:54 |
| `alert_bg` | `#fff1f2` | `#3a1c28` | button with `prefAlert=true` | PS:125 / PS:130 |
| `alert_hover` | `#ffe4e6` | `#4a2432` | alert hover | PS:126 / PS:131 |
| `alert_border` | `#f43f5e` | `#f87171` | alert border | PS:127 / PS:132 |
| `alert_text` | `#b4233a` | `#fecdd3` | alert text | PS:128 / PS:133 |

Note `active_border` is the **only** accent the panel dict knows, and it is a pale
blue in light (`#b9d1ff`) and saturated orange in dark (`#ff6900`). Dark also has
`app_bg == subtle` (`#171717`), so dark has no visible third surface level.

## Color tokens — vendor sheet

| Token | Light | Dark | Usage | Source |
| --- | --- | --- | --- | --- |
| `widget_bg` | `#f8f9fa` | `rgba(32,33,36,1)` | base QWidget background | L:15 / D:31 |
| `widget_text` | `#4d5157` | `rgba(170,170,170,1)` | base text | L:16 / D:32 |
| `selection_bg` | `#0081db` | `rgba(138,180,247,1)` | selection, progress chunk, focus border | L:17 / D:33 |
| `selection_text` | `#f8f9fa` | `rgba(32,33,36,1)` | selection text | L:18 / D:34 |
| `disabled_text` | `#babdc2` | `rgba(105,113,119,1)` | disabled text | L:21 / D:37 |
| `disabled_selection_bg` | `#dadce0` | `rgba(83,87,91,1)` | disabled selection | L:22 / D:38 |
| `control_border` | `#dadce0` | `rgba(63,64,66,1)` | 1px borders on buttons/inputs/tabs | L:111 / D:138 |
| `tooltip_bg` | `#ffffff` | `rgba(41,42,45,1)` | QToolTip | L:59 / D:74 |
| `tooltip_text` | `#263244` | `rgba(228,231,235,1)` | QToolTip text | L:60 / D:75 |
| `tooltip_border` | `#cfd7e6` | `rgba(63,64,66,1)` | QToolTip border | L:61 / D:77 |
| `primary_button` | bg `#0081db`, text `#f8f9fa` | *absent* | `QPushButton:default` | L:359-360 / L:345 |
| `item_selected_bg` | `#4ca6e5` | *absent* | combo popup / item selection | L:468 |
| `alternate_row` | `#e9ecef` | `rgba(41,43,46,1)` | `alternate-background-color` | L:693 / D:648 |
| `scrollbar_handle` | `rgba(155,155,157,0.737)` | `rgba(84,86,86,0.737)` | scrollbar handle; hover `rgba(117,117,119,0.827)` / `rgba(96,96,98,0.933)` pressed | L:195-203 / D:240-247 |

**Accent conflict, stated plainly:** light has `#0081db` (vendor, 4.07:1 on white) as
its real call-to-action color and `#b9d1ff` (panel) as its focus/checked color — the
latter is a *border* tint too weak to read as an accent. Dark has `#ff6900` (panel,
6.1:1 on `#171717`) and `rgba(138,180,247,1)` (vendor, a light blue). A restyle should
choose one accent per theme and delete the other.

## Typography

**The sources define no typography tokens.** No `font-family` and no `font-size`
appears in `PS`, `D` or `L`; the UI inherits the Qt default font. Only weights are set:

| Role | Family | Size | Weight | Source |
| --- | --- | --- | --- | --- |
| Panel tabs | *undefined* | *undefined* | `600` | PS:190, PS:483, PS:610 |
| Buttons / `QToolButton` | *undefined* | *undefined* | `600` | PS:233 |
| Group box title | *undefined* | *undefined* | `600` | PS:217 |
| Table / list header section | *undefined* | *undefined* | `600` | PS:407 |
| Properties sidebar title | *undefined* | *undefined* | `600` | PS:~805 |
| `QGroupBox` (vendor) | *undefined* | *undefined* | `bold` | D:137 / L:110 |
| `QToolBar` (vendor) | *undefined* | *undefined* | `bold` | D:172 / L:147 |

Artboards therefore use the platform UI stack and a platform mono stack for
coordinates and G-code. Their sizes are **artboard decisions, not project tokens** —
no size scale exists to inherit.

## Spacing and metrics

| Token | Value | Source |
| --- | --- | --- |
| Main window margins | `14, 14, 14, 12` | PS:751 |
| Splitter handle width | `12` | PS:767 |
| Splitter contents margins | `0, 8, 0, 0` | PS:768 |
| Project frame layout | `6,6,6,6`, spacing `0` | PS:837-838 |
| Right tab layout margins / spacing | `8,8,8,8` / `10` | PS:843-844 |
| Preferences tab layout | `8,8,8,8`, spacing `8` | PS:907-908, PS:915 |
| Left sidebar min width | `320` | PS:849 |
| Panel tab bar min width | `82px` | PS:189 |
| Preferences tab bar min width | `90px` | PS:482, PS:576 |
| Workspace tab bar min width (left / plot) | `82` / `98` | PS:858 / PS:869 |
| Button min height (panel) | `24px` | PS:234 |
| Button min height (preferences) | `32` | PS:950 |
| Input min height | `28px` | PS:280 |
| Progress bar min height | `18px` | PS:415 |
| Tree item min height | `24px` | PS:648 |
| Scrollbar width / handle min height | `10px` / `24px` | PS:690, PS:696 |
| Tab padding | `7px 34px 7px 12px` (workspace `8px 34px 8px 12px`) | PS:187, PS:480, PS:607 |
| Button padding | `5px 7px` | PS:232 |
| Input padding | `4px 7px` (combo right `28px`) | PS:279, PS:285 |
| List / tree / table item padding | `4px 5px` (project tree `5px`) | PS:382, PS:647 |
| Group box padding / margin-top | `9px 8px 8px 8px` / `13px` | PS:216, PS:215 |
| Menu padding / item padding | `6px` / `6px 22px 6px 28px` | PS:426, PS:431 |
| Checkbox / radio indicator | `15px` × `15px`, spacing `6px` | PS:350-353 |
| Tab close button | `24px` × `24px`, radius `7px` | PS:104-108 |
| Scrollbar track | `transparent`, width `10px` | PS:672-702 |

## Radius

| Token | Value | Source |
| --- | --- | --- |
| Panel root / frame / tab pane / list / menu | `8px` | PS:151-156, PS:174, PS:208-213, PS:371, PS:425 |
| Workspace tab area (left sidebar, plot) | `12px` | PS:512, PS:536 |
| Workspace tab area (default) | `10px` | PS:558, PS:563 |
| Project frame | `10px` | PS:~784 |
| Buttons / inputs / menu item / progress bar / tooltip | `5px` | PS:161, PS:231, PS:278, PS:411, PS:432 |
| Tab top corners | `6px` | PS:185-186, PS:478-479 |
| Tab top corners (non-expanding workspace) | `8px` | PS:584-585 |
| Workspace tab bar top corners | `12px` | PS:597-598 |
| Checkbox / radio indicator | `4px` / `8px` | PS:350, PS:353 |
| Tab close button | `7px` | PS:108 |
| Progress chunk / bar | `3px` / `5px` | PS:419, PS:411 |
| Scrollbar handle | `5px` | PS:693 |
| Properties close button | `6px` | PS:~807 |
| Group box (vendor) | `4px`, `QTabWidget::pane` `3px` | D:140, D:~456, L:111 |

`L` writes radii as `$radius{Npx}` template placeholders (L:62, L:111, L:332, L:446);
literal values there come from the qdarktheme template engine, not from the file.

## Borders and effects

| Token | Value | Source |
| --- | --- | --- |
| Standard border | `1px solid border` | PS:211, PS:230, PS:277 |
| Divider / menu separator | `1px` of `separator`, margin `5px 8px` | PS:443-444 |
| Header underline | `1px solid separator` | PS:405 |
| **Focus** | border-color change to `active_border` only, **no ring** | PS:293 |
| Outline | `outline: 0px` (rings removed globally) | PS:317, D:28, L:~7 |
| Shadows | **none** — no `box-shadow`, no `QGraphicsDropShadowEffect` in any of the three files | — |
| Selection (list) | bg `hover`, text `selected_text` | PS:374-375 |
| Selection (tree) | bg `active`, text `selected_text` | PS:~660 |

## Component rules

- **Panel buttons** — bg `subtle`, `1px border`, radius `5px`, padding `5px 7px`,
  weight `600`, `min-height: 24px`; hover `hover`/`hover_border`; pressed/checked
  `active`/`active_border`; disabled `surface` bg, `disabled` text, `separator` border
  (PS:227-252). `prefAlert=true` swaps in the alert quartet (PS:254-264).
- **Vendor buttons** — `1px control_border`, padding `4px 8px`, radius `4px`, text in
  the accent color (D:291-295, L:345-348); dark hover/press use `rgba(30,43,60,1)` /
  `rgba(46,70,94,1)` (D:297-301), light uses `rgba(181,202,244,0.333/0.733/0.933)`
  (L:363-373). `QPushButton:default` is solid `#0081db` in light (L:359-360) and
  undefined in dark.
- **Tabs** — unselected bg `subtle`, text `hint`, top corners `6px`, padding
  `7px 34px 7px 12px`, `margin-right: 4px`, `min-width: 82px`, weight `600`; hover
  `hover`/`hover_border` + `selected_text`; selected bg `surface`, text `text`, bottom
  border repainted as `surface` to fake a seamless join (PS:180-205).
- **Workspace tab bars are parameterized** by `min_width` and `expanding`: bar bg
  `subtle` when expanding else `transparent`, border `1px` vs `0px`, tab margin
  `0px` vs `5px 5px 0px 0px`, radius `0px` vs `8px` top corners, bar top radius `12px`
  (PS:576-614). Left sidebar uses `82, expanding=True` (PS:858); the plot tab bar uses
  `98, expanding=False` (PS:869).
- **Tab close button** — `24px` × `24px`, transparent border, radius `7px`; hover
  `hover`/`hover_border`; pressed `active`/`active_border` (PS:100-117).
- **List / table rows** — container radius `8px`, `gridline-color: separator`,
  `alternate-background-color: subtle`, selection `hover` + `selected_text` (PS:369-376).
  **Project tree differs:** border `0`, padding `2px`, item radius `5px`, item padding
  `5px`, `min-height: 24px`, hover `hover`, **selected `active`** (PS:631-660). The two
  selection colors are inconsistent between list and tree.
- **Inputs** — bg `surface`, `1px border`, radius `5px`, padding `4px 7px`,
  `min-height: 28px`, text selection `active`/`selected_text` (PS:274-283). Focus only
  recolors the border to `active_border` (PS:292-294) — with `outline: 0` this is the
  entire focus affordance.
- **Checkbox / radio** — spacing `6px`, transparent 2px top/bottom borders to suppress
  QSS artifacts, indicator `15px`, bg `surface`, border `border`, radius `4px`
  (checkbox) / `8px` (radio) (PS:340-364).
- **Panels** — `modernPanelRoot` gets `surface`, `text`, `border: 0`, radius `8px`
  (PS:151-156); `FCFrame`/`QGroupBox` get `1px border` + radius `8px` (PS:208-213);
  sidebar scroll areas radius `8px`, transparent track, `10px` wide, handle
  `separator` → `hover_border` (PS:672-702); the main workspace splitter is `app_bg`
  with `border: 0` (PS:769-779).

## Gaps

Absent from every source. Not filled in above, and not to be treated as project tokens.

1. **No font family, no font sizes, no line-heights, no letter-spacing.** Only weights.
2. **No spacing scale.** 4, 5, 6, 7, 8, 9, 10, 12, 13 and 14 px all appear ad hoc
   (PS:162, 216, 232, 279, 382, 426, 607, 751, 844).
3. **No shadow or elevation tokens**, hence no depth hierarchy beyond 1px borders.
4. **No focus-ring token.** `outline: 0px` removes rings; focus is a border tint that,
   in light theme, is `#b9d1ff` on `#dfe4ec` — a 1.15:1 change, effectively invisible.
5. **No semantic accent name**, and two accents per theme coexist (see above).
6. **No success / info / warning colors.** The only semantics are the `prefAlert`
   quartet; error and success states have no color.
7. **No icon-size scale.** Widths `10/14/18/20/23/24/26/28px` are scattered
   (PS:145, PS:308, D:386, L:~360s).
8. **No disabled tokens for vendor dark buttons** beyond a border color (D:306).
9. **`hint` fails AA for body text on `surface`.** `#6f7b8e` on `#ffffff` measures
   **4.29:1** and on the actual unselected-tab background `subtle #f8fafc` **4.10:1** —
   just under the 4.5:1 floor, for small text (unselected tab labels). Artboards and the
   implementation use a proposed `hint-strong` `#5f6b7e` (**5.40:1** on white, 5.16:1 on
   `#f8fafc`) for small muted text and reserve `hint` for large/decorative use; see below.
   (These ratios were recomputed and corrected on 2026-11-05; an earlier draft said
   3.97:1.)

## Proposed additions (NOT current tokens)

These are **proposals for review**, clearly separated from the synced system. Each one
fills a gap above; none of them is in the codebase today.

| Proposed token | Value | Why | Measured contrast |
| --- | --- | --- | --- |
| `hint-strong` | `#5f6b7e` (light) / `#a8a8a8` (dark) | small muted text that must pass AA | 5.40:1 on `#ffffff`; 6.36:1 for `#a8a8a8` on `#262626` |
| `focus_ring` | 2px offset ring in the theme accent | focus must not rely on a border tint that is 1.15:1 in light | — |
| `accent` (unified) | `#0081db` light / `#ff6900` dark | collapse the two-accent conflict to one per theme | 4.07:1 on white (border/component use, above the 3:1 floor); 6.21:1 on `#171717` |
| type scale | 11 / 12 / 13 / 16 / 20 px | coordinates and G-code need an explicit compact step | — |
| space scale | 4 / 8 / 12 / 16 / 24 | replace the 4-14px ad hoc set | — |
| `danger` / `success` | `#f43f5e` / `#2f9e6b` | states currently have no color | 4.9:1 / 3.4:1 on white → label alongside color |

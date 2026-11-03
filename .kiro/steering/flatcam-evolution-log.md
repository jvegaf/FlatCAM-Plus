---
inclusion: self
---

# FlatCAM Plus — Evolutionary Cognition Log

This file is a living record of discoveries made while using FlatCAM Plus.
Each entry documents a difference, unexpected behavior, workaround or
insight that was not mapped in previous steerings.

---

## How to Use This Log

**For the agent:**

- When the user discovers something new (difference, bug, workaround, hidden feature),
  add an entry here following the template below.
- Periodically, mature entries must be consolidated into main steerings
  (`flatcam-feature-map.md` or `flatcam-plus-optimizations.md`).
- Mark consolidated entries with `[CONSOLIDATED]` in the status.

**For the user:**

- Say "learn this" or "record this difference" when you want me to add it to the log.
- Say "what have we learned?" so I can list the active entries.
- Say "consolidate log" so I can move mature entries to the main steerings.

---

## Entry Template

```
### EVO-XXX: [Short title]

- **Date:** YYYY-MM-DD
- **Status:** ACTIVE | CONSOLIDATED | OBSOLETE
- **Context:** How it was discovered (user question, trial, error, etc.)
- **Version 8.994:** [As it was / as it was in the old one — or "N/A" if it didn't exist]
- **FlatCAM Plus:** [How it is / how it works in Plus]
- **Key Difference:** [The practical difference in a sentence]
- **Optimization?** YES/NO — [If YES, which OPT-XX relates or suggest new]
- **Impact:** HIGH / MEDIUM / LOW
- **Tags:** #ui #workflow #cnc #isolation #probe #gcode #preferences #bug #workaround
```

---

## Entries

### EVO-001: Mouse Settings section hidden in Preferences

- **Date:** 2026-07-04
- **Status:** ACTIVE
- **Context:** User wanted to change the pan button (RMB → MMB). The option exists in the code but is hidden with `.hide()` in the simplified UI.
- **Version 8.994:** Preferences → General → App Settings → Pan Button (MMB/RMB) — visible and accessible.
- **FlatCAM Plus:** The "Mouse Settings" section (Pan Button, Cursor Shape, Multi-Selection) was hidden in commit `6c7afe2` as part of UI simplification. The code works, it just doesn't appear.
- **Key Difference:** Mouse preferences exist but are hidden. Change via `current_defaults_1.1.0.FlatConfig` file in `%APPDATA%\FlatCAM\`.
- **Optimization?** NO — it is an accessibility regression in the UI.
- **Impact:** MEDIUM
- **Tags:** #preferences #ui #workaround
- **Workaround:** Edit `global_pan_button` from `"2"` to `"3"` directly in the `C:\Users\<user>\AppData\Roaming\FlatCAM\current_defaults_1.1.0.FlatConfig` file. Or uncomment `.hide()` in `GeneralAPPSetGroupUI.py` lines of `m_frame` and `mouse_lbl`.

---

### EVO-002: Standalone build fails with OR-Tools (_pywrapcp)

- **Date:** 2026-07-04
- **Status:** ACTIVE
- **Context:** After recompiling with `build_standalone.ps1`, the exe fails with "DLL load failed while importing _pywrapcp".
- **Version 8.994:** Does not use OR-Tools. Simpler build.
- **FlatCAM Plus:** `camlib.py` imports `ortools.constraint_solver.pywrapcp`. PyInstaller does not package native OR-Tools DLLs correctly.
- **Key difference:** The old exe (`dist\windows\x64\`) works; rebuild (`dist\standalone\`) does not. They are different directories.
- **Optimization?** NO — build/packaging issue.
- **Impact:** HIGH (prevents use of the recompiled exe)
- **Tags:** #build #bug #workaround
- **Workaround:** Use the pre-compiled exe in `dist\windows\x64\FlatCAMPlus\FlatCAMPlus.exe`. To run from sources, use the build venv (`c:\temp\fcvenv\Scripts\python.exe flatcam.py`) — the project's local venv does not have PyQt6 installed.

---

### EVO-003: Local Venv has no dependencies installed

- **Date:** 2026-07-04
- **Status:** ACTIVE
- **Context:** Attempt to run `venv\Scripts\python.exe flatcam.py` fails with "No module named 'PyQt6'".
- **Version 8,994:** N/A
- **FlatCAM Plus:** `build_standalone.ps1` creates a separate venv in `c:\temp\fcvenv` with all deps. The `venv\` repository location is empty/incomplete.
- **Key difference:** To run from sources, use `c:\temp\fcvenv\Scripts\python.exe flatcam.py` (if the build was run at least once) or install deps in the local venv with `pip install -r requirements.txt`.
- **Optimization?** NO
- **Impact:** LOW
- **Tags:** #build #workaround

---

### EVO-004: Preferences saved in versioned file

- **Date:** 2026-07-04
- **Status:** ACTIVE
- **Context:** When looking for where preferences are saved for manual editing.
- **Version 8.994:** `%APPDATA%\FlatCAM\current_defaults.FlatConfig` (JSON)
- **FlatCAM Plus:** `%APPDATA%\FlatCAM\current_defaults_1.1.0.FlatConfig` (versioned JSON)
- **Key difference:** The file name includes the version. Factory defaults too: `factory_defaults_1.1.0.FlatConfig`.
- **Optimization?** NO — just nomenclature change.
- **Impact:** LOW
- **Tags:** #preferences #filesystem

---

### EVO-005: Generate With Copper — automatic pour detection

- **Date:** 2026-07-04
- **Status:** ACTIVE
- **Context:** User asked if "Generate With Copper" creates copper pours out of thin air.
- **Version 8.994:** Did not exist. Isolation always generated paths around everything.
- **FlatCAM Plus:** `_is_copper_pour_geometry()` detects pours by geometric criteria: polygon ≥55% of the plate width/height, or with interiors (clearance holes) and ≥8% of the total area. Isolates only internal clearances and filters frames.
- **Key difference:** Does not create pours — recognizes existing pours in Gerber and avoids milling their outer edges unnecessarily.
- **Optimization?** YES — OPT-05
- **Impact:** MEDIUM
- **Tags:** #isolation #workflow #copper

---

### EVO-007: Persistent CNC connection in separate JSON file

- **Date:** 2026-07-04
- **Status:** ACTIVE
- **Context:** User asked if the CNC IP configuration is persistent.
- **Version 8.994:** N/A — did not have CNC connection.
- **FlatCAM Plus:** Connection settings are saved in `%APPDATA%\FlatCAM\cnc_connection_settings.json`. Includes mode (serial/tcp/web), profile, host, port, baudrate, auto_connect. Persists between sessions.
- **Key difference:** Separate file from the main preferences. It is not inside `current_defaults_1.1.0.FlatConfig`.
- **Optimization?** NO — just location information.
- **Impact:** LOW
- **Tags:** #cnc #preferences #filesystem

---

### EVO-016: Definitive fix for OR-Tools — test DefaultRoutingSearchParameters() in import

- **Date:** 2026-07-06
- **Status:** ACTIVE
- **Context:** The except at the top of camlib.py only caught ModuleNotFoundError when importing pywrapcp/routing_enums_pb2. But these imports pass — what fails is DefaultRoutingSearchParameters() internally due to lack of routing_parameters_pb2. The except Exception in the caller should catch it but for some reason the exe doesn't catch it.
- **Version 8.994:** Did not use OR-Tools.
- **FlatCAM Plus:** Fix applied to camlib.py: added `pywrapcp.DefaultRoutingSearchParameters()` in the import's try block. If it fails (any Exception), HAS_ORTOOLS=False and the code automatically uses RTree for any opt_type B or M.
- **Key difference:** With the fix in the source, running via `c:\temp\fcvenv\Scripts\python.exe flatcam.py` works without OR-Tools. The precompiled exe is not affected (internally packaged sources).
- **Optimization?** NO — bug fix.
- **Impact:** HIGH (unlocks drilling to run from sources)
- **Tags:** #drilling #bug #ortools #fix #camlib
- **Modified file:** `c:\dsn\CNC\FlatCAM-Plus\camlib.py` (HAS_ORTOOLS block at top)

---

### EVO-017: Cutout with non-rectangular contour — correct workflow (REVISED)

- **Date:** 2026-07-09 (revised)
- **Status:** ACTIVE
- **Context:** User tried to cut a plate along its real contour (not rectangular) using the Cutout Tool. Investigation of the source code (`ToolCutOut.py`) revealed conditional behavior.
- **Version 8.994:** Cutout Tool with Gerber profile worked directly for non-rectangular contours (explicit Outside option).
- **FlatCAM Plus:** The Cutout Tool **works** for non-rectangular contours BUT with condition: the Gerber needs to be a **single Polygon** (not MultiPolygon). If `isinstance(object_geo, MultiPolygon)` → the code does `box()` (rectangular bounding box). If it is simple Polygon → do `buffer(margin + cut_dia/2)` on the real contour, preserving the shape.
- **Key Difference:** Plus's Cutout Tool works for non-rectangular shapes if the contour Gerber is a single closed polygon. A well-made Edge_Cuts.gbr file (single contour) works correctly. MultiPolygon (multiple contours) becomes a bounding box.
- **Correct workflow:** Tools → Cutout, Source = Gerber profile (Edge_Cuts), Kind = Single, Margin = 0, Multi-Depth = enabled, Depth per pass = 0.5-0.6mm. With margin=0, the buffer applies `cut_dia/2` outward → the piece is the exact Gerber size.
- **CORRECTION about Isolation:** The previous suggestion of using Isolation Routing as a workaround is **incorrect for cutout** because Isolation does NOT have native multi-depth. The Cutout Tool has (`tools_cutout_mdepth` + `tools_cutout_depthperpass`). Using Isolation for cutout would require a single pass = risk of breaking the cutter.
- **Optimization?** NO — but it is important to know that Cutout > Isolation for profile cut.
- **Impact:** HIGH (fundamental workflow for non-rectangular PCBs)
- **Tags:** #cutout #workflow #workaround #multidepth
- **Source code confirmed:** `ToolCutOut.py` lines 750-753 (MultiPolygon → box) and 755-757 (Polygon → correct buffer). Geo_init on lines 893-894 confirms `tools_mill_multidepth` and `tools_mill_depthperpass` passed to Milling.

---

### EVO-016: Maximized window cuts content from sides (DPI/geometry bug)

- **Date:** 2026-07-06
- **Status:** ACTIVE
- **Context:** When running from sources via venv, the maximized window exceeds the limits of the screen, cutting off content on the sides. Minimizing and maximizing again fixes it.
- **Version 8.994:** Didn't have this problem (PyQt5, different DPI handling).
- **FlatCAM Plus:** PyQt6 with QSettings saving window geometry that may not respect DPI scaling. The state saved in the `HKCU\Software\Open Source\FlatCAM_Plus` registry may contain invalid dimensions.
- **Key Difference:** PyQt6 handles DPI differently than PyQt5. Saved geometry may become inconsistent.
- **Optimization?** NO — UI/DPI bug.
- **Impact:** LOW (simple workaround: minimize/maximize)
- **Tags:** #ui #bug #workaround #dpi
- **Workaround:** Clear saved geometry: `Remove-ItemProperty -Path 'HKCU:\Software\Open Source\FlatCAM_Plus' -Name 'geometry'` and `windowState`. Or force DPI override in the shortcut: Compatibility → "Override high DPI scaling behavior" → "Application".

---

### EVO-015: EXCELLON Preferences does not expose Optimization Type in the UI

- **Date:** 2026-07-06
- **Status:** ACTIVE
- **Context:** When searching for Optimization Type in Preferences → EXCELLON to resolve EVO-014 through the UI.
- **Version 8.994:** Preferences → Excellon → Optimization Type was visible (options: MetaHeuristic, Basic, TSA, R-Tree).
- **FlatCAM Plus:** The option has been removed/hidden from the simplified UI. Preferences → EXCELLON only shows: Plot Options, Excellon Format, Mill Holes, Export Options. There is no way to change the type of drill path optimization through the interface.
- **Key difference:** Combined with EVO-014, it makes it impossible to resolve the OR-Tools crash without: (1) editing FlatConfig with app closed + creating new project, or (2) editing factory_defaults, or (3) editing source.
- **Optimization?** NO — accessibility regression.
- **Impact:** HIGH (blocks drilling for existing projects)
- **Tags:** #preferences #excellon #drilling #ui #bug

---

### EVO-014: OR-Tools broken in exe — drill optimization fails with 'B'

- **Date:** 2026-07-06
- **Status:** ACTIVE
- **Context:** When generating CNC Drilling Job, error "No module named 'ortools.constraint_solver.routing_parameters_pb2'". The precompiled exe has incomplete OR-Tools.
- **Version 8.994:** Used TSA (nearest-neighbor) by default. No dependence on OR-Tools.
- **FlatCAM Plus:** Default `excellon_optimization_type: "B"` (OR-Tools Basic). Packaged exe failed. Alternatives that work: `"T"` (TSA nearest-neighbor) or `"N"` (no optimization).
- **Key difference:** Changing `excellon_optimization_type` from `"B"` to `"T"` in FlatConfig solves it. Minimum practical difference for PCBs with <100 holes.
- **Optimization?** NO — workaround for packaging bug.
- **Impact:** HIGH (prevents generation of drilling CNC Job without the fix)
- **Tags:** #drilling #bug #workaround #ortools
- **Workaround:** Edit `C:\Users\<user>\AppData\Roaming\FlatCAM\current_defaults_1.1.0.FlatConfig` and change `"excellon_optimization_type": "B"` to `"excellon_optimization_type": "R"` (RTree, does not touch OR-Tools). **IMPORTANT:** Close FlatCAM BEFORE editing the file — the app overwrites FlatConfig when exiting with the values ​​in memory. Sequence: close app → edit file → open app. **ATTENTION:** .FlatPrj and tool data projects load the opt_type value saved by tool at the time of creation, ignoring FlatConfig. If the project was created with "B", the fix in FlatConfig does not help for existing objects. **Permanent solution:** Create new project after changing FlatConfig — new objects inherit the correct default. Old projects continue with "B" in the internal tool data.
- **Technical analysis (CONFIRMED):** The distributed exe (`dist\windows\x64\`) has the `_internal\ortools\constraint_solver\` directory with ONLY `_pywrapcp.pyd` (native binary). ALL Python wrappers are missing: `__init__.py`, `pywrapcp.py`, `routing_enums_pb2.py`, `routing_parameters_pb2.py`, etc. The PyInstaller that generated the original exe did not include the `.py` from the ortools package — the author's packaging bug. The import of `pywrapcp` at the top of camlib.py does not fail because PyInstaller redirects to `.pyd`, but when inside `.pyd` it tries to `import routing_parameters_pb2` as a sister Python module, it fails because `.py` does not exist in the folder.
- **Definite solution (CONFIRMED):** The distributed exe (`dist\windows\x64\`) has incomplete packaging — the OR-Tools and google.protobuf Python modules are missing. Two solutions:
  1. **Run from sources (immediate):** `c:\temp\fcvenv\Scripts\python.exe c:\dsn\CNC\FlatCAM-Plus\flatcam.py` — works perfectly, complete OR-Tools.
  2. **Correct exe rebuild:** Add `"--collect-all", "ortools"` and `"--collect-all", "google.protobuf"` to `build_standalone.ps1` before running PyInstaller. The original build did not collect these packages. After the fix, running `powershell -ExecutionPolicy Bypass -File build_standalone.ps1` generates a working exe in `dist\standalone\`.

---

### EVO-013: Tool selection in Excellon moved to Drilling plugin

- **Date:** 2026-07-04
- **Status:** ACTIVE
- **Context:** User wanted to disable tools in Excellon. On the Properties screen there are no checkboxes in the Tools Table.
- **Version 8.994:** Excellon Properties (Selected tab) had a clickable "P" (plot/process) column to select/unselect which tools to process in the CNC Job.
- **FlatCAM Plus:** The Tools Table in Excellon Properties is for information only (shows diameter, drills, slots). The selection of which tools to include in the CNC Job is done within the **Drilling** plugin ("Plugins" section below the table → "Drilling" button).
- **Key difference:** In 8,994, I selected tools directly from the object table. In Plus, you need to open the Drilling plugin to choose.
- **Optimization?** NO — UI change that may confuse those coming from 8.994.
- **Impact:** MEDIUM
- **Tags:** #ui #excellon #drilling #workflow

---

### EVO-012: Auto Level section only appears after connecting to the controller

- **Date:** 2026-07-04
- **Status:** ACTIVE
- **Context:** User could not find where to turn on the auto-level. The section is inside CNC Control and is probably only visible after connecting.
- **Version 8,994:** N/A
- **FlatCAM Plus:** The Auto Level section is in the CNC Control panel, stacked between "Job Setup / Zero" and "G-Code Preview / Terminal". Contains: Fit Area, Rows/Columns, Safe Z, Probe Depth/Feed, Slow Probe Feed, Auto Zero Z, Probe/Stop/Clear/3D buttons. The "Enable" (Use Map) checkbox activates Z compensation in streaming. The section may not be visible without an active connection.
- **Key difference:** Auto Level is not a separate tool/plugin — it is a section of the CNC Control dashboard that requires an active connection to appear and function.
- **Optimization?** NO — location information in the UI.
- **Impact:** HIGH (important functionality that is not obvious to find)
- **Tags:** #cnc #autolevel #ui #probe

---

### EVO-011: Telnet is preferred over HTTP for streaming; does not conflict with pendant

- **Date:** 2026-07-04
- **Status:** ACTIVE
- **Context:** User asked whether to use Telnet or HTTP to work with FlatCAM Plus.
- **Version 8,994:** N/A
- **FlatCAM Plus:** Telnet (port 23) is better for streaming/jog/probe: lower latency, persistent connection, does not conflict with pendant (which uses WebSocket on port 80). HTTP is only required for Flash File System. Telnet supports multiple simultaneous connections to FluidNC.
- **Key difference:** Telnet for daily operation (streaming, probe, jog). HTTP only when you need to manage files on flash. Do not use both at the same time to send commands.
- **Optimization?** YES — complements OPT-06: the Telnet + FlatCAM Plus combination is the ideal setup for PCBs with auto-level.
- **Impact:** MEDIUM
- **Tags:** #cnc #connection #fluidnc #streaming #pendant

---

### EVO-010: Streaming vs Upload — Z compensation only works in streaming

- **Date:** 2026-07-04
- **Status:** ACTIVE
- **Context:** User asked if G-Code sent is recorded on the SD card.
- **Version 8,994:** N/A
- **FlatCAM Plus:** Three sending modes: (1) Streaming via Start Queue — line by line, without recording, allows Z compensation with Use Map. (2) Upload via Flash File System (HTTP) — writes to the ESP32 flash, runs as an SD job, without compensation. (3) Physical SD card — no compensation.
- **Key difference:** Auto-level bicubic Z compensation ONLY works in streaming mode. If you save the file to SD/flash and run it as a job, the G-Code will be uncompensated.
- **Optimization?** YES — reinforces OPT-01: integrated streaming is mandatory for auto-level to work.
- **Impact:** HIGH
- **Tags:** #cnc #autolevel #streaming #gcode

---

### EVO-009: Flash File System requires HTTP connection, not Telnet

- **Date:** 2026-07-04
- **Status:** ACTIVE
- **Context:** User asked what the "Flash File System" button is in CNC Control.
- **Version 8,994:** N/A
- **FlatCAM Plus:** The "Flash File System" button opens an ESP32 flash file manager (SPIFFS/LittleFS). Allows you to list, upload, download, delete, create folders — equivalent to the Files tab of the FluidNC WebUI. However, it only works in HTTP/Web mode, not via Telnet.
- **Key difference:** If connecting via Telnet (port 23), Flash File System does not work. Need HTTP (port 80) to access the file REST API.
- **Optimization?** NO — usage information.
- **Impact:** LOW
- **Tags:** #cnc #filesystem #fluidnc

---

### EVO-008: Height map does not persist between sessions

- **Date:** 2026-07-04
- **Status:** ACTIVE
- **Context:** User asked if auto-level is automatic when submitting job. Explanation revealed that the map lives only in memory.
- **Version 8,994:** N/A
- **FlatCAM Plus:** The probed height map remains in memory during the session. There is no export/import of map file. If you close the app, you lose and have to try it again.
- **Key difference:** Probe needs to be redone after each FlatCAM Plus session. "Use Map" activates streaming compensation but does not trigger probes automatically.
- **Optimization?** NO — current limitation. bCNC allows saving/loading height maps to file.
- **Impact:** MEDIUM
- **Tags:** #cnc #probe #autolevel #limitation

---

### EVO-006: Precompiled exe and rebuild exe are in different directories

- **Date:** 2026-07-04
- **Status:** ACTIVE
- **Context:** User recompiled and the exe did not work, but was opening the wrong exe.
- **Version 8,994:** N/A
- **FlatCAM Plus:** `build_standalone.ps1` generates in `dist\standalone\FlatCAMPlus\FlatCAMPlus.exe`. The precompiled exe that works is in `dist\windows\x64\FlatCAMPlus\FlatCAMPlus.exe`. They are different builds.
- **Key Difference:** Always check which dist directory is being used. The functional one is `dist\windows\x64\`.
- **Optimization?** NO
- **Impact:** MEDIUM
- **Tags:** #build #filesystem #workaround

---

### EVO-017: Queue UP/DOWN buttons may be invisible due to lack of horizontal space

- **Date:** 2026-07-07
- **Status:** ACTIVE
- **Context:** User reported that he does not see UP/DOWN buttons in the Job Queue / Sender section of CNC Control. Confirmed in the code that the buttons exist (`queue_up_btn`, `queue_down_btn`) and are not hidden with `.hide()`.
- **Version 8.994:** N/A — did not have Queue or CNC Control.
- **FlatCAM Plus:** The Queue horizontal bar has 9 widgets in a single `QHBoxLayout`: combo, Refresh, ADD, REMOVE, UP, DOWN, START QUEUE, PAUSE, STOP. In smaller windows/resolutions, the UP and DOWN buttons (which are in the middle) may be cut off or compressed to the point where they are not visible.
- **Key difference:** The buttons exist in the code (`appPlugins/cnc_control/ui.py` lines 1131-1132, 1150-1151) but the UI does not guarantee scroll or wrap — it depends on the width of the window.
- **Optimization?** NO — it's a UI layout/responsiveness issue.
- **Impact:** MEDIUM (useful functionality that appears to not exist)
- **Tags:** #ui #cnc #queue #layout #bug
- **Workaround:** Maximize the window or enlarge the panel. Alternative: add the jobs in the correct starting order (the queue runs from top to bottom), or use REMOVE + ADD to reposition.

---

### EVO-018: Cutout with Gerber MultiPolygon (contour + internal cutout) generates bounding box

- **Date:** 2026-07-09
- **Status:** ACTIVE
- **Context:** User exported Gerber from Fusion 360 profile containing external contour + internal cutout (slot/oblong). The file has two paths (two D02 commands). FlatCAM Plus interpreted it as MultiPolygon and the Cutout Tool generated rectangular bounding box instead of the actual contour.
- **Version 8.994:** Cutout Tool treated MultiPolygon differently (unconfirmed if it worked better).
- **FlatCAM Plus:** In `ToolCutOut.py`, when `kind == 'single'` and `isinstance(object_geo, MultiPolygon)` → executes `box(x0, y0, x1, y1)` (lines 750-752). This discards the actual geometry and uses bounding box. Condition: Gerber with multiple contours (D02 separating paths) is parsed as MultiPolygon by the Shapely lib.
- **Key Difference:** Gerbers with outer outline + inner cutouts in the same file do not work with Cutout Kind=Single. The fallback for bounding box is silent (no warning).
- **Workarounds confirmed in the code:**
  1. **Kind != Single:** With kind other than 'single', the code iterates each geometry individually with `flatten_shapely_geometry()` and buffers correctly on each separate contour.
  2. **Separate contours in CAD:** Export only the external contour in Gerber profile. Internal cutouts as separate operation.
  3. **Import as Geometry:** Geometry with LinearRing/LineString receives correct buffer without MultiPolygon check.
- **Root cause in Gerber:** Each `D02` command (move without draw) starts a new path. Two D02 = two closed polygons = MultiPolygon in Shapely. Gerbers from Fusion 360 (and EAGLE) with internal slots/cuts export everything in the same profile file.
- **Optimization?** NO — Cutout Tool limitation with composite geometries.
- **Impact:** HIGH (any non-rectangular board with holes/slots in the outline is affected)
- **Tags:** #cutout #gerber #multipolygon #fusion360 #bug #workaround

---

### EVO-019: Cutout Tool does not distinguish external contour from internal cutout (offset always outside)

- **Date:** 2026-07-09
- **Status:** ACTIVE
- **Context:** When using Kind != Single to process Gerber with outer contour + inner slot (EVO-018 workaround), the Cutout Tool applied an outward offset to BOTH contours. Result: correct external path (mill outside the board), but wrong internal slot path (mill outside the triangle = removing material from the board instead of opening the hole).
- **Version 8.994:** Cutout Tool had an explicit "Inside/Outside" option that allowed controlling the offset direction manually. Processed each contour with the correct direction.
- **FlatCAM Plus:** With Kind != Single, the code iterates with `flatten_shapely_geometry()` and applies `buffer(margin)` + `.exterior` uniformly across all geometries (line ~800). There is no logic to detect whether a contour is "inside" (hole) vs "outside" (plate edge) and reverse the offset automatically.
- **Key Difference:** The Cutout Tool treats all contours as if they were outer edges. For internal cutouts (slots, non-circular holes), the offset should be towards the inside of the hole (= "outside" of the slot polygon when seen as an independent shape, but "inside" in relation to the board).
- **Logic in the code (`margin < 0`):** If margin is negative, the code uses `.interiors` instead of `.exterior`:

  ```python
  if margin >= 0:
      geo_buf = object_geo.buffer(margin + abs(cut_dia / 2))
      geo = geo_buf.exterior
  else:
      geo_buf = object_geo.buffer(-margin + abs(cut_dia / 2))
      geo = unary_union(geo_buf.interiors)
  ```

  But this generates paths inside the buffered polygon, it does not solve the case of separate slots.
- **Functional workaround:** Separate the contours into two independent Gerbers in CAD:
  1. **External outline Gerber** → Cutout margin=0 → offset out ✅
  2. **Internal slot Gerber** (as isolated closed polygon) → Cutout margin=0 → offset out of THAT polygon = into the hole in the board ✅
  Both with multi-depth. Result: plate and hole in exact dimensions.
- **Optimization?** NO — functional limitation that requires manual separation of contours.
- **Impact:** HIGH (any plate with non-circular internal cutouts is affected)
- **Tags:** #cutout #offset #internal #slot #fusion360 #workaround

---

### EVO-020: Standalone build requires --collect-all certification and tracking

- **Date:** 2026-07-10
- **Status:** ACTIVE
- **Context:** When generating the installer with `build_standalone.ps1`, the exe crashed at startup with `AttributeError: module 'certifi' has no attribute 'where'`. The string: `ToolImage.py` → `import rasterio` → `rasterio._env` → `certifi.where()` → fails.
- **Version 8.994:** Did not use rasterio nor did it have a PyInstaller installer.
- **FlatCAM Plus:** The original `build_standalone.ps1` did not include `--collect-all certifi` nor `--collect-all rasterio`. `certifi` was installed in venv but PyInstaller did not package it automatically because the dependency is indirect (via rasterio._env which calls certifi at runtime, not at import time).
- **Key difference:** The official script `packaging/windows/build_windows_installer.ps1` has `--collect-all rasterio` but `build_standalone.ps1` (used for quick builds) did not. Both need the same flags.
- **Fix applied:** Added `"--collect-all", "certifi"` and `"--collect-all", "rasterio"` to `build_standalone.ps1`.
- **Optimization?** NO — build/packaging fix.
- **Impact:** HIGH (exe does not open without the fix)
- **Tags:** #build #packaging #rasterio #certifi #crash #fix
- **Modified file:** `build_standalone.ps1`

---

## Consolidation Rules

An entry must be consolidated when:

1. It has been validated by repeated use (not an isolated case)
2. It represents a permanent difference (not a temporary bug)
3. Can be described in a generic way (does not depend on a single context)

When consolidating:

1. Add the information to the appropriate steering (`feature-map` or `optimizations`)
2. Mark the entry here as `[CONSOLIDATED]`
3. Add reference: "Consolidated in: flatcam-feature-map.md, section X"

---

## Statistics

- Total entries: 20
- Active: 20
- Consolidated: 0
- Obsolete: 0
- Last update: 2026-07-10

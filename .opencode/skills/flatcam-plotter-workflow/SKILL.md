---
name: flatcam-plotter-workflow
description: "Trigger: pen plotter, PCB Plotter, plotter G-code, GRBL_11_pen_plotter, pen up/down. Run the FlatCAM Plus plotter workflow safely."
license: Apache-2.0
metadata:
  author: "th3g3ntl3man"
  version: "1.0"
---

# FlatCAM Plus Pen Plotter Workflow

## Activation Contract

Load when working on the PCB Plotter tool, the `GRBL_11_pen_plotter` preprocessor, plotter G-code, the `Plotter Pen` preset, or its physical test protocol.

## Hard Rules

- The plotter is a separate GUI path: `Plugins > PCB Plotter` in `appPlugins/ToolPlotter.py`, preset `Plotter Pen`, preprocessor `GRBL_11_pen_plotter`. Do not alter the CNC milling flow to add plotter behavior.
- The `Plotter Pen` Tools DB preset is seeded at startup and must not overwrite existing user values; only fill missing fields.
- Every exported plotter G-code must pass `python scripts/validate_pen_plotter_gcode.py <file.gcode>` before physical use.
- The validator requires: no `M03`/`M04`, a `G20` or `G21` unit command, `G90`, a pen-up Z move before the first XY move, and no rapid XY travel while the pen is down.
- Preset starting values: pen width `0.4 mm`, pen down Z `-0.3 mm`, pen up Z `3.0 mm`, draw feed `600 mm/min`, Z feed `200 mm/min`, rapid `1500 mm/min`.

## Decision Gates

| Goal | Mode |
| --- | --- |
| Draw trace centerlines | `Follow` |
| Fill copper trace/pad areas for etching | `Fill` |
| Direct draw on copper | Usually no mirror for top layer; verify against the Gerber |
| Paper transfer to copper | Mirror is normally required |

## Execution Steps

1. Open the Gerber, then open `Plugins > PCB Plotter`.
2. Choose `Mode = Follow` or `Fill`; set mirror and apply the preset.
3. Generate the path, then generate the geometry from the opened geometry panel.
4. In `Plotter Operation`, confirm Z-offset and feeds, then `Generate Plotter Job`.
5. Export with `Export Plotter G-code`.
6. Validate:
   `python scripts/validate_pen_plotter_gcode.py <output.gcode>`
7. For physical tests, follow `PLOTTER_TEST_PROTOCOL.md` in order: air run, paper, copper coupon.

## Output Contract

Report: mode, preset values used, generated artifacts, validator result, and any mirror decision with its justification.

## References

- `PLOTTER_WORKFLOW.md` — full Follow/Fill and preset workflow (Turkish).
- `PLOTTER_TEST_PROTOCOL.md` — physical test procedure (Turkish).
- `preprocessors/GRBL_11_pen_plotter.py` — plotter preprocessor.
- `scripts/validate_pen_plotter_gcode.py` — automated G-code safety checks.
- `assets/examples/pen_plotter_20x20_square.gcode` — known test asset.

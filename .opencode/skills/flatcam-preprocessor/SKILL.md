---
name: flatcam-preprocessor
description: "Trigger: G-code preprocessor, post-processor, PreProc, GRBL, Marlin, laser, pen plotter output. Add or change FlatCAM Plus G-code generation."
license: Apache-2.0
metadata:
  author: "th3g3ntl3man"
  version: "1.0"
---

# FlatCAM Plus Preprocessor

## Activation Contract

Load when creating or editing a module under `preprocessors/`, changing emitted G-code, or wiring a new preprocessor into milling, drilling, or plotter output.

## Hard Rules

- Put each preprocessor in `preprocessors/<name>.py` and subclass `PreProc` from `flatcam_plus.appPreProcessor`.
- The class name is the user-visible preprocessor name. Registration is automatic: `ABCPreProcRegister` registers on class creation, and `load_preprocessors()` imports every `preprocessors/*.py`. Never add a central registry edit.
- Implement every abstract method: `start_code`, `lift_code`, `down_code`, `toolchange_code`, `up_to_zero_code`, `rapid_code`, `linear_code`, `end_code`, `feedrate_code`, `spindle_code`, `spindle_stop_code`.
- Read parameters from the `p` mapping: `p['feedrate']`, `p['z_cut']`, `p['z_move']`, `p['z_feedrate']`, `p['multidepth']`, `p['toolchange']`, `p['units']`, `p['obj_options']`, `p['xy_toolchange']`, `p['xy_end']`.
- Set `include_header`, `coordinate_format`, and `feedrate_format` on the class when the base defaults do not fit.
- Selection keys are `tools_mill_ppname_g` (milling/geometry) and `tools_drill_ppname_e` (drilling). Look up instances with `self.app.preprocessors[name]`.
- A pen plotter preprocessor must emit no `M03`/`M04`, must emit `G20`/`G21` and `G90`, and must lift Z before the first XY move.

## Decision Gates

| Target | Base to copy |
| --- | --- |
| Mach3-style milling | `preprocessors/default.py` |
| GRBL milling | `preprocessors/GRBL_11.py` |
| Marlin / Repetier | `preprocessors/Marlin.py` |
| Laser without spindle | `preprocessors/GRBL_laser.py` |
| Pen plotter | `preprocessors/GRBL_11_pen_plotter.py` |

## Execution Steps

1. Copy the closest base file and rename the class and file consistently.
2. Implement or override the methods that differ; keep output deterministic and free of trailing blank lines.
3. Use `self.coordinate_format % (p.coords_decimals, value)` and `self.feedrate_format % (p.fr_decimals, value)` for numeric output.
4. Do not modify the base classes for one-variant behavior; override in the subclass.
5. For plotter output, validate with `python scripts/validate_pen_plotter_gcode.py <file.gcode>`.

## Output Contract

Report: file and class name, methods implemented, emitted safety commands, selection keys, and validation command output.

## References

- `flatcam_plus/appPreProcessor.py` — `PreProc` contract and registration.
- `preprocessors/default.py` — full reference implementation.
- `preprocessors/GRBL_11_pen_plotter.py` — plotter-safe output example.
- `PLOTTER_WORKFLOW.md` — plotter generation and validation flow.

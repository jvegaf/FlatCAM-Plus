---
name: flatcam-testing
description: "Trigger: run tests, pytest, verify change, add test, headless GUI. Run and add tests for FlatCAM Plus without inventing tooling."
license: Apache-2.0
metadata:
  author: "th3g3ntl3man"
  version: "1.0"
---

# FlatCAM Plus Testing

## Activation Contract

Load when running tests, adding a regression test, or verifying a change in this repository.

## Hard Rules

- Run tests with `uv run --with pytest pytest tests -q`. `pytest` is NOT a project dependency; never assume it is installed.
- Run one file with `uv run --with pytest pytest tests/test_<name>.py -v`.
- `python flatcam.py` requires a real display. Do not assume or invent headless support; gate display-dependent checks or leave them as manual smoke tests.
- Importing `flatcam_plus.appPlugins`/`flatcam_plus.appObjects` pulls in PyQt6 and a live `App`. Keep pure logic in importable functions and test those; the existing `tests/test_classify_contours.py` deliberately duplicates logic for this reason.
- There is no CI, linter, formatter, or type-check configuration. Do not invent commands or claim they pass.
- Put scratch state outside the worktree in a `mktemp -d` directory; remove it after use.
- Verify behavior changes with a focused test first, then the full suite once.
- Follow ODD's test-first policy: observe RED before implementation, then GREEN, then refactor. Never invent or assume test evidence.

## Decision Gates

| What changed | Check |
| --- | --- |
| Pure geometry/algorithm function | Unit test with Shapely, no Qt import |
| Tool/plugin/object wired to `App` | Manual GUI smoke test plus any pure extracted function test |
| Preprocessor output | Render G-code through the app or a small harness; validate plotter output with the script |
| Docs or comments only | Structural readback; no test run required |

## Execution Steps

1. Identify whether the changed code can be imported without PyQt6 or an `App`.
2. If yes, add a focused test under `tests/` with plain `pytest` and Shapely or stdlib assertions.
3. If no, extract the pure decision into a function, test that, and keep the Qt wrapper thin.
4. Run the focused test, then `uv run --with pytest pytest tests -q`.
5. Record the exact commands and observed results; report skips or display limitations honestly.

## Output Contract

Report: test file added or changed, focused command result, full-suite result, and any check that could not run without a display.

## References

- `tests/test_classify_contours.py` — standalone Shapely-only test pattern.
- `scripts/validate_pen_plotter_gcode.py` — plotter G-code validator.
- `AGENTS.md` — canonical run/test commands.

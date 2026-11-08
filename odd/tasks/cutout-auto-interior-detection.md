# Cutout auto interior detection — hardening

Harden the interior/exterior contour detection that landed in `c848b5a` and put it behind
a Cutout option. The feature decides offset direction per contour, so a wrong answer
machines the wrong side of the material.

## Specs

**S1 — Classify by containment depth, not by area.**
A contour's role is decided by how many other filled contours contain it: even nesting
depth (0, 2, 4…) is material and gets the offset outside; odd depth (1, 3, 5…) is a hole
and gets the offset inside. The current rule — "the polygon with the largest filled area
is the exterior, anything whose representative point falls inside it is a hole" — must
go. Required cases:
- board outline with an internal slot → outline outside, slot inside (must keep working);
- a pad inside a slot → depth 2 → material;
- a panel where one board is larger than the outline → classification must not depend on
  which polygon is biggest;
- a mouse-bite frame, where the frame is a set of arcs around a board;
- a contour that cannot be classified at all → see S3.

**S2 — Use every interior ring.**
`buffered.interiors` is a list. Where the offset lands inside a hole, all of its rings
must be carried into the resulting geometry, not only `interiors[0]`. Extra rings are
currently dropped without a word.

**S3 — Never fail silently.**
A contour whose classification raises, or which no filled contour can describe, must
produce an `app.log.warning` naming the contour index and the reason, and then be treated
as exterior. `except Exception: pass` is not acceptable.

**S4 — The behaviour lives behind a Cutout option and defaults to on.**
Add `tools_cutout_auto_interior` to `flatcam_plus/defaults.py` in the existing
`tools_cutout_*` family, expose it in the Cutout UI next to the other Gerber options, and
persist it like its neighbours. Default `True`, because the behaviour is already
unconditional in `dev`: defaulting to off would silently revert every user's internal
slots to the wrong side. When the option is on and detection runs, log one line naming
how many contours were classified as holes, so the user can see the tool took that
decision.

**S5 — Off means exactly the old behaviour.**
With the option off, every contour takes the exterior path in every branch, byte-identical
to the code before `c848b5a`: no classification call, no warning, no interior rings.

**S6 — Tests exercise the production code.**
`tests/test_classify_contours.py` must keep importing `CutOut._classify_contours` from the
plugin module and must never carry its own copy of the logic. New behaviour is covered
through the same seam plus the option, not through reimplementations.

## Tasks

| ID | Task | Specs | Route | Commit |
| --- | --- | --- | --- | --- |
| T1 | Add `tools_cutout_auto_interior` to defaults, UI and persistence | S4 | worker | not started |
| T2 | Rewrite `_classify_contours` as depth parity over filled contours, with warnings | S1, S3 | worker | not started |
| T3 | Wire the option and all interior rings into the offset branches | S2, S4, S5 | worker | not started |
| T4 | Tests: depth cases, multi-ring, unclassifiable warning, option off parity | S1–S6 | worker | not started |

## Log

**L1** — User: "vale encaralos" — accepting the four gaps named in the comment posted on
fork PR #18, measured against the code in `dev` rather than against that PR's diff:
largest-area-is-exterior with no notion of depth; only `interiors[0]`; `except
Exception: pass`; and no way for a user to turn the behaviour off.

**L2** — Decision (parent, 2026-11-08): the option defaults **on**. The behaviour is
already unconditional in `dev`, so a default of off would change every existing user's
output, which is the class of unrequested change this cluster has been rejecting all
along. The option is an escape hatch, not a migration.

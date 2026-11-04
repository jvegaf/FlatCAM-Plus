---
name: flatcam-odd-workflow
description: "Trigger: ODD, Organic Driven Development, feature work, task tracking, implementation plan. Execute FlatCAM Plus work under the ODD workflow."
license: Apache-2.0
metadata:
  author: "th3g3ntl3man"
  version: "1.0"
---

# FlatCAM Plus ODD Workflow

## Activation Contract

Load for every authorized implementation, bugfix, refactor, or feature in this repository, and whenever a task references `odd/tasks/<feature>.md`.

## Hard Rules

- Follow ODD in order: authorize, explore, resolve uncertainty, classify, track, implement, close. Read-only requests never write.
- Small work (understood, contained risk, resumable from the diff) runs inline with no task file. Large work requires `odd/tasks/<feature-name>.md` before the first source write, with a header, `## Specs` (`S#`), `## Tasks` (`T#` linked to `S#`), and `## Log` (`L1` = the original request verbatim).
- When a feature document exists, read it until `## Log` before editing. Work only the assigned `T#` and `S#`; report which `S#` you covered.
- Requirement changes append a verbatim `## Log` entry, rewrite only the affected `S#`, and reopen only the linked tasks.
- Test first: observe RED, implement GREEN, then refactor. Assert observable effects (output, exit code, persisted data), not implementation details.
- Reuse existing helpers for shared state; never duplicate a registration, parser, or option path with a different shape.
- Keep scope within the authorization. Do not add unrequested behavior, dependencies, or tooling.
- Commit reviewable work units of about 400 authored changed lines, with tests and docs alongside the behavior, using Conventional Commits. Branch first when on the default branch.
- Close every change with `Risk: item N (reason)` or `Risk: none`, naming failed or skipped checks honestly.

## Decision Gates

| Situation | Action |
| --- | --- |
| Change fits one understood diff | Work inline; no task file |
| Multi-session, external wait, or separate deliverables | Create the feature document and mirror it |
| No runnable RED exists | State the exception and run a proportionate structural or functional check |
| Requirement changes mid-flight | Append to `## Log`, update affected `S#`, reopen linked `T#` |

## Execution Steps

1. Confirm the request authorizes a change; if not, stay read-only.
2. Locate the code with CodeGraph or targeted grep; read only owning functions.
3. Classify the task; create or read the feature document for large work.
4. Write or identify the failing check, then implement the smallest correct change.
5. Run the focused check, then the full suite once.
6. Review `git diff` for scope, tests, and docs; commit per work unit.
7. Report outcome, `S#` coverage, verification evidence, and the Risk line.

## Output Contract

Return: task and `S#` covered, files changed, RED/GREEN evidence or stated exception, focused and full check results, skipped checks, commit(s) if any, and `Risk: item N (reason)` or `Risk: none`.

## References

- `AGENTS.md` — canonical ODD section and run/test commands.
- `odd/tasks/` — feature documents for tracked work.
- `.kiro/specs/` — examples of requirement, design, and task documents.

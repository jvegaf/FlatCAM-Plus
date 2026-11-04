# Agent docs and project skills

Objective: give future agents verified repository guidance, project-scoped skills, a mandatory ODD workflow and a CodeGraph index.
Branch: `dev` | Delivery: one direct commit on `dev` plus an uncommitted local index | Test runner: `uv run --with pytest pytest tests -q`

## Specs

- **S1 — Agent guide**: `AGENTS.md` documents the verified run/test entrypoints, package map and repo-specific gotchas.
- **S2 — Project skills**: seven project-scoped skills under `.opencode/skills/`: `flatcam-repo-map`, `flatcam-tool-plugin`, `flatcam-object-model`, `flatcam-preprocessor`, `flatcam-tcl-command`, `flatcam-testing`, `flatcam-plotter-workflow`.
- **S3 — ODD workflow**: `AGENTS.md` states that all development follows Organic Driven Development, and `flatcam-odd-workflow` is available as a project skill (eight skills total).
- **S4 — CodeGraph**: the repository has its own `.codegraph/` index, excluded through `.git/info/exclude` rather than `.gitignore`.
- **S5 — Skill registry**: `.atl/skill-registry.md` lists the project skills; the `.atl/` directory is gitignored.

### Acceptance criteria

| Spec | Check |
| --- | --- |
| S1 | `AGENTS.md` exists and its claims were verified against the repository |
| S2, S3 | Eight `SKILL.md` files under `.opencode/skills/` |
| S4 | `codegraph_explore` answers from the FlatCAM Plus index; `git status` does not show `.codegraph/` |
| S1-S3 | `uv run --with pytest pytest tests -q` → 13 passed at creation time (18 passed on 2026-11-04) |

## Tasks

- **T1 — AGENTS.md** (`S1`): verified run/test commands, package map, conventions and gotchas. Route: inline. Status: done in `95a1bc9`.
- **T2 — Project skills** (`S2`): seven skills plus `AGENTS.md` registration. Route: inline. Status: done in `95a1bc9`.
- **T3 — ODD adoption** (`S3`): `AGENTS.md` development-workflow section, `flatcam-odd-workflow` skill, pointers from `flatcam-repo-map` and `flatcam-testing`. Route: inline. Status: done in `95a1bc9`.
- **T4 — CodeGraph index** (`S4`): `gentle-ai codegraph init --cwd <root>`. Route: inline. Status: done; not committed (`.git/info/exclude`).
- **T5 — Skill registry** (`S5`): `gentle-ai skill-registry refresh --force`. Route: inline. Status: done; local-only artifact.

## Log

- **L1 — Original request (not preserved)**: Engram session summary #140 records the goal as creating a compact, verified `AGENTS.md`; observation #144 records a request to analyze the repository and provision the skills needed for correct development. The verbatim user prompts were not captured.
- **L2 — Discoveries recorded in the guide**: the real entrypoint is `python flatcam.py`; `src/flatcam_plus` is a stub; Python is 3.14 while `README.md`, `requirements.txt` and `Makefile` are stale; `pytest` is not a project dependency; tool plugins are instantiated in `App.install_tools` and appended to `self.app_plugins`; preprocessors self-register, only Tcl commands need a manual alphabetical import; `appVersion.APP_VERSION = "1.2.0"` is the app version while `defaults.py` version `8.992` is the preferences-format version.
- **L3 — Verification**: `uv run --with pytest pytest tests -q` → 13 passed at creation time. `uv run --with pytest pytest tests -q` → 18 passed on 2026-11-04.
- **L4 — CodeGraph evidence**: index built with 341 files, 8,795 nodes and 37,304 edges (~48 MB); MCP queries work with `projectPath`, and CLI intelligence reads need `codegraph sync -q <root>` first.
- **L5 — Reconstruction note**: this document was generated from Engram observations #139, #140, #144, #145 and #146 on 2026-11-04 because no ODD log existed when the work was implemented.

Next step: none.

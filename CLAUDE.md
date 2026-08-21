# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

`arch-review` is an eval environment for the Prime Intellect Environments Hub. The model reads a diff with seeded, documented defects and writes a code review. The score measures defect recall plus precision, penalizing false alarms.

The project is the qualifying credential for the SWE-Swiss (Full Pipeline) bounty. See `README.md` for the phase checklist and `docs/01-bounty-context.md` for the bounty context.

## Current state

Planning-only. No code exists yet; `docs/0*.md` hold the plan.
Phase 2 introduces the Python verifier — `ReviewData`/`ReviewTask`/`Taskset`, judge, rewards — per `docs/03-verifiers-v1.md` and `docs/07-plan.md`.

## Planned commands

No build, lint, or test exists yet. The intended toolchain is uv plus the Prime Intellect CLI:
- `uv run init arch-review-v1` — scaffold the taskset (Phase 2)
- `uv run eval arch-review-v1` — run the eval (Phase 2)
- `prime login` / `prime env push` — publish (Phase 4)

## Repo rules

- The repo is public. It is the showcase.
- No PII. Seed defects into synthetic code, or into OSS under a permissive license, citing the origin.
- Curation stays visible. Every task carries an authorship comment explaining its defect.

## Architecture decisions

`docs/adr/` holds the accepted decisions. Read the ADRs that touch the area you are about to change. Start at `docs/adr/README.md` for the index.

If your work contradicts an ADR, say so explicitly instead of overriding it silently.

**Open conflict — ADR-0001.** That ADR requires US English for all project output. The existing `README.md` and `docs/0*.md` are in Portuguese. Nothing was translated. Decide whether to translate them or to amend ADR-0001.

## Agent skills

- **Issue tracker** — GitHub Issues via the `gh` CLI. See `docs/agents/issue-tracker.md`.
- **Triage labels** — five canonical labels. See `docs/agents/triage-labels.md`.
- **Domain docs** — how skills consume `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.

`CONTEXT.md` does not exist yet. Do not create it upfront. The `/domain-modeling` skill creates it when terms actually need resolving.

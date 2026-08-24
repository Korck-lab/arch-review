# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

`arch-review` is an eval environment for the Prime Intellect Environments Hub. The model reads a diff with seeded, documented defects and writes a code review. The score measures defect recall plus precision, penalizing false alarms.

The project is the qualifying credential for the SWE-Swiss (Full Pipeline) bounty. See `README.md` for the phase checklist and `docs/01-bounty-context.md` for the bounty context.

## Current state

The verifier is implemented and scored. `arch_review_v1/` holds the taskset,
the two-judge pipeline, and the F1 reward; `arch_review_v1/tasks/` holds 6
curated scenarios plus 15 single-defect sub-tasks derived from them (ADR-0029).
`docs/0*.md` hold the plan and the bounty context.

## Commands

```bash
uv run pytest                  # 79 tests
uv run mypy arch_review_v1     # type check
uv run eval arch-review-v1     # run the eval (needs a client + judge endpoint)
prime env push arch-review     # publish to the Hub
```

`tools/claude_proxy.py` is a **dev-only** shim that serves the eval from a local
`claude -p` instead of a paid provider. It is not part of the published
environment and nothing in `arch_review_v1/` imports it.

## Repo rules

- The repo is public. It is the showcase.
- No PII. Seed defects into synthetic code, or into OSS under a permissive license, citing the origin.
- Curation stays visible. Every task carries an authorship comment explaining its defect.

## Architecture decisions

`docs/adr/` holds the accepted decisions. Read the ADRs that touch the area you are about to change. Start at `docs/adr/README.md` for the index.

If your work contradicts an ADR, say so explicitly instead of overriding it silently.

**Resolved — ADR-0001.** All project output is US English. README, `docs/0*.md`, and filenames were translated (`ffdc113`).

## Agent skills

- **Issue tracker** — GitHub Issues via the `gh` CLI. See `docs/agents/issue-tracker.md`.
- **Triage labels** — five canonical labels. See `docs/agents/triage-labels.md`.
- **Domain docs** — how skills consume `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.

`CONTEXT.md` does not exist yet. Do not create it upfront. The `/domain-modeling` skill creates it when terms actually need resolving.

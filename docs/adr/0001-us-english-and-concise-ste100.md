# ADR-0001: US English and Concise STE100 for all project output

## Status

Accepted

## Context

The project author converses with Claude Code in many languages. Portuguese is common. The session output style changes by project. Artifacts then drift in language and style. Code comments, docs, issues, and commit messages lose consistency.

## Decision

Write all project output in US English. Use the Concise STE100 output style. This holds even when the conversation happens in another language. It holds even when Concise STE100 is not the session default.

## Consequences

Artifacts stay uniform across sessions and languages.
Translate user input into US English before recording it in the repo.
Non-English input is a signal to produce English output, not to mirror the input.

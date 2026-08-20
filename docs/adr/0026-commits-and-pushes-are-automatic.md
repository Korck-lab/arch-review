# ADR-0026: Commits and pushes are automatic; do not ask

## Status

Accepted

## Context

The agent asked for permission before each commit and push. The owner answered "commit and push" every time. Asking again is waste.

## Decision

After any change, commit and push without asking. Work directly on `main`. The owner may still ask for a commit to be amended or undone.

## Consequences

Faster turnaround. The remote stays current with the repo. The owner gives a direct instruction to stop when they want review first.

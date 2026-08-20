# ADR-0013 — Content gates run at every boundary where text can reach a delivered artifact

## Status

Accepted

## Context

A content rule was enforced by a pattern table living privately inside one module, run once, over one field shape. It had never failed — it had never been asked. Violations reached the delivered artifact through three structural holes, each independently sufficient. The table was unreachable: module-private, imported by nothing, so the last points at which text can reach the artifact had no check at all. It saw only one field shape, so hand-entered units and aggregate fields bypassed it. And it reported the first match per pattern, so a reviewer could fix one occurrence, re-run, see green, and ship the rest. A fourth gap sat outside the tooling entirely: the private staging copy — the artifact the human actually reads before approving — was never scanned.

## Decision

1. **One table, an importable versioned module, every chokepoint.** Every boundary at which text can reach a document runs the same check: at generation, at manual entry, at conversion into an execution plan, at staging, and immediately before the live write.
2. **Scan private and staged copies too.** A private copy is still a document a human reads, and still the rehearsal for the live write.
3. **Report every match, never the first per pattern.**
4. **Rule names join the tool namespace**, disjoint by construction from project-data identifiers.
5. **Two severities.** A *blocking* rule is never legitimate in a delivered artifact and refuses. A *review* rule has a plausible innocent form and is surfaced for a human read.
6. **Ownership decides block versus warn.** A blocking hit in a field the project owns refuses. The identical hit in a counterpart's field is a warning, because a gate that blocked on it would pressure someone into committing the violation the gate exists to prevent.
7. **The gate refuses; a human repairs.** Never auto-strip: silently rewriting prose to satisfy a pattern is how meaning gets lost.
8. **Every rule carries both fixtures** — a positive one proving it detects, and a negative one drawn from real accepted output — so a pattern that would have blocked good work fails its own test before it ever blocks anyone.

## Consequences

The gap closes at the point of use rather than by discipline. Cost: more false positives to read, ongoing calibration of ownership detection, and one more refusal class arriving on a deadline. The failure mode to watch is a gate that fires too often, gets switched off, and then gates nothing — tune the patterns rather than the enforcement.
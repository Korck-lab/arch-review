# ADR-0015 — Resolve formatting-encoded semantics before diffing or linting

## Status

Accepted

## Context

Some sources encode meaning in formatting rather than in characters: struck-through text means deleted, a color means added, a style means approved or owned by someone else. The convenient plain-text export drops all of it, so deleted content comes out indistinguishable from content nobody touched.

When every tool reads the flattened export, the failure is silent and it points the wrong way. It does not crash and it does not return empty — it produces a large, confident, wrong finding list. On one measured document, dozens of formatting-encoded deletions were invisible to the flattened view, and linting it produced roughly an order of magnitude more phantom findings than real ones. Each phantom would have read as a defect a counterpart had just introduced, when in fact each was a definition they had correctly deleted.

## Decision

1. **Obtain a representation that preserves the formatting, and derive a semantic analysis view from it** before any diff, lint, or classification.
2. **Verify the converter before trusting it, every run.** Re-run it with the semantic transformation disabled and compare against the independently obtained flat representation; they must agree, and any residual difference is investigated rather than waved through. A converter that has not been checked against the real export is another silent failure waiting to happen.
3. **Reason from the resolved view.** Read content, requirements, and workflow from it.
4. **Keep the raw representation as the drift baseline.** Drift detection is a byte comparison against what the source actually serves, so it must keep comparing raw to raw. The resolved view lives alongside the raw one, never in its place.
5. **Read from resolved; count and match against raw.** Where a write surface operates on the raw representation, every search string and every expected-count guard must be derived from raw. A plan built from resolved-view counts under-counts, and its guards will then fire on correct operations. This read/write asymmetry is the single most error-prone consequence of keeping two views.
6. **Adjudicate the formatting-encoded edits as their own provenance bucket** — the runs, their authorship, and what ignoring them would have cost — rather than dropping them.
7. **An artifact of the resolved view is not a defect.** A deletion that leaves an empty item behind is the convention working as designed. Never file it.

## Consequences

Analysis reflects the artifact its readers actually see, and the largest single class of false blame against a counterpart is removed before findings are framed. Cost: two representations and a verification comparison per revision instead of one; the converter reimplements part of someone else's layout rules and is pinned by that check rather than by a spec, so an upstream change surfaces as a verification failure that needs a human. Residual gap: formatting that marks *additions* may still be indistinguishable in both views, and is covered only while a pre-change baseline exists to compare against.
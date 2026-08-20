# ADR-0002 — Diffs segment by the source's own units and align by content

## Status

Accepted

## Context

When a diff is cited as evidence rather than read as a convenience, its completeness is load-bearing: a missed fragment is a missed finding, and a spurious one is an accusation against another author. Two failure modes dominate, and both are silent.

The first is reconstructing structure the source does not have. An implementation built on an assumed input shape — that the source wraps at a fixed width — folded a whole document into one block because the assumed separator was almost absent. The premise was never measured; what had been observed was a terminal wrapping the output, not the source.

The second is aligning by position. Comparing element *i* to element *i* means one insertion shifts every later element into a false "changed". Injecting a single formatting-neutral unit turned a handful of real differences into dozens of reported ones. The approach had survived earlier inputs only because every addition happened to land inside an existing block — luck, not method.

## Decision

1. **Use the source's own smallest reliable unit; never reconstruct one.** Records, lines, blocks, or syntax nodes that the format already delimits are the segmentation. Before deriving units from an assumed property of the input, measure that property.
2. **Align by content, not by index.** Canonicalize each unit and align the canonical sequences, so an inserted or deleted unit reports as an insert or a delete rather than displacing everything after it.
3. **Refine replacement regions hierarchically.** When a region leaves unmatched material on both sides — the signature of reflowed or restructured text — join each run and re-diff at a finer granularity, so only the content that actually changed survives.
4. **Canonicalization and similarity may select pairings; they may never decide existence.** A heuristic may choose *which* units to compare; it may never decide *whether* a difference is real. Anything canonicalization would drop is classified, never silently discarded.
5. **Report coordinates back into the source** so every fragment can be re-found and cited.

## Consequences

Insertions stop poisoning every later comparison, and the exhaustiveness claim becomes defensible because it rests on the source's own structure rather than on an assumption about it. Cost: the refinement path adds real implementation complexity, and unmatched units inside a replacement region are still paired by a similarity threshold. That heuristic is confined to pairing and is never permitted to suppress a difference.
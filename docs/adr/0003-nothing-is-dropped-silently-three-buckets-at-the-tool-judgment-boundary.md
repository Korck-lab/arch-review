# ADR-0003 — Nothing is dropped silently: three buckets at the tool/judgment boundary

## Status

Accepted

## Context

Any tool that filters, normalizes, or suppresses input before a human or an agent reads it can fail in two directions. A false positive costs attention and can make a wrong claim about another author. A false negative — normalization quietly eating a real difference — costs a missed finding and is unrecoverable, because nothing in the output records that anything was suppressed. Unguarded normalization is the dangerous half: the output looks clean.

## Decision

1. **Three buckets, exactly one per detected difference.** *Signal* (deterministic, actionable, cite it), *review required* (provably ambiguous — a rule cannot decide, a judgment layer must), *suppressed* (provably cosmetic; dropped from the signal list, recorded with the rule that dropped it).
2. **The tool finds; the judgment layer adjudicates.** A deterministic producer describes differences and never infers intent. Once the finder is a model, its output stops being citable evidence and becomes inference.
3. **The suppression ledger is mandatory output, not a debug flag.** It is the only thing that makes the false-negative direction auditable.
4. **Ambiguity is grouped losslessly, never resolved by heuristic.** Collapse consecutive ambiguous items into runs stamped with a mechanical property — for example, whether an ordinal sequence is intact. Grouping is arithmetic, adds no judgment, and merges no distinct evidence; it is what turns an unreadable list into a bounded number of decisions, and it is what keeps the adjudication step affordable. A rule that cannot decide escalates rather than guessing.
5. **Every downstream claim carries provenance** naming its bucket, its source location, and — where the domain has more than one author — whose content it came from. A claim without that provenance is invalid.

## Consequences

The reviewable delta shrinks from "everything" to a bounded list, and suppression becomes auditable rather than invisible. The cost is a required adjudication step, bounded by grouping, and a classification contract that must stay stable. A rule that escalates instead of guessing is the intended behavior, not a regression. The ledger must be read, at least sampled, or it becomes a write-only file that satisfies the letter of the rule and none of its purpose.
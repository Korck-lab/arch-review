# ADR-0017 — Outbound messages follow the project's concise output style

## Status

Accepted

## Context

Drafts written for outbound channels had grown past four hundred words and had settled into the recipients' house style: restate the question, frame it, explain the background, sign off. The length is actively costly, not merely inelegant. The reader is scanning several threads at once, so a point buried in the fourth sentence competes with someone else's message that leads with it. And the measurements *are* the message — the counts, the identifiers, the citations. The prose around them adds nothing a reader of that channel needs, and dilutes what matters.

The concise style already existed and was already active for interactive replies; it simply was not applied to outbound text, because drafts were being written into files and therefore treated as documents rather than as messages.

## Decision

Outbound drafts obey the project's concise output style on the same terms as interactive replies.

1. **Outcome first.** The first line states the result or the action required. Never open by restating what the other person asked, and never with what you are about to do.
2. **One bullet per item, one line each.** Four things raised means four bullets. Prose only where a point genuinely needs more than a sentence.
3. **Keep, always:** every number and measurement, every identifier, every resolvable citation, remaining uncertainty, and the status of anything unresolved or escalated.
4. **Cut:** restatement of the question, framing openers, explanation of what the reader already knows, apologies, sign-offs.
5. **Honesty overrides brevity.** An open defect, a skipped step, an unverified number, and a correction of something previously sent are stated in full regardless of length. Brevity is a word-count discipline, never a content one.
6. **Write to the constraint; do not trim to it.** Post-editing a long draft down does not work in practice — by the time the length is noticed, the draft is already staged. This is the clause that makes the rest operational.
7. **Automation drafts; a human sends**, unless the project has an explicit recorded policy authorizing automated posting. Treat staging as destructive: it may silently replace whatever is already waiting in that channel.

## Consequences

The finding is the first thing read, which is the only property that decides whether it gets acted on, and drafts become checkable — a bullet either carries a measurement or it is filler. Risk: terseness can read as curt, and compression is where a caveat gets cut along with the framing. When a cut is ambiguous, keep the caveat and cut a sentence of framing instead.
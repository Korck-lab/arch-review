# ADR-0018 — A failing gate is a defect to investigate; expectations are re-anchored, never retuned

## Status

Accepted

## Context

A deterministic precision gate went red. The first reflex — "pre-existing, not mine" — is rejected. The tempting fix, editing the expectation to match the new numbers, looked identical to the correct fix from the outside and was distinguishable only by investigating. The investigation found the pinned values were never stale: they correctly described a frozen baseline. The pin's *path* pointed at the live artifact instead, so every committed edit moved the count further away from it. A second defect compounded it: a missing pinned corpus file silently skipped the anchor instead of failing.

## Decision

1. **No gate failure is ever "not mine", skipped, or made green by editing the expectation.** Every red gate is investigated to a named root cause before any expectation changes.
2. **An expectation may be edited only when all four hold:** (a) the referent is correct and named — the artifact the values are true about is stated explicitly; (b) the delta traces to identified committed changes to that referent; (c) the values are re-derived deterministically from rule code independently known not to have changed; (d) every anchor that remains true about some frozen artifact is preserved rather than overwritten. Overwriting a true anchor so the current input passes is test-gaming, however it is phrased.
3. **A pinned expectation names its referent's mutability.** A pin against a frozen artifact can never legitimately drift. A pin against a live artifact moves on every committed edit, so it must be re-verified in the same commit that moved its referent. Prefer two anchors — one frozen, one current — over a single ambiguous pin.
4. **A missing pinned fixture is a failure, not a skip.** A skipped anchor is "correct but unreachable", which is precisely the silent-pass hole the gate exists to close.
5. **Never change the producing code to emit the expected number.** This is the second and worse way to fake a pass: it leaves the gate green and the expectation untouched while fabricating the exact class of defect the gate was built to catch.

## Consequences

The gate stays trustworthy, historical evidence is not erased to manufacture green, and drift becomes diagnosable in one read because each pin declares what it is true about. Cost: a live-referent pin carries an ongoing same-commit obligation, and legitimate corpus or parser corrections require documented re-anchoring. Guard: a delta with no committed referent change behind it is a rule bug, not a pin refresh.
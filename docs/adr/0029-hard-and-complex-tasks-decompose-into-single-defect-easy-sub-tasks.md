# ADR-0029 — Hard and complex tasks decompose into single-defect easy sub-tasks; the splitter enforces the split

## Status

Accepted

## Context

A hard task carries three to four gold defects plus two or more distractors. The reviewer reads one diff and must find every defect while ignoring every distractor. A cheap reviewer model finds the loudest defect and misses the rest, so hard-task recall caps the mean score. The pilot set hit this ceiling: every hard pilot scored below the easy floor.

The spec (issue #12) answers with decomposition. Split a hard task into one easy sub-task per defect. Each sub-task isolates one mechanism in a minimal diff, with no distractors, so a cheap reviewer can perfect it. The floor becomes perfectable; the hard task keeps its ceiling for a stronger reviewer.

Decomposition must be trustworthy or it is curation theater. A sub-task that leaks a second defect, carries a line owned by another defect, or fails the gold contract poisons the measurement it was built to fix. The split must therefore be a pure function of its inputs: same input task, byte-identical output directories. Determinism is what lets the pipeline ship sub-tasks it never hand-checked.

Not every defect splits cleanly. Two defects that interleave on the same lines, or share a name bound by the parent diff, cannot be cut apart. Forcing the cut ships a sub-task with an incoherent diff or a phantom reference. The spec's answer is explicit: those are hand-written by the author, never synthesized (spec issue #12: "the author hand-writes"). The pilot loop confirmed both failure modes — t002 d1/d2 interleave in orders.py, t004 d3/d4 both reference the orphan `_drain_jobs` — and confirmed the resolution: mark them, ship nothing.

## Decision

1. **Every hard or complex task ships its decomposition.** The taskset contains the parent task plus one easy sub-task per defect. A task without sub-tasks is incomplete.
2. **The splitter enforces the split.** `decompose` and `generate` are pure functions: no model calls, no clocks, no randomness. Rerunning on the same input produces byte-identical `diff.patch`, `context.md`, `gold.yaml`, and `_meta.yaml`.
3. **The split is gated, not hoped for.** A sub-task ships only when it passes all coherence gates: its diff lines are contained in the parent diff, no changed line is owned by another defect, the gold inherits the parent defect verbatim, and the sub-task validates against the dataset contract.
4. **An unsplittable defect is flagged, never forced.** `decompose` marks it `needs-hand-write` with a recorded reason. The curator writes that sub-task by hand or holds the defect. A split the gate rejects is never committed.
5. **Enforcement lives in the test suite.** The taskset test pins the exact parent-plus-subtask membership; the taskgen tests pin determinism, containment, isolation, gold inheritance, and contract validity. A change that breaks any property fails the suite, and the eval will not load the broken set.

## Consequences

The easy tier becomes perfectable by the cheap reviewer, so the mean score is no longer capped by the hard ceiling. The hard tasks remain in the set for the stronger reviewer. Cost: the taskset grows to roughly one directory per defect (19 tasks today: 6 pilots plus 13 clean sub-tasks), and curation runs the generator and the suite before publishing. Risk: a hand-write that never lands leaves the parent task without a complete sub-task set; the pinned test surfaces that gap instead of hiding it. A split that cannot be made coherent stays visible as `needs-hand-write`, never shipped silently (ADR-0003).

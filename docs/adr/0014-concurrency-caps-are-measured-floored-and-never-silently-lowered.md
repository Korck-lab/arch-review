# ADR-0014 — Concurrency caps are measured, floored, and never silently lowered

## Status

Accepted

## Context

A pipeline fanned out concurrent subprocesses at a guessed cap. Two questions had never been answered: is the work actually running in parallel, and what is the right number. The workload turned out to be I/O-bound — each worker launches a process and waits on network round trips, with no local computation of consequence — so core count does not cap concurrency the way it would for CPU-bound work, and the guessed cap was leaving most of the available throughput unused.

## Decision

1. **Set the cap from a measurement, not a guess.** Keep a reproducible benchmark in the repo that exercises the same call shape as the pipeline under realistic load, and record its table in this record so the question can be re-run rather than re-argued.
2. **Pick the knee, not the maximum.** Throughput that scales and then flattens has one defensible setting: the last point before flattening. Past it you pay a large concurrency increase for a small throughput gain, and load a shared resource other consumers depend on.
3. **A floor, enforced as a hard error at startup.** The previously proven value is the floor; a configured cap below it fails loudly at startup rather than silently halving throughput. Lowering the floor itself requires a new benchmark recorded here. This is a mechanism, not a review step — "require an explicit decision" is satisfied by anyone who decides, and is invisible one session later.
4. **One shared resolver, and the resolved value is logged in the run record.** Separate phases with their own constants drift apart, and an ambient environment variable is invisible in the artifact.
5. **Do not derive worker counts from core count for I/O-bound work.** It models the wrong constraint and leaves the measured optimum unused.
6. **Per-call spend is not a reason to lower the cap.** Concurrency changes wall-clock, not the number of calls, so "it costs too much" is not by itself an argument. Throttling, retry amplification, contention, and per-hour infrastructure charges *are* legitimate reasons — and they are settled by re-measuring, not by asserting.
7. **Re-run the benchmark when the workload, host, upstream limits, retry behavior, or pricing materially change** — not when someone has an opinion about it.

## Consequences

The critical path runs at the measured optimum, and a config change that halves throughput becomes an error instead of a mystery. Cost: more memory and more sockets in flight, a higher chance of tripping an upstream rate limit, and a recurring measurement obligation. Retry behavior at the call seam is the thing to watch after raising the cap.
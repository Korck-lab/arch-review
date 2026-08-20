# ADR-0009 — Classifier gates are calibrated blind, anchored, and floored, or they are not evidence

## Status

Accepted

## Context

A statistical classifier used as a release gate is only as good as its calibration, and calibration is where the bias enters. Three defects were found in one instrument, all invisible from the outside. A calibration corpus drawn from texts that had already passed the gate appeared to license loosening the threshold; a blind corpus refuted it. A known-good input scoring above the flag line went undetected, because nothing checked the instrument's own frame of reference. And every documented false positive was short text. Published work on comparable classifiers reports high false-positive rates on some legitimate populations, so an uncalibrated gate can be worse than no gate.

## Decision

A classifier is used as a gate only where a project requirement and an approved data policy justify it, and only after all of the following hold.

1. **Blind corpus.** Calibration samples are selected by provenance and length only, never by score, and no sample is dropped for scoring badly. A corpus of survivors measures the gate, not the population.
2. **Anchor set, not anchor pair.** Carry in-domain known-good and known-bad anchors. If any known-good anchor flags, or any known-bad anchor passes, the run **parks** and produces no evidence at all. Input may never override an anchor.
3. **The threshold moves one way only.** The loader rejects any threshold looser than the current evidence-backed line; loosening requires a fresh blind calibration recorded alongside the change. The observed false-positive rate at the chosen line is reported with the score.
4. **Length floor.** Inputs below the measured floor are scored for diagnosis, banded as such, and cannot flag.
5. **Topology follows validation evidence.** Choose single model or ensemble from measurement, not convention. Where an ensemble is used, combine correlated members within a family before combining across families, so a redundant pair does not vote twice.
6. **Declare the consequence in advance, and let it follow ownership.** A flag on text the project owns is actionable per the declared policy. A flag on a counterpart's text is a warning surfaced through the normal channel, never a license to edit their work.
7. **A flag changes process, never the conclusion.** It is evidence about the text's register, not a finding about its subject.
8. **Confidential material does not go to unapproved third-party services** merely to obtain a second score.

## Consequences

The gate becomes defensible and reproducible, and a miscalibrated run is loud rather than silently wrong. Cost: anchors, a blind corpus, a measured floor, and a data-policy review are real setup work, and inputs near the boundary still need a human read. Risk: treating the score as a target rather than a stop condition — guarded separately.
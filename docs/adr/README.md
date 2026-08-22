# Architecture Decision Records

General engineering decisions, usable across projects. They generalize the ADRs of the humanedge engagement (2026-08-12..18) via an adversarial review (Opus 5 vs gpt-5.6-sol, consensus by judge). Each entry strips humanedge-specific machinery and keeps the idea.

## Index

| ADR | Decision |
|---|---|
| [0001](0001-us-english-and-concise-ste100.md) | US English and Concise STE100 for all project output |
| [0002](0002-diffs-segment-by-the-source-s-own-units-and-align-by-content.md) | Diffs segment by the source's own units and align by content |
| [0003](0003-nothing-is-dropped-silently-three-buckets-at-the-tool-judgment-boundary.md) | Nothing is dropped silently: three buckets at the tool/judgment boundary |
| [0004](0004-verifying-a-write-to-a-live-artifact-you-cannot-fully-observe.md) | Verifying a write to a live artifact you cannot fully observe |
| [0005](0005-designed-material-is-read-from-its-source-never-reconstructed.md) | Designed material is read from its source, never reconstructed |
| [0006](0006-delivered-text-is-self-contained-state-the-artifact-never-the-process.md) | Delivered text is self-contained: state the artifact, never the process |
| [0007](0007-tool-minted-identifiers-live-in-a-namespace-that-cannot-collide-with-project-data.md) | Tool-minted identifiers live in a namespace that cannot collide with project data |
| [0008](0008-one-observation-contract-between-the-deterministic-layer-and-the-model-layer.md) | One observation contract between the deterministic layer and the model layer |
| [0009](0009-classifier-gates-are-calibrated-blind-anchored-and-floored-or-they-are-not-evidence.md) | Classifier gates are calibrated blind, anchored, and floored, or they are not evidence |
| [0010](0010-the-pipeline-drafts-the-owner-s-control-is-approval-not-authorship.md) | The pipeline drafts; the owner's control is approval, not authorship |
| [0011](0011-if-it-is-hand-launched-in-a-chat-session-it-is-not-automated.md) | If it is hand-launched in a chat session, it is not automated |
| [0012](0012-a-gate-is-a-stop-condition-never-an-optimization-target-verify-the-instrument-first.md) | A gate is a stop condition, never an optimization target; verify the instrument first |
| [0013](0013-content-gates-run-at-every-boundary-where-text-can-reach-a-delivered-artifact.md) | Content gates run at every boundary where text can reach a delivered artifact |
| [0014](0014-concurrency-caps-are-measured-floored-and-never-silently-lowered.md) | Concurrency caps are measured, floored, and never silently lowered |
| [0015](0015-resolve-formatting-encoded-semantics-before-diffing-or-linting.md) | Resolve formatting-encoded semantics before diffing or linting |
| [0016](0016-an-edit-changes-only-what-it-must-another-author-s-work-is-never-altered.md) | An edit changes only what it must; another author's work is never altered |
| [0017](0017-outbound-messages-follow-the-project-s-concise-output-style.md) | Outbound messages follow the project's concise output style |
| [0018](0018-a-failing-gate-is-a-defect-to-investigate-expectations-are-re-anchored-never-retuned.md) | A failing gate is a defect to investigate; expectations are re-anchored, never retuned |
| [0019](0019-run-truth-lives-in-one-module-the-exit-code-is-a-pure-function-of-one-verdict.md) | Run truth lives in one module; the exit code is a pure function of one verdict |
| [0020](0020-one-caller-owns-the-model-call-seam-retry-extraction-and-validation-inside-it.md) | One caller owns the model-call seam: retry, extraction, and validation inside it |
| [0021](0021-one-parser-owns-format-knowledge-a-parser-swap-is-proven-behavior-neutral.md) | One parser owns format knowledge; a parser swap is proven behavior-neutral |
| [0022](0022-contract-validators-at-the-model-extraction-seam-not-prose-in-prompts.md) | Contract validators at the model-extraction seam, not prose in prompts |
| [0023](0023-the-approval-ledger-mints-from-every-source-and-re-entry-is-idempotent.md) | The approval ledger mints from every source, and re-entry is idempotent |
| [0024](0024-ready-is-not-authorized-a-consequential-live-write-needs-an-explicit-per-action-grant.md) | Ready is not authorized: a consequential live write needs an explicit, per-action grant |
| [0025](0025-delegate-context-heavy-work-to-subagents-the-main-session-keeps-the-decision.md) | Delegate context-heavy work to subagents; the main session keeps the decision |
| [0026](0026-commits-and-pushes-are-automatic.md) | Commits and pushes are automatic; do not ask |
| [0027](0027-eval-failures-are-fixed-at-the-root-architectural-cause-not-patched-at-the-symptom.md) | An eval failure is fixed at its root architectural cause, never patched at the symptom |
| [0028](0028-the-distinct-category-rule-names-defect-types-finely.md) | The distinct-category rule names defect types finely; authorization, injection, and traversal are separate from security |
| [0029](0029-hard-and-complex-tasks-decompose-into-single-defect-easy-sub-tasks.md) | Hard and complex tasks decompose into single-defect easy sub-tasks; the splitter enforces the split |

## Provenance

Destination 0002..0025 map to humanedge ADRs by number. The destination number differs from the source because destination 0001 already exists.

| Source (humanedge) | Destination | Title |
|---|---|---|
| 0001 | 0002 | Diffs segment by the source's own units and align by content |
| 0002 | 0003 | Nothing is dropped silently: three buckets at the tool/judgment boundary |
| 0003 | 0004 | Verifying a write to a live artifact you cannot fully observe |
| 0004 | 0005 | Designed material is read from its source, never reconstructed |
| 0005 | 0006 | Delivered text is self-contained: state the artifact, never the process |
| 0007 | 0007 | Tool-minted identifiers live in a namespace that cannot collide with project data |
| 0008 | 0008 | One observation contract between the deterministic layer and the model layer |
| 0009 | 0009 | Classifier gates are calibrated blind, anchored, and floored, or they are not evidence |
| 0010 | 0010 | The pipeline drafts; the owner's control is approval, not authorship |
| 0011 | 0011 | If it is hand-launched in a chat session, it is not automated |
| 0012 | 0012 | A gate is a stop condition, never an optimization target; verify the instrument first |
| 0013 | 0013 | Content gates run at every boundary where text can reach a delivered artifact |
| 0014 | 0014 | Concurrency caps are measured, floored, and never silently lowered |
| 0016 | 0015 | Resolve formatting-encoded semantics before diffing or linting |
| 0017 | 0016 | An edit changes only what it must; another author's work is never altered |
| 0018 | 0017 | Outbound messages follow the project's concise output style |
| 0020 | 0018 | A failing gate is a defect to investigate; expectations are re-anchored, never retuned |
| 0021 | 0019 | Run truth lives in one module; the exit code is a pure function of one verdict |
| 0022 | 0020 | One caller owns the model-call seam: retry, extraction, and validation inside it |
| 0023 | 0021 | One parser owns format knowledge; a parser swap is proven behavior-neutral |
| 0024 | 0022 | Contract validators at the model-extraction seam, not prose in prompts |
| 0025 | 0023 | The approval ledger mints from every source, and re-entry is idempotent |
| 0028 | 0024 | Ready is not authorized: a consequential live write needs an explicit, per-action grant |
| 0029 | 0025 | Delegate context-heavy work to subagents; the main session keeps the decision |

Rejected (not installed): humanedge 0006 (Drive connector routing), 0015 (Productive-minutes cap), 0019 (Submitted-at timestamp) — vendor- or template-specific, no general principle.

Out of scope (already adopted): humanedge 0003's ego-browser provisions and 0027 — adopted as standard across projects.

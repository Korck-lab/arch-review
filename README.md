# arch-review — architectural code review eval (verifiers environment)

An environment for the **Prime Intellect Environments Hub**. The model receives a diff with seeded, documented defects. It writes a code review. The score measures defect recall plus precision. Precision penalizes false alarms.

**Why this project exists:** this is the qualifying credential ("completed project") for the Prime Intellect bounty **SWE-Swiss (Full Pipeline) — $3,500**. See `docs/01-bounty-context.md`.

## Status
- [x] Phase 1 — dataset: 6 curated pilot tasks (diffs with seeded defects), codex-adjudicated — see `docs/04-defect-taxonomy.md` and `docs/05-task-format.md`
- [x] Phase 2 — verifiers v1 implementation (`Taskset` + two judges + F1 reward), smoke eval 3/3 green — see `docs/03-verifiers-v1.md`
- [x] Phase 3 — model slate: 2 models × 21 tasks × 3 rollouts = 126 episodes, all completed
- [ ] Phase 4 — `prime env push` (env not yet scaffolded on the hub)
- [ ] Phase 5 — bounty application (draft kept outside this repo)

## Results

Two reviewer models, 21 tasks, 3 rollouts per task per model. 126 episodes, all completed. Means reported.

The 21 tasks split into two populations that are **not comparable to each other**. The 6 curated tasks carry 2–4 seeded defects each in a full diff. The 15 sub-tasks are narrowed slices derived from the curated set, each carrying exactly 1 seeded defect. With one defect available, the same claim count produces far more false alarms, so precision falls. The tables stay separate for that reason.

### Curated tasks (6 tasks, 18 rollouts per model)

| Model | F1 | Recall | Precision | Claims | False alarms |
|---|---|---|---|---|---|
| claude-haiku-4-5 | **0.848** | 0.887 | 0.840 | 4.11 | 0.78 |
| claude-opus-5 | 0.828 | 0.880 | 0.826 | 4.17 | 0.72 |

### Sub-tasks (15 tasks, 45 rollouts per model)

| Model | F1 | Recall | Precision | Claims | False alarms |
|---|---|---|---|---|---|
| claude-opus-5 | **0.556** | 0.956 | 0.453 | 3.33 | 1.76 |
| claude-haiku-4-5 | 0.492 | 0.933 | 0.363 | 4.13 | 2.33 |

**The ranking inverts between the two tables.** Haiku wins on curated, Opus wins on sub-tasks. Pooling the 21 tasks would report 0.634 for Opus against 0.594 for Haiku and hide the split entirely. That inversion is the main reason this environment is worth running: a single pooled number misreports which model reviews better.

Recall is high in both populations (0.88–0.96). Precision is what separates them, and false alarms are what move precision. Haiku produces more claims than Opus on sub-tasks (4.13 vs 3.33) and pays for it (2.33 false alarms vs 1.76).

**Method.** The model reads the diff plus task context and writes a free-form review. A gold-blind claim extractor turns the review into one claim per distinct issue; a matcher maps each claim to the seeded gold (defect, distractor, or false alarm). Recall credits each seeded defect once at its best match status; precision is the share of claims that are not false alarms; F1 is their harmonic mean. An empty review scores recall 0, precision 1.0, F1 0.

**Judge degradation.** The judge validates that every extracted claim quotes the review verbatim. A claim set that fails validation is retried once, then degraded to empty rather than crashing the rollout (ADR-0003). That degradation fired on 1 rollout out of 126 (Opus, sub-tasks). It is counted in the means above, not excluded.

### Reproducibility — what this run does and does not establish

The reviewer and both judges run through `tools/claude_proxy.py`, a dev shim that translates the Anthropic Messages API into a `claude -p` subprocess. **The shim passes only `--model`. It discards `temperature`, `max_tokens` and thinking config.** So the numbers above were not produced at a pinned sampling temperature, and re-running them will not reproduce them byte for byte.

A separate control run tested whether the judge itself is deterministic when temperature is actually honoured. It pointed the judge at a local ollama backend at `temperature=0.0` and replayed one fixed real review of `t001-payment-race`:

- `verifiers` does send the temperature on the wire (`verifiers/v1/judge.py:178`), so the loss is in the shim, not the framework.
- `qwen2.5:7b-instruct` cannot serve as judge here. It emits schema-valid JSON but paraphrases its quotes, so the verbatim validator rejects it on 3 of 3 runs. Its determinism is therefore untested, not disproved.
- `llama3.1:8b` completes the pipeline. The claim extractor produced a byte-identical output on 3 of 3 runs. The matcher produced two distinct outputs across the same 3 runs (F1 0.800, 0.857, 0.857).
- Isolating that matcher divergence failed. Replaying the identical matcher prompt gave byte-identical output across 18+ replays. Adding an explicit seed changed nothing; cold versus warm model load changed nothing; schema-constrained decoding versus free-form decoding were each internally identical; loading a second model to force memory pressure did not reproduce it.

**Honest state: one unexplained matcher divergence stands against 18+ identical controlled replays. End-to-end judge determinism is not established, and this README does not claim it.**

### Excluded from the slate

A third model, `claude-fable-5`, was run and is **excluded**. 49 of its 63 rollouts died on `502 — claude -p failed (1)` with an empty proxy error body. The 11 survivors all fall on `t001-payment-race` and its 3 derived sub-tasks — one task, zero coverage of the other 17. Their mean F1 of 0.691 would outrank both surviving models purely through selection, so it is not published as a comparable result.

## Local run without paid inference (dev)

Point the eval at `claude -p` via the bundled proxy; no API key or spend:

```bash
python tools/claude_proxy.py --port 8788 &      # Anthropic Messages -> claude -p
CLAUDE_LOCAL_KEY=dummy uv run eval arch-review-v1 -n 3 \
  @ <(printf '[client]\nbase_url = "http://127.0.0.1:8788"\napi_key_var = "CLAUDE_LOCAL_KEY"\n\n[env.agent.runtime]\ntype = "subprocess"\n\n[env.taskset.task.judge]\nbase_url = "http://127.0.0.1:8788"\napi_key_var = "CLAUDE_LOCAL_KEY"\n')
```

The judge and reviewer both run on the `claude` CLI's configured model. Use `subprocess` runtime only for local debugging.

## Quick start (machine setup)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # if uv is not installed
uv tool install prime                              # Prime Intellect CLI
prime login                                        # Rafael's account
prime env init arch-review                         # official skeleton
# inside the verifiers workspace:
uv run init arch-review-v1                         # v1 taskset skeleton
uv run eval arch-review-v1                         # run the eval
```

## Repo rules
- Public (it is the showcase). English in code and final README.
- No PII: no real client code — defects seeded into synthetic or permissively licensed OSS (cite the origin).
- Manual curation visible: every task carries an authorship comment explaining its defect (their filter rejects "fully vibecoded" projects).

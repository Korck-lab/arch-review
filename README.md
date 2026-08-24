# arch-review — architectural code review eval (verifiers environment)

An environment for the **Prime Intellect Environments Hub**. The model receives a diff with seeded, documented defects. It writes a code review. The score measures defect recall plus precision. Precision penalizes false alarms.

**Why this project exists:** this is the qualifying credential ("completed project") for the Prime Intellect bounty **SWE-Swiss (Full Pipeline) — $3,500**. See `docs/01-bounty-context.md`.

## Status
- [x] Phase 1 — dataset: 6 curated pilot tasks (diffs with seeded defects), codex-adjudicated — see `docs/04-defect-taxonomy.md` and `docs/05-task-format.md`
- [x] Phase 2 — verifiers v1 implementation (`Taskset` + two judges + F1 reward), smoke eval 3/3 green — see `docs/03-verifiers-v1.md`
- [x] Phase 3 — model slate: 3 models × 21 tasks × 3 rollouts = 189 episodes, all completed
- [x] Phase 4 — published: [korck/arch-review-v1](https://app.primeintellect.ai/dashboard/environments/korck/arch-review-v1) v0.1.4, public, Hub integration test green
- [x] Phase 5 — bounty application submitted 24 Aug 2026 (SWE-Swiss Full Pipeline)

## Results

Three reviewer models, 21 tasks, 3 rollouts per task per model. 189 episodes, all completed. Means reported.

The 21 tasks split into two populations that are **not comparable to each other**. The 6 curated tasks carry 2–4 seeded defects each in a full diff. The 15 sub-tasks are narrowed slices derived from the curated set, each carrying exactly 1 seeded defect. With one defect available, the same claim count produces far more false alarms, so precision falls. The tables stay separate for that reason.

### Curated tasks (6 tasks, 18 rollouts per model)

| Model | F1 | Recall | Precision | Claims | False alarms | Distractor hits |
|---|---|---|---|---|---|---|
| claude-haiku-4-5 | **0.833** | 0.887 | 0.807 | 4.11 | 0.78 | 0.11 |
| claude-fable-5 | 0.793 | 0.894 | 0.743 | 3.94 | 0.33 | 0.78 |
| claude-opus-5 | 0.758 | 0.880 | 0.694 | 4.17 | 0.72 | 0.67 |

### Sub-tasks (15 tasks, 45 rollouts per model)

| Model | F1 | Recall | Precision | Claims | False alarms | Distractor hits |
|---|---|---|---|---|---|---|
| claude-fable-5 | **0.610** | 0.956 | 0.508 | 2.80 | 1.49 | 0.04 |
| claude-opus-5 | 0.526 | 0.956 | 0.427 | 3.33 | 1.76 | 0.29 |
| claude-haiku-4-5 | 0.476 | 0.933 | 0.345 | 4.13 | 2.33 | 0.13 |

**The ranking reorders between the two tables.** Haiku is first on curated and last on sub-tasks. Fable is second on curated and first on sub-tasks. Pooling the 21 tasks would hide the reordering entirely.

**How much of it is established: one gap of three.** The 21 task directories come from only 6 independently authored scenarios — the 15 sub-tasks are slices of those same 6 diffs (ADR-0029), and the 3 rollouts per task measure sampling noise, not new task evidence. A paired bootstrap that resamples the 6 parent scenarios separates one pair, on one population:

| Population | Pair | Gap | 95% CI | Verdict |
|---|---|---|---|---|
| Sub-tasks | fable − haiku | +0.134 | [+0.035, +0.235] | **separated** |
| Sub-tasks | fable − opus | +0.084 | [+0.032, +0.147] | **separated** |
| Sub-tasks | haiku − opus | −0.050 | [−0.134, +0.019] | not separated |
| Curated | haiku − opus | +0.075 | [−0.019, +0.176] | not separated |
| Curated | haiku − fable | +0.040 | [−0.087, +0.176] | not separated |
| Curated | fable − opus | +0.035 | [−0.027, +0.104] | not separated |

Reproduce with `python tools/significance.py <model-a> <model-b> outputs/<run-dir> ...`. Fable's sub-task lead is real at 95%. **Every curated gap is not, and neither is the haiku/opus flip.** Read the reordering as the effect this environment is built to expose, not as a measured ranking. Closing the rest needs independently authored scenarios, not more rollouts on these six.

Recall is high everywhere (0.88–0.96) and barely separates the models. Precision does, and claim volume drives precision. On sub-tasks the three models rank exactly by restraint: fable claims 2.80, opus 3.33, haiku 4.13, and their false alarms follow at 1.49, 1.76, 2.33. The curated tier prices a different skill — distractor discipline. Fable hits 0.78 planted distractors per rollout and opus 0.67, against haiku's 0.11, which is what puts haiku first there despite claiming the most.

**Method.** The model reads the diff plus task context and writes a free-form review. A gold-blind claim extractor turns the review into one claim per distinct issue; a matcher maps each claim to the seeded gold (defect, distractor, or false alarm). Recall credits each seeded defect once at its best match status. Precision is `matched / (claims − duplicates)`: a claim against a planted distractor is working code called a bug, so it costs precision like any other false alarm (ADR-0030). F1 is their harmonic mean. An empty review scores recall 0, precision 1.0, F1 0.

**Scoring formula.** Every trace carries a `scoring_formula` metric naming the rule that scored it. Formula 1 exempted distractor hits from the precision denominator, which made every planted distractor free and left the dataset's precision probe disconnected from the reward. Formula 2 charges for them (ADR-0030).

The opus and haiku runs predate the change and are read through `tools/results_table.py`, which recomputes F1 from the stored metrics under the live formula — exact arithmetic, no new judge call. Curated F1 moved 0.828→0.758 (Opus) and 0.848→0.833 (Haiku); sub-tasks moved 0.556→0.526 and 0.492→0.476. The fable run was scored under formula 2 natively and passes through unchanged.

**Judge degradation.** The judge validates that every extracted claim quotes the review verbatim. A claim set that fails validation is retried once, then degraded to empty rather than crashing the rollout (ADR-0003). That degradation fired on 2 rollouts out of 189 — one Opus, one Fable, both on sub-tasks. Both are counted in the means above, not excluded.

### Reproducibility — what this run does and does not establish

The reviewer and both judges run through `tools/claude_proxy.py`, a dev shim that translates the Anthropic Messages API into a `claude -p` subprocess. **The shim passes only `--model`. It discards `temperature`, `max_tokens` and thinking config.** So the numbers above were not produced at a pinned sampling temperature, and re-running them will not reproduce them byte for byte.

A separate control run tested whether the judge itself is deterministic when temperature is actually honoured. It pointed the judge at a local ollama backend at `temperature=0.0` and replayed one fixed real review of `t001-payment-race`:

- `verifiers` does send the temperature on the wire (`verifiers/v1/judge.py:178`), so the loss is in the shim, not the framework.
- `qwen2.5:7b-instruct` cannot serve as judge here. It emits schema-valid JSON but paraphrases its quotes, so the verbatim validator rejects it on 3 of 3 runs. Its determinism is therefore untested, not disproved.
- `llama3.1:8b` completes the pipeline. The claim extractor produced a byte-identical output on 3 of 3 runs. The matcher produced two distinct outputs across the same 3 runs (F1 0.800, 0.857, 0.857).
- Isolating that matcher divergence failed. Replaying the identical matcher prompt gave byte-identical output across 18+ replays. Adding an explicit seed changed nothing; cold versus warm model load changed nothing; schema-constrained decoding versus free-form decoding were each internally identical; loading a second model to force memory pressure did not reproduce it.

**Honest state: one unexplained matcher divergence stands against 18+ identical controlled replays. End-to-end judge determinism is not established, and this README does not claim it.**

### `claude-fable-5` — previously excluded, now complete

An earlier fable run lost 49 of 63 rollouts to `502 — claude -p failed (1)` with an empty proxy error body. Only `t001-payment-race` and its 3 sub-tasks survived, so that run was published as excluded rather than as a comparable result.

The run above is a fresh full pass: 63 of 63 rollouts scored, all 21 tasks, zero proxy errors, at the same concurrency of 4 as the failed attempt. **The original failure is unexplained.** `claude -p --model claude-fable-5` answers normally today and the dead rollouts carried empty stderr, so nothing points at a cause. It is recorded as an unreproduced transient, not as a diagnosed and fixed defect.

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

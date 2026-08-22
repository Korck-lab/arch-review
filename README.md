# arch-review — architectural code review eval (verifiers environment)

An environment for the **Prime Intellect Environments Hub**. The model receives a diff with seeded, documented defects. It writes a code review. The score measures defect recall plus precision. Precision penalizes false alarms.

**Why this project exists:** this is the qualifying credential ("completed project") for the Prime Intellect bounty **SWE-Swiss (Full Pipeline) — $3,500**. See `docs/01-bounty-context.md`.

## Status
- [x] Phase 1 — dataset: 6 curated pilot tasks (diffs with seeded defects), codex-adjudicated — see `docs/04-defect-taxonomy.md` and `docs/05-task-format.md`
- [x] Phase 2 — verifiers v1 implementation (`Taskset` + two judges + F1 reward), smoke eval 3/3 green — see `docs/03-verifiers-v1.md`
- [~] Phase 3 — local eval, 1 model scored (6/6 episodes); 2–3 model slate pending
- [ ] Phase 4 — `prime env push` (env not yet scaffolded on the hub)
- [ ] Phase 5 — bounty typeform — see `docs/06-typeform.md`

## Results

Reviewer under test: a flash-tier model routed through the local `claude -p` proxy. Three episodes per task, means reported. F1 combines defect recall with precision; false alarms penalize precision.

| Task | F1 | Recall | Precision | Claims | False alarms |
|---|---|---|---|---|---|
| t001-payment-race | 0.62 | 0.83 | 0.50 | 4.0 | 1.7 |
| t002-shop-orders | 0.87 | 1.00 | 0.78 | 3.0 | 0.7 |
| t003-reports-export | 0.71 | 1.00 | 0.56 | 3.7 | 1.7 |
| t004-warehouse-sync | 0.66 | 1.00 | 0.50 | 5.0 | 2.3 |
| t005-notify-queue | 1.00 | 1.00 | 1.00 | 2.7 | 0.0 |
| t006-customer-webhooks | 0.82 | 1.00 | 0.72 | 3.0 | 1.0 |
| **Mean** | **0.78** | **0.97** | **0.68** | **3.6** | **1.2** |

**Method.** The model reads the diff plus task context and writes a free-form review. A gold-blind claim extractor turns the review into one claim per distinct issue; a matcher maps each claim to the seeded gold (defect, distractor, or false alarm). Recall credits each seeded defect once at its best match status; precision is the share of claims that are not false alarms; F1 is their harmonic mean. An empty review scores recall 0, precision 1.0, F1 0.

**Reading.** The reviewer is told to report only high-confidence, diff-supported defects and to consolidate symptoms of one root cause. That keeps it precise: a mean of 1.2 false alarms per task instead of unconstrained listing. Recall stays near perfect (0.97); the one miss is a concurrency defect a rollout judged too theoretical. The eval discriminates — the clean task (t005) scores 1.00, the two-defect race task (t001) the lowest.

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

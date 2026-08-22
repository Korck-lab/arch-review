# arch-review — architectural code review eval (verifiers environment)

An environment for the **Prime Intellect Environments Hub**. The model receives a diff with seeded, documented defects. It writes a code review. The score measures defect recall plus precision. Precision penalizes false alarms.

**Why this project exists:** this is the qualifying credential ("completed project") for the Prime Intellect bounty **SWE-Swiss (Full Pipeline) — $3,500**. See `docs/01-bounty-context.md`.

## Status
- [ ] Phase 1 — dataset: 30 curated tasks (diffs with seeded defects) — see `docs/04-defect-taxonomy.md` and `docs/05-task-format.md`
- [ ] Phase 2 — verifiers v1 implementation (`Taskset` + rewards + judge) — see `docs/03-verifiers-v1.md`
- [ ] Phase 3 — local eval on 2–3 models, README with scores
- [ ] Phase 4 — `prime login` (Rafael) + `prime env push`
- [ ] Phase 5 — bounty typeform — see `docs/06-typeform.md`

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

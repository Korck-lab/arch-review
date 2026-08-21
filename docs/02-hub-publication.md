# Publishing on the Environments Hub

## Flow (source: PrimeIntellect-ai/prime README)
```bash
uv tool install prime
prime login                    # Rafael's Prime Intellect account (created 09/Aug/2026)
prime env init arch-review
prime env push arch-review
```
- `prime env list` shows the hub's verified environments (good for studying competition/style).
- `prime lab setup` creates a local verifiers workspace (evals, GEPA, Hosted Training) — useful but not required to publish.

## Costs
- Running the eval locally uses the inference API (own key; a few dollars on a cheap model for a smoke test, plus one run on the 30 tasks with 2–3 models for the README).
- Publishing on the Hub is free.

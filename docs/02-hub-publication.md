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
- Running the eval uses the inference API (own key). The reported slate is 21 tasks × 3 episodes × 3 reviewer models, with the two judge calls per episode dominating the cost.
- Publishing on the Hub is free.

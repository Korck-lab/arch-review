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

## What the first real publication taught (24 Aug 2026)

**Visibility does not come from the CLI.** `prime env push --visibility PUBLIC` is accepted and then ignored. Set it on the web: environment page → Settings → Visibility → radio "Public". It applies at once, with no save button.

**The Hub CI requires `tags`.** The integration test `test_pyproject_has_metadata` demands `name`, `version`, `description` and `tags` under `[project]`. A missing `tags` key failed version `0.1.1`; commit `15bb085` fixed it.

**Republishing is cheap.** `prime env push --auto-bump` raises the patch version on each push. It does not reset the visibility, so a public environment stays public across pushes.

## Costs
- Running the eval uses the inference API (own key). The reported slate is 21 tasks × 3 episodes × 3 reviewer models, with the two judge calls per episode dominating the cost.
- Publishing on the Hub is free.
- The Prime account has no credit today, on both the personal and the Korck team accounts. Prime paid inference is therefore not available. The reported slate ran through `tools/claude_proxy.py` instead.

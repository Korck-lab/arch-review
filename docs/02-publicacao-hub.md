# Publicação no Environments Hub

## Fluxo (fonte: README do PrimeIntellect-ai/prime)
```bash
uv tool install prime
prime login                    # conta Prime Intellect do Rafael (criada 09/ago/2026)
prime env init arch-review
prime env push arch-review
```
- `prime env list` mostra os environments verificados do hub (bom para estudar concorrência/estilo).
- `prime lab setup` cria workspace local verifiers (evals, GEPA, Hosted Training) — útil mas não obrigatório para publicar.

## Custos
- Rodar o eval local usa API de inferência (chave própria; alguns dólares em modelo barato para smoke test, mais um run nos 30 tasks com 2–3 modelos para o README).
- Publicar no Hub é grátis.

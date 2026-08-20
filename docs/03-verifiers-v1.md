# verifiers v1 — o contrato (fonte: AGENTS.md + skill create-environments do repo oficial)

Repo: https://github.com/PrimeIntellect-ai/verifiers (docs/ + skills/ são as fontes; v0 `import verifiers as vf` está DEPRECATED — usar `verifiers.v1`).

## Regras principais
- SEMPRE começar pelo scaffold: `uv run init arch-review-v1` (opções `-T` toolset, `-H` harness custom — provavelmente desnecessários aqui).
- Rodar com `uv run`, nunca `python` direto.
- Um pacote exporta UMA subclasse `vf.Taskset` via `__all__` (opcional: `Env` p/ multi-agente, `Harness` custom). NÃO criar `load_environment()`/`load_taskset()`.
- Não sobrescrever `Taskset.__init__` (implementar `load()`); não sobrescrever `Harness.__init__` (usar `setup()`).
- Preferir harnesses prontos a tools custom. Judge multi-run já existe: `--env.id agentic-judge`.
- Taskset básico = poucas dezenas de linhas: classes tipadas de data/task/config, `load()`, rewards decorados.

## Esqueleto mínimo (adaptado do exemplo oficial)
```python
import verifiers.v1 as vf

class ReviewData(vf.TaskData):
    seeded_defects: list[dict]   # [{id, category, file, line_hint, description}]
    diff: str

class ReviewTask(vf.Task[ReviewData]):
    @vf.reward
    async def defect_recall(self, trace: vf.Trace) -> float:
        ...  # % dos defeitos semeados citados no review (matching via judge)

    @vf.reward
    async def precision(self, trace: vf.Trace) -> float:
        ...  # penaliza issues inventadas (falso alarme)

class ArchReviewTaskset(vf.Taskset[ReviewTask, vf.TasksetConfig]):
    def load(self) -> list[ReviewTask]:
        ...  # carrega tasks/ do disco

__all__ = ["ArchReviewTaskset"]
```

## Antes de implementar, decidir (checklist da skill oficial)
- Campos do dataset; necessidade de tools (aqui: nenhuma — single-turn review);
- controle de fluxo (single-turn; sem user simulado);
- rewards (recall + precision) e métricas extras (por categoria de defeito);
- judge: sim — matching semântico entre issue apontada e defeito semeado (LLM judge com rubrica).

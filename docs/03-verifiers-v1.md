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
    async def f1(self, trace: vf.Trace) -> float:
        ...  # harmônica de recall e precision; matching via judge (extrator + matcher)

    @vf.metric
    async def recall(self, trace: vf.Trace) -> float:
        ...  # defeitos semeados citados / defeitos semeados

    @vf.metric
    async def precision(self, trace: vf.Trace) -> float:
        ...  # issues verdadeiras / issues apontadas (distractor isenta)

class ArchReviewTaskset(vf.Taskset[ReviewTask, vf.TasksetConfig]):
    def load(self) -> list[ReviewTask]:
        ...  # carrega tasks/ do disco

__all__ = ["ArchReviewTaskset"]
```

> **Corrigido (issue #8):** `verifiers.v1` soma rewards nomeados — `Trace.reward = sum(r.value for r in self.rewards.values())`. Dois `@vf.reward` (recall + precision) somariam recall+precision, não F1. Por isso o reward é um único `f1`; recall, precision e métricas por categoria viram `@vf.metric`.

## Antes de implementar, decidir (checklist da skill oficial)
- Campos do dataset; necessidade de tools (aqui: nenhuma — single-turn review);
- controle de fluxo (single-turn; sem user simulado);
- rewards (um F1 como reward único; recall, precision e por-categoria como metrics);
- judge: sim — matching semântico entre issue apontada e defeito semeado (LLM judge com rubrica).

# arch-review — eval de code review arquitetural (verifiers environment)

Environment para o **Environments Hub da Prime Intellect**: o modelo recebe um diff/trecho de código com **defeitos semeados e documentados** e deve produzir um code review; a pontuação mede recall dos defeitos + precisão (penaliza falso alarme).

**Por que este projeto existe:** é a credencial de qualificação ("completed project") para aplicar ao bounty **SWE-Swiss (Full Pipeline) — $3.500** da Prime Intellect. Ver `docs/01-contexto-bounty.md`.

## Estado
- [ ] Fase 1 — dataset: 30 tarefas curadas (diffs com defeitos semeados) — ver `docs/04-taxonomia-defeitos.md` e `docs/05-formato-task.md`
- [ ] Fase 2 — implementação verifiers v1 (`Taskset` + rewards + judge) — ver `docs/03-verifiers-v1.md`
- [ ] Fase 3 — eval local em 2–3 modelos, README com scores
- [ ] Fase 4 — `prime login` (Rafael) + `prime env push`
- [ ] Fase 5 — typeform do bounty — ver `docs/06-typeform.md`

## Quick start (setup da máquina)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # se uv não instalado
uv tool install prime                              # CLI da Prime Intellect
prime login                                        # conta do Rafael
prime env init arch-review                         # esqueleto oficial
# dentro do workspace verifiers:
uv run init arch-review-v1                         # esqueleto do taskset v1
uv run eval arch-review-v1                         # rodar o eval
```

## Regras do repo
- Público (é a vitrine). Inglês em código e README final.
- Nada de PII: nenhum código de cliente real — defeitos semeados em código sintético ou OSS com licença permissiva (citar origem).
- Curadoria manual visível: cada task com comentário de autoria explicando o defeito (o filtro deles descarta projeto "fully vibecoded").

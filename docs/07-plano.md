# Plano de execução (estimativa 1–2 dias úteis)

## Fase 1 — Dataset (o grosso do valor; ~meio dia+)
- [ ] Escrever 6 tasks piloto (1 por categoria principal), com gold.yaml completo
- [ ] Validar formato rodando 1 modelo à mão (sem verifiers ainda)
- [ ] Completar 30 tasks (balancear categoria × dificuldade)

## Fase 2 — Environment (~2-3h com scaffold)
- [ ] `uv run init arch-review-v1`, implementar ReviewData/ReviewTask/Taskset
- [ ] Judge com rubrica p/ matching; rewards recall + precision
- [ ] `uv run eval` smoke test com 3 tasks

## Fase 3 — Resultados (~2h + custo API)
- [ ] Eval completo em 2–3 modelos (1 forte, 1 médio, 1 barato)
- [ ] README final em inglês: metodologia, tabela de scores, análise por categoria

## Fase 4 — Publicar
- [ ] Repo público no GitHub (conta a confirmar)
- [ ] `prime login` (Rafael) + `prime env push`

## Fase 5 — Aplicar
- [ ] Preencher typeform (docs/06), revisão do Rafael, envio com ok dele

## Riscos
- SWE-Swiss ser atribuído a outro durante a construção → planos B na mesma credencial
- Judge instável no matching → fixar rubrica + exemplos few-shot no prompt do judge; medir concordância em 5 tasks à mão
- Datas na planilha indicam ciclo de revisão lento deles — aplicar assim que publicar, não esperar polish infinito

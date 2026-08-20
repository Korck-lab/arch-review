# Taxonomia de defeitos semeados (curadoria manual — a alma do projeto)

Cada task semeia 1–4 defeitos de categorias distintas. Meta: 30 tasks, cobertura balanceada, dificuldade crescente. Cada defeito tem gabarito com justificativa escrita à mão (isso é o anti-"vibecoded").

## Categorias (do repertório CTO/due-diligence do Rafael)
1. **Concorrência**: race condition, deadlock, check-then-act, estado compartilhado sem lock
2. **Dados**: N+1 query, migração destrutiva sem rollback, transação ausente, índice faltante em query quente
3. **Contratos**: quebra de compatibilidade de API pública, mudança de semântica sem versionamento, erro silencioso engolido
4. **Segurança**: segredo hardcoded, SQL injection, path traversal, log de PII, authz ausente em endpoint novo
5. **Resiliência**: retry sem backoff/idempotência, timeout ausente, fallback que mascara falha, cache sem invalidação
6. **Arquitetura**: dependência circular introduzida, camada furada (UI→DB direto), acoplamento a detalhe de vendor, god object crescendo
7. **Operabilidade**: métrica/log removido de caminho crítico, feature flag sem kill switch, config em código

## Anti-padrões do dataset (evitar)
- Defeito detectável por linter trivial (aí não mede julgamento arquitetural)
- Diff gigante (manter 50–300 linhas; o sinal é densidade, não volume)
- Ambiguidade não intencional: cada defeito semeado deve ser defensável como bug real em code review humano

## Distratores
- Cada task inclui código correto que PARECE suspeito (para medir precisão/falso alarme) — documentar no gabarito por que está ok.

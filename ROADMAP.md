# ROADMAP — Morpho Risk Tooling

Fases em alto nível, extraídas de `docs/validation-plan-v2.md`. Princípio: **validação antes do build** — zero código de produção até o veredito.

## Fase 0 — Gate Zero: pré-registro (Dia 0, antes de qualquer dado)

- Preencher e commitar `docs/validation-preregistration.md` com limiares travados (FORTE/MÉDIO/FRACO, ABERTO/CONTESTADO/FECHADO, TEM/FINA/SEM) e a regra de decisão congelada.
- Commit separado e rotulado, pushado ao remote, ancorado externamente (OpenTimestamps e/ou hash postado publicamente).
- **Bloqueia tudo que toca dados de liquidação.**

## Fase 1 — Teste 1: reconstrução dos eventos de estresse (Semana 1–2)

- Reconstruir 5–10 liquidações em **dois regimes**: fev/2026 (evento primário) e out/2025 (out-of-sample).
- Três camadas de medição: janela teórica (upper bound), **janela realizada point-in-time** (sem look-ahead), atribuição **capacidade vs. consciência** → teto de mercado endereçável.
- Risco antecipado: preço de oráculo no bloco histórico por market (pode exigir nó arquival).
- Trabalho paralelo seguro: scaffold, enquadramento regulatório, dados via Dune + subgraph (sem indexer próprio).
- Entregável: reconstruções + **peça de pesquisa publicada** + health checker mínimo (se o tempo apertar, a pesquisa vem primeiro).

## Fase 2 — Testes 2 e 3: espaço e rampa (Semana 2–4)

- **Teste 2 (Espaço):** conversas com Morpho (estratégia oficial de risk tooling vs. Hypernative) e com ≥1 integrador (build-vs-buy; pedir dado de alert-delivery).
- **Teste 3 (Rampa):** inventário de 20 contatos em integradores Morpho, por grau e função; classificar TEM/FINA/SEM.

## Fase 3 — Veredito GO/NO-GO (Semana 4)

- Síntese pela matriz de decisão (Espaço × Sinal, Rampa modula execução).
- Sinal FRACO em qualquer cenário → pivô de tese (ação automática ou Wedge A); não buildar o aviso.

## Pós-GO (somente após veredito positivo)

- Modelo estrutural (Black-Cox/Merton, point-in-time) no `quant/`.
- Indexer próprio (se a pesquisa justificar), API B2B (mês 4–5), aprofundamento MiCA (mês 3–4).
- Auditoria real de modelo/código.

# Seed de Issues & Milestones

> Fonte para `scripts/seed-issues.sh`. **Não** criar nada ao vivo antes do push do repo — rodar o script só após `git push` + `gh auth login` (GUARDRAIL 6).

## Milestone: Gate Zero (pré-registro)

- **Preencher thresholds do § 4 do pré-registro** — decisão humana dos limiares FORTE/MÉDIO/FRACO, ABERTO/CONTESTADO/FECHADO, TEM/FINA/SEM, antes de qualquer dado.
- **Commit + push separado e rotulado do pré-registro** — usar a mensagem de commit do CONTRIBUTING.md; nenhum outro arquivo no commit.
- **Ancorar o pré-registro externamente** — OpenTimestamps no arquivo e/ou hash do commit postado publicamente (fórum Morpho / X).

## Milestone: Test 1 — Reconstrução (fev+out)

- **Resolver fonte de preço de oráculo histórico por bloco** — nó arquival vs. feed do provedor; risco nº 1 de cronograma (§ 3.3 do plano).
- **Reconstruir 5–10 liquidações de fev/2026 (3 camadas)** — janela teórica, janela realizada point-in-time, atribuição capacidade vs. consciência.
- **Checagem out-of-sample em out/2025** — repetir a reconstrução no flash crash; comparar estabilidade entre regimes.
- **Redigir e publicar a peça de pesquisa** — fórum Morpho + X + Dune, referenciando o hash do commit do pré-registro.

## Milestone: Test 2 — Posicionamento (Morpho+integrador)

- **Conversa com Morpho (fórum/BD)** — estratégia oficial de risk tooling retail/integrador-facing e posição vs. Hypernative.
- **Call com ≥1 integrador (warm intro)** — build-vs-buy de terceiro neutro; o que faltou em fevereiro.
- **Pedir dado de alert-delivery ao integrador** — refina o teto endereçável removendo "viu e declinou".

## Milestone: Test 3 — Rampa

- **Inventariar 20 contatos em integradores Morpho** — por grau (direto/2º/zero) e por função (risco/lending/eng).
- **Classificar a rampa (TEM/FINA/SEM)** — contra os limiares pré-registrados.

## Milestone: Semana 4 — Veredito

- **Consolidar os 3 sinais contra a matriz de decisão** — Sinal × Espaço, Rampa modulando execução.
- **Registrar o veredito GO/NO-GO/Pivô** — documento curto com expectativa (§ 1 do pré-registro) vs. observado.

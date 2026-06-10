# Morpho Risk Tooling

Tooling de risco **neutro e informacional** sobre o protocolo [Morpho](https://morpho.org), focado no Wedge B: **alerta antecipado de liquidação para o tomador/integrador**. O projeto está em fase de **validação pré-build** — zero código de produção até os três testes (Sinal, Espaço, Rampa) retornarem o veredito GO/NO-GO. Ver `docs/validation-plan-v2.md`.

## Stack

- **TypeScript** (`packages/ingestion/`) — ingestão/dados. Licença **MIT**.
- **Python 3.11** (`quant/`) — modelo quant. Licença **BUSL-1.1**. Gerenciado com [uv](https://docs.astral.sh/uv/).
- **Dune** (`dune/`) — queries de dados públicos. Licença **MIT**.
- Chains do MVP: **Ethereum + Base** apenas.

Ver `LICENSING.md` para o split de licenças por diretório.

## ⚠️ Regra de ordem do pré-registro (bloqueante)

> **O commit de `docs/validation-preregistration.md` com os limiares (§ 4) preenchidos DEVE existir no remote ANTES de qualquer query em `dune/queries/` ganhar conteúdo.**

Depois de ver os dados de liquidação, pré-registrar limiares é logicamente impossível. Por isso a regra é **código, não convenção**: o job `preregistration-gate` no CI falha se houver `.sql` não-vazio em `dune/queries/` enquanto a tabela de limiares (§ 4 do pré-registro) ainda contiver `[___]`. Detalhes e template de commit em `CONTRIBUTING.md`.

## Estrutura

| Caminho | O que é |
|---|---|
| `docs/validation-preregistration.md` | Pré-registro de limiares (Gate Zero) — preenchido por humano, antes de dados |
| `docs/validation-plan-v2.md` | Plano de validação completo (3 testes + matriz GO/NO-GO) |
| `docs/regulatory-framing.md` | Enquadramento regulatório (informacional, sem execução) |
| `packages/ingestion/` | Esqueleto TypeScript de ingestão (MIT) |
| `quant/` | Esqueleto Python do modelo de risco — apenas schema, sem lógica (BUSL-1.1) |
| `dune/queries/` | Vazia de propósito até o pré-registro estar commitado |
| `ROADMAP.md` | Fases em alto nível |

## Status

Dia 1 — scaffold. Nenhum dado de liquidação foi inspecionado.

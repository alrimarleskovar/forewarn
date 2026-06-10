# Validation Pre-Registration — Morpho Risk Tooling (Wedge B)

> **REGRA DE OURO:** este arquivo é preenchido e commitado **antes de qualquer dado de liquidação ser visualizado**. Depois de ver os dados, pré-registrar é logicamente impossível. Não preencha nenhum número desta página com base em dados já observados.

---

## 0. Atestado de pré-registro

- **Autor(es):** `[ALRIMAR]`
- **Data/hora do commit:** `[2026-06-10 01:50 TZ]`
- **Commit hash:** `[preenchido pelo git]`
- **Atesto que nenhum dado de liquidação de fev/2026 ou out/2025 foi inspecionado antes deste commit:** `[x] SIM`

---

## 1. Hipótese sob teste

> Um modelo de risco neutro voltado ao tomador/integrador entrega aviso de liquidação útil e acionável com mais antecedência (ou melhor conversão em ação) do que as soluções atuais.

- **Predição direcional (preencher antes dos dados — compara-se esperado vs. observado nos 3 eixos):**
  - **Sinal esperado:** teto endereçável ~`[50]%`, janela realizada mediana ~`[1-2h]`.
  - **Espaço esperado:** `[ CONTESTADO  ]` — racional: `[ incumbente oficial (Hypernative) existe, mas há brecha no neutro/borrower-facing]`.
  - **Rampa esperada:** `[ TEM / FINA / SEM ]` — contatos warm/2º grau atualmente conhecidos: `[___]`.

  *(Registrar a expectativa nos 3 eixos força honestidade na leitura depois — não só no Sinal.)*

---

## 2. Definições de métrica (congeladas)

**2.1 Janela realizada point-in-time** — tempo entre o primeiro instante em que um modelo *walk-forward* (usando só dados conhecíveis naquele timestamp) teria emitido alerta de risco e o instante da execução da liquidação. **Sem look-ahead bias.**

**2.2 Janela teórica (upper bound)** — idem, mas com visibilidade pós-fato. Usada só como teto, **não** como claim de venda.

**2.3 Capacidade de curar (observável on-chain)** — dentro da janela realizada, a posição tinha **gas suficiente** `E` **colateral/fundos acessíveis** para adicionar/repagar e restaurar a saúde? `(sim/não)`

**2.4 Teto de mercado endereçável** — fração das liquidações com **capacidade = sim** que foram liquidadas mesmo assim. É o limite superior do que um produto de aviso poderia ter evitado.

**2.5 Consciência/vontade (não-observável on-chain)** — só refinável com dado de alert-delivery do integrador (Teste 2). **Não** entra no número on-chain; registrado como pendência.

---

## 3. Dados e escopo (congelados)

- **Evento primário:** fev/2026.
- **Evento out-of-sample:** out/2025.
- **Nº de liquidações reconstruídas por evento:** `[5–10]`
- **Critério de seleção das liquidações:** `[ex.: maiores por valor / amostra aleatória estratificada por colateral — DEFINIR]`
- **Fontes:** Dune + Etherscan + subgraph Morpho + GraphQL oficial; **preço de oráculo histórico por bloco via** `[nó arquival / feed — DEFINIR]`.
- **Chains no escopo:** Ethereum, Base.

---

## 4. Limiares pré-comprometidos

> Defaults de referência abaixo. **Confirmar ou ajustar deliberadamente ANTES de ver dados.** Marcar cada um como confirmado.

### 4.1 Sinal (Teste 1)
| Classe | Critério (default a confirmar) | Confirmado? |
|---|---|---|
| **FORTE** | janela realizada mediana **≥ 2h** `E/OU` teto endereçável **≥ 40%**, **estável nos dois regimes** | `[x]` valor final: `[___]` |
| **MÉDIO** | janela **1–2h** `OU` sinal instável entre regimes / atribuição mista | `[x]` valor final janela: `[___]` |
| **FRACO** | janela **< 1h** `E` teto endereçável **< `[25]%`** | `[x]` valor final janela: `[___]` / teto: `[___]` |

**Definição de "estável entre regimes":** a classe não muda entre fev/2026 e out/2025; divergência rebaixa para MÉDIO no máximo. `[ ]` confirmado

### 4.2 Espaço (Teste 2)
| Classe | Critério (default a confirmar) | Confirmado? |
|---|---|---|
| **ABERTO** | ≥1 sinal explícito (Morpho ou integrador) de que terceiro neutro tem lugar | `[x ]` |
| **CONTESTADO** | Hypernative provavelmente estende `OU` integrador sinaliza preferência por build in-house | `[x ]` |
| **FECHADO** | parceiro oficial cobrirá `E` integradores construindo internamente | `[x ]` |

### 4.3 Rampa (Teste 3)
| Classe | Critério (default a confirmar) | Confirmado? |
|---|---|---|
| **TEM** | **≥ 3** contatos warm/2º grau nas funções certas | `[x]` valor final: `[]` |
| **FINA** | 1–2 | `[x ]` |
| **SEM** | 0–1 | `[x ]` |

---


ALRIMAR SOBRINHO 10-06-2026


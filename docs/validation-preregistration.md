# Validation Pre-Registration — Morpho Risk Tooling (Wedge B)

> **REGRA DE OURO:** este arquivo é preenchido e commitado **antes de qualquer dado de liquidação ser visualizado**. Depois de ver os dados, pré-registrar é logicamente impossível. Não preencha nenhum número desta página com base em dados já observados.

---

## 0. Atestado de pré-registro

- **Autor(es):** `[NOME]`
- **Data/hora do commit:** `[YYYY-MM-DD HH:MM TZ]`
- **Commit hash:** `[preenchido pelo git]`
- **Atesto que nenhum dado de liquidação de fev/2026 ou out/2025 foi inspecionado antes deste commit:** `[ ] SIM`

---

## 1. Hipótese sob teste

> Um modelo de risco neutro voltado ao tomador/integrador entrega aviso de liquidação útil e acionável com mais antecedência (ou melhor conversão em ação) do que as soluções atuais.

- **Predição direcional (preencher antes dos dados — compara-se esperado vs. observado nos 3 eixos):**
  - **Sinal esperado:** teto endereçável ~`[___]%`, janela realizada mediana ~`[___]`.
  - **Espaço esperado:** `[ ABERTO / CONTESTADO / FECHADO ]` — racional: `[___]`.
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
| **FORTE** | janela realizada mediana **≥ 2h** `E/OU` teto endereçável **≥ 40%**, **estável nos dois regimes** | `[ ]` valor final: `[___]` |
| **MÉDIO** | janela **1–2h** `OU` sinal instável entre regimes / atribuição mista | `[ ]` valor final janela: `[___]` |
| **FRACO** | janela **< 1h** `E` teto endereçável **< `[___]%`** | `[ ]` valor final janela: `[___]` / teto: `[___]` |

**Definição de "estável entre regimes":** a classe não muda entre fev/2026 e out/2025; divergência rebaixa para MÉDIO no máximo. `[ ]` confirmado

### 4.2 Espaço (Teste 2)
| Classe | Critério (default a confirmar) | Confirmado? |
|---|---|---|
| **ABERTO** | ≥1 sinal explícito (Morpho ou integrador) de que terceiro neutro tem lugar | `[ ]` |
| **CONTESTADO** | Hypernative provavelmente estende `OU` integrador sinaliza preferência por build in-house | `[ ]` |
| **FECHADO** | parceiro oficial cobrirá `E` integradores construindo internamente | `[ ]` |

### 4.3 Rampa (Teste 3)
| Classe | Critério (default a confirmar) | Confirmado? |
|---|---|---|
| **TEM** | **≥ 3** contatos warm/2º grau nas funções certas | `[ ]` valor final: `[___]` |
| **FINA** | 1–2 | `[ ]` |
| **SEM** | 0–1 | `[ ]` |

---

## 5. Regra de decisão (congelada)

| Espaço | Veredito (Sinal FORTE/MÉDIO) | Papel da Rampa |
|---|---|---|
| ABERTO | **GO pleno** | TEM/FINA → outbound+inbound · SEM → inbound-led |
| CONTESTADO | **GO acelerado c/ cláusula de obsolescência** (+ plano de defensibilidade) | TEM/FINA → outbound-led · SEM → inbound-led |
| FECHADO | **NO-GO no formato atual** | — |

**Sinal FRACO (qualquer Espaço/Rampa):** **Pivô** — avaliar produto de ação automática (mais regulado) ou Wedge A. Não buildar o aviso.

- **Acordo da equipe de seguir esta regra mesmo se o resultado for inconveniente:** `[ ] SIM`

---

## 6. Cláusula de alteração de limiar

Qualquer ajuste de limiar **após** ver dados exige, neste arquivo:
- **Data do ajuste:** `[___]`
- **Limiar antigo → novo:** `[___]`
- **Motivo explícito (não "o resultado ficaria melhor"):** `[___]`
- **Reset de expectativa registrado:** `[ ]`
- **Aprovado por:** `[___]`

> Log de alterações (append-only):
> - `[nenhuma até o momento]`

---

## 7. Pendências que dependem de dados externos (não bloqueiam o veredito on-chain)

- [ ] Dado de alert-delivery do integrador → refina teto endereçável removendo "viu e declinou".
- [ ] Confirmar granularidade do preço de oráculo histórico na fonte escolhida.

---

## 8. Assinaturas

- `[NOME]` — `[DATA]`
- `[NOME]` — `[DATA]`

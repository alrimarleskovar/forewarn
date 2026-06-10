# Morpho Risk Tooling — Plano de Validação Pré-Build & Veredito de GO/NO-GO (v2 — FINAL)

**Status:** versão consolidada para execução. Substitui a v1.
**Data:** 09 de junho de 2026
**Wedge primário:** B — alerta antecipado de liquidação do *borrower*
**Princípio:** zero código de produção até os 3 testes retornarem. Validação antes do build.

**Mudanças nesta versão (v2):**
1. Atribuição reescrita como **capacidade (on-chain) vs. consciência (não-observável)** + teto de mercado endereçável.
2. **Pré-registro de limiares** como gate obrigatório, antes de qualquer dado.
3. Coluna **CONTESTADO** refeita (GO acelerado com cláusula de obsolescência) + **checagem out-of-sample** (out/2025) para tirar o veredito de cima de um único evento.

> ⚠️ Não é aconselhamento jurídico nem financeiro. Confirmar regulação com advogado de cripto na UE antes de monetizar/constituir empresa.

---

## 1. A tese e a pergunta que o GO responde

> *Um modelo de risco neutro e voltado ao tomador/integrador entrega aviso de liquidação útil e acionável com mais antecedência (ou melhor conversão em ação) do que as soluções atuais — e há comprador disposto a pagar por isso.*

O GO cruza **três sinais**; um forte não ressuscita outro morto:

1. **Sinal** — o produto resolve dor real? (Teste 1)
2. **Espaço** — o incumbente fecha o mercado? (Teste 2)
3. **Rampa** — existe caminho de venda? (Teste 3)

---

## 2. GATE ZERO — Pré-registro (antes de qualquer dado) *(delta 2)*

**Antes de o Teste 1 começar e antes de qualquer dado de liquidação tocar os olhos de alguém**, escrever e commitar `validation-preregistration.md` (esqueleto fornecido em anexo) com:

- os limiares numéricos de FORTE/MÉDIO/FRACO, ABERTO/CONTESTADO/FECHADO, TEM/FINA/SEM **travados**;
- a regra de decisão (matriz da seção 6) congelada.

Ajuste de limiar após ver dados é permitido **somente** com motivo explícito documentado no próprio arquivo + reset de expectativa. Sem isso, FRACO vira "talvez MÉDIO" quando inconveniente.

> Esta é a única dependência de ordem *lógica* do plano: depois de ver os dados, pré-registrar é impossível por definição.

---

## 3. Teste 1 — Reconstrução dos eventos de estresse *(deltas 1 e 3)*

**Por quê:** a credibilidade depende de provar valor sobre as soluções atuais. O erro a evitar é medir só a janela de aviso e/ou apoiar tudo num único evento.

**Prazo:** 1–2 semanas. Custo: trivial, sem código de produção.

### 3.1 As três camadas de medição

1. **Janela teórica (upper bound).** 5–10 liquidações reais via Dune + Etherscan + APIs públicas; janela máxima de aviso com visibilidade pós-fato. *Teto, não claim de venda.*
2. **Janela realizada point-in-time (o número vendável).** Reconstrução *walk-forward*: a cada timestamp, usando só o que era conhecível naquele instante. Sem look-ahead bias. **É este número que vai para a pesquisa e o pitch.**
3. **Atribuição — capacidade vs. consciência** *(delta 1)*:
   - **Capacidade de curar (observável on-chain):** dentro da janela realizada, a wallet tinha **gas suficiente** *e* **colateral/fundos acessíveis** para adicionar/repagar?
     - **Tinha capacidade e foi liquidada mesmo assim** → entra no **teto de mercado endereçável**.
     - **Não tinha capacidade** → **não endereçável por aviso nenhum** (precisava de auto-ação ou parâmetros/LTV diferentes).
   - **Consciência/vontade (NÃO observável on-chain):** entre os que tinham capacidade, quem *não viu* o alerta vs. *viu e não agiu* só se separa com **dado de alert-delivery do integrador** → vira pedido natural na call de discovery do Teste 2.

**Número honesto que sai do Teste 1:** *fração dos liquidados que tinha capacidade física de curar dentro da janela e foi liquidada mesmo assim* = **teto do mercado endereçável** por um produto de aviso. O dado do integrador depois refina esse teto para baixo (removendo "viu e declinou").

### 3.2 Checagem out-of-sample *(delta 3)*

Não decidir sobre n=1. Reconstruir **dois regimes**:
- **fev/2026** (crash forte mas ordenado; liquidação funcionou "dentro dos parâmetros") — evento primário.
- **out/2025** (flash crash) — checagem out-of-sample da descoberta de capacidade/janela.

Se o achado se segura nos dois → GO robusto. Se diverge → você aprendeu algo crítico por custo trivial (e o veredito muda).

### 3.3 Risco de execução a antecipar

Reconstruir a saúde minuto a minuto exige **preço do oráculo no bloco histórico**, por market (Morpho é permissionless: cada market define seu oráculo). Dune pode não dar essa granularidade — prever nó arquival ou feed histórico do provedor. **Item mais provável de transformar "1 semana" em "2".**

### 3.4 Saída → classificação de **Sinal**

(limiares exatos travados no pré-registro)
- **FORTE** — janela realizada point-in-time mediana **≥ limiar_alto** *e/ou* teto endereçável **≥ fração_alta**, **mantendo-se nos dois regimes**.
- **MÉDIO** — janela na faixa intermediária **ou** sinal existe mas instável entre regimes/atribuição mista.
- **FRACO** — janela **< limiar_baixo** *e* teto endereçável pequeno. → produto de *aviso* é marginal (ver matriz, seção 6).

---

## 4. Teste 2 — Posição da Morpho **e** do integrador

**Por quê:** Hypernative é parceiro oficial da Morpho desde jul/2025 — mas duas premissas a corrigir:

- **A Morpho não é o portão do mercado.** É minimalista e permissionless; aval dela vale para amplificação/parceria, não para acesso. "Hypernative vai estender" é flag amarela, não sentença — independência frente ao parceiro oficial pode ser argumento de venda.
- **O incumbente real do Wedge B é o integrador.** Você vende a Coinbase/Binance/Société Générale/etc., e a Coinbase **já construiu** o aviso de 30 min. O risco central é **build-vs-buy no comprador**.

**Duas conversas:**
1. **Morpho (fórum/BD):** "Estratégia oficial para risk tooling retail/integrador-facing, e onde isso senta vs. Hypernative?"
2. **Um integrador (warm intro):** "Construiriam in-house ou comprariam de um terceiro neutro? O que faltou em fevereiro?" + **pedir o dado de alert-delivery** (alimenta a camada 3.1 do Teste 1).

**Como conseguir as calls:** warm intro via portfolio Paradigm/a16z, ex-contributors da Morpho no LinkedIn, e principalmente **a peça de pesquisa do Teste 1 puxando-os** (ver sequência, seção 5).

**Saída → classificação de Espaço:**
- **ABERTO** — Morpho sinaliza neutralidade desejável **e/ou** integrador demonstra interesse em terceiro neutro.
- **CONTESTADO** — Hypernative provavelmente estende **ou** integradores tendem a construir in-house.
- **FECHADO** — parceiro oficial cobrirá **e** integradores construindo internamente.

---

## 5. Teste 3 — Rampa de warm intros

**Por quê:** venda B2B a integradores. Cold ~5–10% (heurística); warm ~40–60%. Saber se a porta existe.

**Como:** inventariar 20 contatos em integradores Morpho, por grau (direto / 2º grau / zero) **e por função** (dono de produto de risco/lending ou líder de eng — intro para função errada vale quase nada).

**Saída → classificação de Rampa:**
- **TEM** — ≥ 3 warm/2º grau nas funções certas.
- **FINA** — 1–2.
- **SEM** — 0–1 → liderar por ferramenta pública + inbound, não outbound (não é fatal).

---

## 6. Sequenciamento — GATE ZERO → 1 → (2 e 3)

```
Antes de tudo: GATE ZERO — escreve validation-preregistration.md (limiares travados)
                      │
Semana 1–2:  TESTE 1 (reconstrução fev + out, 3 camadas)  +  trabalho paralelo seguro (seção 7)
                      │  publica a peça de pesquisa
                      ▼
Semana 2–4:  TESTE 2 (Morpho + integrador, com pedido de alert-delivery)  +  TESTE 3 (rampa)
                      │
                      ▼
Semana 4:    VEREDITO GO/NO-GO (matriz, seção 8)
```

---

## 7. Trabalho paralelo seguro (Semana 1)

**Decisões one-way (travar agora):**
- Wedge B primário ✓
- Stack: TypeScript (ingestão/indexer) + Python (quant)
- Chains MVP: Ethereum + Base
- **Licença:** *não* MIT em tudo. Infra-commodity (wrappers/helpers/queries) → permissiva/MIT; **modelo de risco → source-available/proprietária (estilo BSL).** Precedente: core da Morpho Blue é **BUSL-1.1**.
- **Enquadramento regulatório (1h, 1 página commitada):** "informacional, **sem execução, sem conselho personalizado**". É o que o Teste 1 pode tentar você a violar (se a atribuição apontar para "precisa de ação automática", vira produto regulado).

**Scaffold de engenharia (menor alavancagem — pode escorregar 1 dia):**
- Repo público + README + roadmap + LICENSE (split MIT/BUSL); pyproject + lockfile; CI básico (lint + test, sem deploy); schema base dos models de risco.

**Dados sem indexer próprio:**
- Dune (posições liquidadas) + subgraph Morpho (primária) + GraphQL oficial (secundária). ~70% do necessário para o backtest. Exceção: preço de oráculo histórico (seção 3.3).

---

## 8. O que **não** fazer agora

| Não comece | Por quê |
|---|---|
| Indexer próprio multi-chain | 3 meses de buraco; subgraph + Dune chegam. Decide após a pesquisa. |
| Black-Cox/Merton completo | Simples primeiro. O Teste 1 nem precisa do modelo estrutural — precisa da reconstrução crua. Sofisticação só após o sinal validar. |
| API B2B / SaaS infra | Mês 4–5. |
| Pesquisa profunda de MiCA | Mês 3–4 (mas trave o **enquadramento** agora). |
| Dashboard borrower-facing completo | Suba só uma versão mínima read-only ("health checker") como distribuição da pesquisa. Se o tempo apertar na semana 2, **publique a pesquisa primeiro** — ela é a substância; o checker é distribuição. |

---

## 9. Matriz de decisão GO/NO-GO *(coluna CONTESTADO refeita — delta 3)*

Lê-se por **coluna de Espaço** (com Sinal não-FRACO); a Rampa só modula *como* se executa.

| Espaço (T2) | Veredito (Sinal FORTE/MÉDIO) | Papel da Rampa (T3) |
|---|---|---|
| **ABERTO** | **GO pleno** — build no ritmo normal | TEM/FINA → outbound + inbound · SEM → inbound-led (ferramenta pública + pesquisa; adia outbound) |
| **CONTESTADO** | **GO acelerado com cláusula de obsolescência** — corre a janela antes do incumbente comprimir; exige plano de defensibilidade explícito (por que você sobrevive ao incumbente descer / ao integrador construir) | TEM/FINA → outbound-led · SEM → inbound-led |
| **FECHADO** | **NO-GO no formato atual** — repensar ângulo/wedge antes de qualquer build | — |

**Regra transversal — Sinal FRACO (qualquer Espaço/Rampa):** **Pivô de tese.** O produto de aviso é marginal. Avaliar: (a) produto de **ação automática/pré-autorizada** (mais regulado), ou (b) **Wedge A** (exit-liquidity do lender). **Não buildar o aviso.**

---

## 10. Cronograma consolidado

| Quando | Atividade | Entregável |
|---|---|---|
| Dia 0 (antes de dados) | GATE ZERO | `validation-preregistration.md` commitado |
| Semana 1–2 | Teste 1 (fev + out) + scaffold + dados externos | Reconstruções (3 camadas, 2 regimes) + peça de pesquisa publicada + health checker mínimo |
| Semana 2–4 | Teste 2 (Morpho + integrador, c/ pedido de alert-delivery) + Teste 3 (rampa) | Posição oficial + leitura build-vs-buy + inventário de 20 contatos |
| Semana 4 | Síntese | **Veredito GO/NO-GO** pela matriz |

---

## 11. Plano do Dia 1 (segunda-feira)

**Ordem importa:** o pré-registro vem **antes** de abrir o Dune — e isso é regra mecânica, não regra de honra.

1. **(BLOQUEANTE) Escrever, commitar e *pushar* `validation-preregistration.md` no repo público.** O commit hash deste arquivo é referenciado em qualquer query Dune daqui em diante. O passo 4 (queries) **só inicia após este commit existir no remote** — assim, quem olhar o repo em 6 meses verifica pela timeline do git que o pré-registro veio antes da primeira query.
2. Decisão de enquadramento regulatório → 1 página commitada.
3. Repo público + README + roadmap + LICENSE (split MIT/BUSL); pyproject + lockfile + CI básico.
4. Setup Dune + primeiras queries de liquidações (fev/2026; depois out/2025). *Bloqueado até o commit do passo 1 estar no remote.*
5. Inventário inicial de 20 contatos integradores (LinkedIn + crossover de portfolio), por grau e função.

**Fim da semana 1:** 2–3 liquidações reconstruídas, peça de pesquisa em draft, contatos categorizados.
**Fim da semana 2:** pesquisa publicada (fórum Morpho + X + Dune), health checker mínimo no ar, outreach iniciado.
**Semana 4:** veredito pela matriz.

---

## 12. Apêndice — premissas e fontes

- **Validadas em jun/2026:** Morpho US$11B+ depósitos / TVL Blue ~US$6,57B; rodada US$175M (~US$2B), Paradigm/a16z crypto/Ribbit + Apollo/Circle Ventures/VanEck/Ledger Cathay; integradores Coinbase, Binance, Kraken, Société Générale, Anchorage, Galaxy, Bitwise, Ledger, Trezor.
- **fev/2026:** BTC −17%/ETH −26% na semana; ~US$238M liquidações Morpho (Steakhouse); Coinbase US$170M colateral liquidado, US$90,7M numa quinta, ~2.000 usuários no dia, ~3.300 sem intervir; avisos "a cada 30 min" reconhecidamente atrasam.
- **out/2025:** flash crash usado por Hypernative como prova de monitoramento de bad debt em tempo real — base da checagem out-of-sample.
- **Incumbente oficial:** Hypernative (jul/2025; foco curador/instituição).
- **Licença:** core Morpho Blue sob BUSL-1.1.
- **Régua quant:** debate público (abr/2026) sobre modelos estruturais de crédito (Black-Cox/Merton) e parâmetro LGD em CDPs DeFi.
- **Heurísticas (não dados):** hit-rate cold ~5–10% / warm ~40–60%; limiares de janela — direcionais, a travar no pré-registro.

*Métricas de DeFi mudam rápido: revalidar TVL, liquidações e integradores na véspera de qualquer apresentação externa.*

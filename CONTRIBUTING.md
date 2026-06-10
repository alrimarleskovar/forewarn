# CONTRIBUTING

## Regra bloqueante: pré-registro antes de dados (norma do repo)

> **Nenhum arquivo em `dune/queries/` pode ganhar conteúdo antes de o commit do `docs/validation-preregistration.md` — com a tabela de limiares (§ 4) preenchida — existir no remote.**

Motivo: o veredito GO/NO-GO depende de limiares **pré-comprometidos**. Depois de inspecionar dados de liquidação, pré-registrar é logicamente impossível, e "FRACO" viraria "talvez MÉDIO" quando inconveniente.

Esta regra é **mecânica, não de honra**:

1. O job `preregistration-gate` no CI (`.github/workflows/ci.yml`) **falha** se ambas forem verdadeiras:
   - a seção § 4 de `docs/validation-preregistration.md` ainda contém `[___]`; **e**
   - existe algum `dune/queries/*.sql` com conteúdo não-vazio.
2. O template de PR inclui a checagem manual prévia correspondente.
3. A timeline do git deve permitir que terceiros verifiquem a ordem: pré-registro primeiro, queries depois. Toda query Dune referencia o hash do commit do pré-registro.

O check de `[___]` é limitado à **seção § 4 (limiares)** — campos de nome/data/assinatura podem ficar em branco sem bloquear.

### Ajuste de limiar após ver dados

Permitido **somente** via a cláusula § 6 do próprio pré-registro: motivo explícito, limiar antigo → novo, reset de expectativa e aprovação, em log append-only.

## Pre-registration commit

O commit do `docs/validation-preregistration.md` preenchido DEVE ser **separado** (nenhum outro arquivo junto) e usar exatamente esta mensagem, auditável por terceiros:

```
chore(validation): commit pre-registered thresholds

No liquidation data has been inspected prior to this commit.
See attestation in docs/validation-preregistration.md § 0.
Signed-off-by: [name]
```

Após o push desse commit, ancorar externamente (OpenTimestamps no arquivo e/ou hash do commit postado publicamente).

## Fluxo geral

- Branch a partir de `main`; PR obrigatório com 1 review (ver `docs/branch-protection-checklist.md`).
- CI deve passar: lint + test (`quant/` e `packages/ingestion/`), `preregistration-gate` e CodeQL.
- `quant/` usa **uv** (`uv sync`, `uv run ruff check`, `uv run pytest`); `packages/ingestion/` usa npm (`npm run lint`, `npm test`).
- Atualize docs quando o comportamento ou o processo mudar.
- Vulnerabilidades: **não** abra issue pública — ver `SECURITY.md`.

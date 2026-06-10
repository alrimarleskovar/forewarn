# Security Policy

## Como reportar

Reporte vulnerabilidades **em privado**:

- Preferencial: GitHub Security Advisory privado — `https://github.com/alrimarleskovar/forewarn/security/advisories/new`
- Alternativa: e-mail `alrimar6@gmail.com`

**Não** abra issue pública para falhas de segurança. Responderemos em até 7 dias.

## Escopo e postura

Este projeto é **analytics read-only**:

- **Sem custódia** de fundos. **Sem smart contracts** próprios. **Sem execução de transações.**
- Não há código de produto em produção nesta fase (validação pré-build).

A superfície de risco real é:

1. **Dependências** (npm em `packages/ingestion/`, pip/uv em `quant/`, GitHub Actions) — monitoradas por Dependabot e CodeQL.
2. **Vazamento de segredos** — chaves de RPC/Dune e arquivos `.env` (nunca commitados; ver `.gitignore`; secret scanning + push protection habilitados nas settings do repo).
3. **Supply-chain** — pacotes comprometidos, actions não-pinadas.

## Auditoria

Auditoria real (modelo de risco e qualquer contrato/código de produto) é **pós-GO** — não existe código de produto para auditar nesta fase. O Dia 1 cobre postura + scanning automático (CodeQL, Dependabot, secret scanning), não auditoria de código.

## Supported versions

| Versão | Suportada |
|---|---|
| `main` | ✅ |

# Security Policy

## How to report

Report vulnerabilities **privately**:

- Preferred: private GitHub Security Advisory — `https://github.com/alrimarleskovar/forewarn/security/advisories/new`
- Alternative: e-mail `alrimar6@gmail.com`

Do **not** open a public issue for security flaws. We will respond within 7 days.

## Scope and posture

This project is **read-only analytics**:

- **No custody** of funds. **No smart contracts** of our own. **No transaction execution.**
- There is no product code in production at this stage (pre-build validation).

The actual risk surface is:

1. **Dependencies** (npm in `packages/ingestion/`, pip/uv in `quant/`, GitHub Actions) — monitored by Dependabot and CodeQL.
2. **Secret leakage** — RPC/Dune keys and `.env` files (never committed; see `.gitignore`; secret scanning + push protection enabled in the repo settings).
3. **Supply chain** — compromised packages, unpinned actions.

## Auditing

A real audit (of the risk model and any product contract/code) comes **after the validation verdict** — there is no product code to audit at this stage. Day 1 covers posture + automated scanning (CodeQL, Dependabot, secret scanning), not a code audit.

## Supported versions

| Version | Supported |
|---|---|
| `main` | ✅ |

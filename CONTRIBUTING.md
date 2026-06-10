# CONTRIBUTING

## Blocking rule: pre-registration before data (repo norm)

> **No file in `dune/queries/` may receive content before the commit of `docs/validation-preregistration.md` — with the thresholds table (§ 4) filled in — exists on the remote.**

Reason: the GO/NO-GO verdict depends on **pre-committed** thresholds. After inspecting liquidation data, pre-registering is logically impossible, and "WEAK" would turn into "maybe MEDIUM" whenever inconvenient.

This rule is **mechanical, not honor-based**:

1. The `preregistration-gate` job in CI (`.github/workflows/ci.yml`) **fails** if both of the following are true:
   - section § 4 of `docs/validation-preregistration.md` still contains `[___]`; **and**
   - some `dune/queries/*.sql` exists with non-empty content.
2. The PR template includes the corresponding manual pre-check.
3. The git timeline must allow third parties to verify the order: pre-registration first, queries after. Every Dune query references the hash of the pre-registration commit.

The `[___]` check is limited to **section § 4 (thresholds)** — name/date/signature fields may be left blank without blocking.

### Adjusting a threshold after seeing data

Allowed **only** via clause § 6 of the pre-registration itself: explicit reason, old → new threshold, expectation reset and approval, in an append-only log.

## Pre-registration commit

The commit of the filled-in `docs/validation-preregistration.md` (English courtesy copy: `docs/validation-preregistration.en.md`) MUST be **separate** (no other files included) and use exactly this message, auditable by third parties:

```
chore(validation): commit pre-registered thresholds

No liquidation data has been inspected prior to this commit.
See attestation in docs/validation-preregistration.md § 0.
Signed-off-by: [name]
```

After pushing that commit, anchor it externally (OpenTimestamps on the file and/or the commit hash posted publicly).

## General workflow

- Branch off `main`; PR required with 1 review (see `docs/branch-protection-checklist.md`).
- CI must pass: lint + test (`quant/` and `packages/ingestion/`), `preregistration-gate`, and CodeQL.
- `quant/` uses **uv** (`uv sync`, `uv run ruff check`, `uv run pytest`); `packages/ingestion/` uses npm (`npm run lint`, `npm test`).
- Update the docs whenever behavior or process changes.
- Vulnerabilities: do **not** open a public issue — see `SECURITY.md`.

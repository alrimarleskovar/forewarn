## What changes

<!-- short description -->

## Checklist

- [ ] Lint and tests pass locally (`quant/`: `uv run ruff check . && uv run pytest`; `packages/ingestion/`: `npm run lint && npm test`).
- [ ] Docs updated, if behavior or process changed.
- [ ] **Pre-registration gate:** if this PR touches `dune/queries/*.sql`, I confirm that
      `docs/validation-preregistration.md` § 4 does not contain `[___]`.
      (The `preregistration-gate` CI fails anyway — this is the prior manual check.)

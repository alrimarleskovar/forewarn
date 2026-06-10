## O que muda

<!-- descrição curta -->

## Checklist

- [ ] Lint e testes passam localmente (`quant/`: `uv run ruff check . && uv run pytest`; `packages/ingestion/`: `npm run lint && npm test`).
- [ ] Docs atualizadas, se o comportamento ou o processo mudou.
- [ ] **Pre-registration gate:** se este PR toca `dune/queries/*.sql`, confirmo que
      `docs/validation-preregistration.md` § 4 não contém `[___]`.
      (O CI `preregistration-gate` falha de qualquer forma — esta é a checagem manual prévia.)

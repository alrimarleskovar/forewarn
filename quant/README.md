# risk-model (quant)

Módulo quant do Morpho Risk Tooling.

**Licença: BUSL-1.1** (Change License: Apache-2.0) — ver `LICENSE-BSL` na raiz e `LICENSING.md`. Uso adicional permitido: pesquisa não-produtiva e avaliação interna.

Nesta fase (validação pré-build) o módulo contém **apenas o schema base** (`src/risk_model/schema.py`) — tipos pydantic, sem lógica. O modelo estrutural (Black-Cox/Merton, point-in-time) **não** é implementado antes do veredito GO.

## Dev

Python pinado em `3.11.7` (`.python-version`); gerenciado com [uv](https://docs.astral.sh/uv/) — `uv.lock` commitado.

```bash
uv sync
uv run ruff check .
uv run pytest
```

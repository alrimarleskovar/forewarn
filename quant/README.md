# risk-model (quant)

Quant module of the Morpho Risk Tooling.

**License: BUSL-1.1** (Change License: Apache-2.0) — see `LICENSE-BSL` at the repo root and `LICENSING.md`. Additional use permitted: non-production research and internal evaluation.

At this stage (pre-build validation) the module contains **only the base schema** (`src/risk_model/schema.py`) — pydantic types, no logic. The structural model (Black-Cox/Merton, point-in-time) is **not** implemented before a GO verdict.

## Dev

Python pinned at `3.11.7` (`.python-version`); managed with [uv](https://docs.astral.sh/uv/) — `uv.lock` is committed.

```bash
uv sync
uv run ruff check .
uv run pytest
```

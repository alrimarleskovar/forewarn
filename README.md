# forewarn

Liquidation early-warning research and live risk monitoring for
[Morpho](https://morpho.org) lending markets on Ethereum and Base.

**Live dashboard: [forewarn.vercel.app](https://forewarn.vercel.app)**

> Scope: informational tooling only — no transaction execution, no custody,
> no personalized financial advice.

## Method

The starting point is a backtest of the February 2026 stress event: for a
sample of real liquidations, we replay each position hour by hour in a strict
**walk-forward** fashion — at every step the model only sees prices knowable at
that timestamp (no look-ahead) — and measure how much earlier a simple health
alert (10% buffer over the liquidation threshold) would have fired. Position
sizes are read from the Morpho Blue contract state at the pre-liquidation
block; an attribution pass then checks, at the alert block, whether the
borrower had gas and accessible funds to cure. To keep the measurement honest,
all thresholds were **pre-registered and externally anchored before any data
was inspected** (see `docs/validation-preregistration.md`, Portuguese canonical,
with an [English courtesy translation](docs/validation-preregistration.en.md));
a CI gate blocks data queries from landing before the pre-registration commit.

The live monitor points the same health math at current on-chain state: it
enumerates borrowers across all relevant Morpho markets (non-idle, ≥ $50k
borrowed) via the official API, then verifies every position on-chain at a
pinned block with Multicall3-batched `position()` reads and each market's own
oracle. Markets are bucketed as **directional** (volatile collateral vs.
uncorrelated debt — where a warning matters, and what the dashboard headline
counts), **correlated** (stable/stable or LST/underlying pairs, peg-checked —
intentional leverage), or **anomalous** (a "stable" side trading below ~97% of
its native peg). All cutoffs are logged in the snapshot metadata, never silent.

## Repository layout

| Path | What | License |
|---|---|---|
| `quant/` | Risk engine: backtest, attribution, live monitor, dashboard generator | **BUSL-1.1** |
| `packages/ingestion/` | TypeScript data-ingestion stub | MIT |
| `dune/` | SQL for the raw liquidation extraction | MIT |
| `docs/` | Pre-registration + process docs | MIT |
| `site/` | Generated static dashboard (deployed to Vercel) | MIT |

See `LICENSING.md` for the split. The quant module converts to Apache-2.0 on
the BUSL Change Date.

## Reproduce

```bash
cd quant
uv sync                              # Python 3.11, pinned via .python-version
uv run ruff check . && uv run pytest # lint + tests
uv run python -m risk_model.refresh  # full refresh: live monitor → site/index.html
```

Individual stages: `warning_window_v1` (backtest), `attribution_v1`
(capacity-to-cure), `demo_prep_v1_1` (real-size v1.1 + demo trajectories),
`live_monitor_v1` (snapshot only), `dashboard_v0` (HTML only). Outputs land in
`results/` (gitignored); the dashboard is written to `site/index.html`. Public
data sources only: Morpho GraphQL API, public archival RPCs, CoinGecko, ECB FX.

## Pre-registration ordering rule

No file in `dune/queries/` may gain content before the commit of
`docs/validation-preregistration.md` with thresholds filled (§ 4) exists on the
remote. The `preregistration-gate` CI job enforces this mechanically — see
`CONTRIBUTING.md`.

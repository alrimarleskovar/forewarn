# SPDX-License-Identifier: BUSL-1.1
# Licensed Work: Morpho Risk Tooling — Quant Module. See LICENSE-BSL at the repo root.
"""Live monitor v1 — all relevant Morpho markets (Ethereum + Base).

Evolution of v0 (2 markets → all): same health math, same real per-market
oracle, same logged dust cutoffs. "Relevant" markets = non-idle with
borrow ≥ US$50k (cutoff logged in the JSON).

Health is 100% on-chain (collateral × price()/1e36 × LLTV ÷ debt — valid
for any pair). USD enters ONLY in the ranking/aggregate, via the Morpho
API's loanAsset.priceUsd.

Market metadata (idToMarketParams/market/price) and position() per borrower
are read in batches via Multicall3 at a pinned block per chain; reverting
oracles are skipped and counted (tryAggregate).

Usage:
    uv run python -m risk_model.live_monitor_v1
"""

import json
import sys
import time
from datetime import UTC, datetime

import requests

from risk_model.live_monitor_v0 import (
    MIN_DEBT_USD,
    MORPHO,
    MULTICALL3,
    SEL_ID_TO_PARAMS,
    SEL_MARKET,
    SEL_ORACLE_PRICE,
    SWEEP_HEALTH_LTE,
    SWEEP_MIN_DEBT_USD,
    batch_positions,
    decode_aggregate,
    encode_aggregate,
    enumerate_borrowers,
    gql,
    rpc_multi,
)
from risk_model.warning_window_v1 import ALERT_BUFFER, RESULTS

SEL_TRY_AGGREGATE = "0xbce38bd7"  # tryAggregate(bool,(address,bytes)[])
MARKET_MIN_BORROW_USD = 50_000.0

# --- collateral×debt correlation heuristic (approximation, logged) ------------
# stable-stable (sUSDe/USDtb) and same LST/underlying family (wstETH/WETH,
# LBTC/WBTC) = "correlated": intentional leverage, low risk of price-driven
# liquidation. Everything else = "directional" (cbBTC/USDC), where warning
# matters.
STABLE_EXTRA = {"DAI", "SDAI", "FRAX", "LUSD", "GHO", "USR", "EURC", "EURE",
                "DOLA", "BOLD", "MKUSD", "RLUSD"}
CORRELATION_HEURISTIC = (
    "asset class by symbol: 'USD' in the symbol or stables list → stable; "
    "'BTC' → BTC family; 'ETH' → ETH family; same class (stable-stable, "
    "eth-eth, btc-btc) = correlated, rest = directional. Approximation — does "
    "not consider peg depth or the oracle."
)


def asset_class(symbol: str) -> str:
    s = symbol.upper()
    if "USD" in s or s in STABLE_EXTRA:
        return "stable"
    if "BTC" in s:
        return "btc"
    if "ETH" in s:
        return "eth"
    return "other"


def classify_market(collateral_symbol: str, loan_symbol: str) -> tuple[str, str]:
    """('correlated'|'directional', reason) — simple symbol-based heuristic."""
    a, b = asset_class(collateral_symbol), asset_class(loan_symbol)
    if a == b and a in ("stable", "eth", "btc"):
        return "correlated", f"{a}-{b}"
    return "directional", f"{a}-{b}"


# --- v1.3: asymmetric peg check, in the asset's own currency -------------------
# Depeg flag ONLY below ~97% of the NATIVE peg (or no price). Above par is
# normal: yield-bearing wrappers (sUSDe, sUSDS, syrupUSDC) are worth >$1 by
# design. Euro stables (EURC/EURe) are compared against EUR/USD, not $1.
DEPEG_BELOW = 0.97


def get_peg_targets() -> dict[str, float | None]:
    """{'USD': 1.0, 'EUR': EUR/USD rate}. EUR=None if FX fails (do not flag)."""
    targets: dict[str, float | None] = {"USD": 1.0}
    try:
        resp = requests.get("https://api.frankfurter.app/latest?from=EUR&to=USD", timeout=15)
        resp.raise_for_status()
        targets["EUR"] = float(resp.json()["rates"]["USD"])
    except Exception:  # noqa: BLE001 — without FX, EUR stables are not judged
        targets["EUR"] = None
    return targets


def stable_currency(symbol: str) -> str:
    return "EUR" if symbol.upper() in ("EURC", "EURE", "EURS") else "USD"


def depegged_stables(sides: list[tuple[str, float | None, str]],
                     targets: dict[str, float | None]) -> list[dict]:
    """Stables below DEPEG_BELOW × native peg (or with no price)."""
    out = []
    for sym, price, side in sides:
        if asset_class(sym) != "stable":
            continue
        target = targets.get(stable_currency(sym))
        if target is None:
            continue  # FX unavailable — no judgment
        if price is None or price < DEPEG_BELOW * target:
            out.append({"side": side, "symbol": sym, "price_usd": price,
                        "peg_target_usd": target})
    return out


def classify_market_v2(coll_sym: str, coll_price: float | None,
                       loan_sym: str, loan_price: float | None,
                       targets: dict[str, float | None]) -> tuple[str, str, list[dict]]:
    """('directional'|'correlated'|'anomalous', reason, real depegs)."""
    base, reason = classify_market(coll_sym, loan_sym)
    depegs = depegged_stables(
        [(coll_sym, coll_price, "collateral"), (loan_sym, loan_price, "loan")], targets
    )
    if base == "correlated" and depegs:
        names = ", ".join(f"{d['symbol']}@{d['price_usd']}" for d in depegs)
        return "anomalous", f"{reason} + depeg ({names})", depegs
    return base, reason, depegs
CHAINS = [1, 8453]
CHAIN_NAME = {1: "ethereum", 8453: "base"}
META_CHUNK = 150

MARKETS_QUERY = """
query ($first: Int!, $skip: Int!) {
  markets(
    first: $first, skip: $skip,
    where: { chainId_in: [1, 8453], isIdle: false, borrowAssetsUsd_gte: MIN_BORROW },
    orderBy: BorrowAssetsUsd, orderDirection: Desc
  ) {
    pageInfo { countTotal }
    items {
      marketId lltv chain { id }
      collateralAsset { address symbol decimals priceUsd }
      loanAsset { address symbol decimals priceUsd }
      state { borrowAssetsUsd }
    }
  }
}
""".replace("MIN_BORROW", str(int(MARKET_MIN_BORROW_USD)))


def discover_markets() -> tuple[list[dict], dict]:
    out, skipped = [], {"no_collateral": 0, "no_loan_price": 0, "zero_lltv": 0}
    targets = get_peg_targets()
    skip = 0
    while True:
        data = gql(MARKETS_QUERY, {"first": 500, "skip": skip})["markets"]
        for it in data["items"]:
            coll, loan = it["collateralAsset"], it["loanAsset"]
            if not coll:
                skipped["no_collateral"] += 1
                continue
            if not loan.get("priceUsd"):
                skipped["no_loan_price"] += 1
                continue
            if int(it["lltv"]) == 0:
                skipped["zero_lltv"] += 1
                continue
            coll_price = float(coll["priceUsd"]) if coll.get("priceUsd") else None
            bucket, corr_reason, depegs = classify_market_v2(
                coll["symbol"], coll_price, loan["symbol"], float(loan["priceUsd"]), targets
            )
            out.append({
                "chain_id": it["chain"]["id"],
                "chain": CHAIN_NAME[it["chain"]["id"]],
                "label": f"{coll['symbol']}/{loan['symbol']}",
                "bucket": bucket,
                "correlation": bucket,  # compat: older dashboards read this field
                "correlation_reason": corr_reason,
                "depegged_assets": depegs,
                "collateral_price_usd": coll_price,
                "market_id": it["marketId"],
                "collateral_decimals": coll["decimals"],
                "loan_decimals": loan["decimals"],
                "loan_price_usd": float(loan["priceUsd"]),
                "borrow_usd_api": it["state"]["borrowAssetsUsd"],
            })
        skip += 500
        if skip >= data["pageInfo"]["countTotal"]:
            return out, skipped


def _multicall(chain_id: int, calls: list[tuple[str, str]], block_hex: str,
               tolerate_revert: bool = False) -> list[str | None]:
    """Batch of eth_calls; with tolerate_revert uses tryAggregate (None on reverts)."""
    results: list[str | None] = []
    for i in range(0, len(calls), META_CHUNK):
        chunk = calls[i : i + META_CHUNK]
        if not tolerate_revert:
            data = encode_aggregate(chunk)
            raw = rpc_multi(chain_id, "eth_call", [{"to": MULTICALL3, "data": data}, block_hex])
            results.extend(decode_aggregate(raw))
        else:
            # tryAggregate(false, calls): bool + offset + same array as aggregate
            array = encode_aggregate(chunk)[10 + 64:]
            data = SEL_TRY_AGGREGATE + f"{0:064x}" + f"{0x40:064x}" + array
            raw = rpc_multi(chain_id, "eth_call", [{"to": MULTICALL3, "data": data}, block_hex])
            h = raw[2:] if raw.startswith("0x") else raw
            arr_off = int(h[0:64], 16) * 2
            n = int(h[arr_off : arr_off + 64], 16)
            base = arr_off + 64
            for j in range(n):
                rel = int(h[base + j * 64 : base + (j + 1) * 64], 16) * 2
                start = base + rel
                ok = int(h[start : start + 64], 16) == 1
                blen = int(h[start + 128 : start + 192], 16)
                results.append(h[start + 192 : start + 192 + blen * 2] if ok else None)
        time.sleep(0.3)
    return results


def load_market_chain_state(markets: list[dict], blocks: dict[int, str]) -> int:
    """Attaches on-chain oracle/lltv/tba/tbs/price36 to each market. Returns skip count."""
    skipped_oracle = 0
    for cid in CHAINS:
        group = [m for m in markets if m["chain_id"] == cid]
        if not group:
            continue
        block_hex = blocks[cid]
        params = _multicall(
            cid, [(MORPHO, SEL_ID_TO_PARAMS[2:] + m["market_id"][2:]) for m in group], block_hex
        )
        states = _multicall(
            cid, [(MORPHO, SEL_MARKET[2:] + m["market_id"][2:]) for m in group], block_hex
        )
        for m, p, s in zip(group, params, states, strict=True):
            m["oracle"] = "0x" + p[64 * 2 + 24 : 64 * 3]
            m["lltv"] = int(p[64 * 4 : 64 * 5], 16) / 1e18
            m["tba"] = int(s[128:192], 16)
            m["tbs"] = int(s[192:256], 16)
        prices = _multicall(
            cid, [(m["oracle"], SEL_ORACLE_PRICE[2:]) for m in group], block_hex,
            tolerate_revert=True,
        )
        for m, pr in zip(group, prices, strict=True):
            if pr is None or pr == "":
                m["price36"] = None
                skipped_oracle += 1
            else:
                m["price36"] = int(pr, 16)
    return skipped_oracle


def main() -> int:
    snapshot_ts = int(time.time())
    blocks = {cid: rpc_multi(cid, "eth_blockNumber", []) for cid in CHAINS}
    print(f"Snapshot @ {datetime.fromtimestamp(snapshot_ts, tz=UTC).isoformat()} "
          f"| blocks: { {cid: int(b, 16) for cid, b in blocks.items()} }")

    markets, disc_skipped = discover_markets()
    print(f"relevant markets (borrow ≥ ${MARKET_MIN_BORROW_USD:,.0f}): {len(markets)} "
          f"| dropped during discovery: {disc_skipped}")
    skipped_oracle = load_market_chain_state(markets, blocks)
    active_markets = [m for m in markets if m.get("price36")]
    print(f"on-chain metadata OK: {len(active_markets)} | reverting oracles: {skipped_oracle}")

    positions, meta_markets, failed_markets = [], [], []
    covered = 0
    consecutive_failures = 0
    for idx, m in enumerate(active_markets, 1):
        try:
            borrowers, stats = enumerate_borrowers(m)
            addr_list = list(borrowers)
            states = batch_positions(
                m["chain_id"], m["market_id"], addr_list, blocks[m["chain_id"]], m
            ) if addr_list else {}
            consecutive_failures = 0
            n_risk = 0
            for addr, (coll_raw, debt_raw) in states.items():
                if debt_raw == 0 or coll_raw == 0:
                    continue
                health = coll_raw * m["price36"] / 1e36 * m["lltv"] / debt_raw
                debt_usd = debt_raw / 10 ** m["loan_decimals"] * m["loan_price_usd"]
                at_risk = health < ALERT_BUFFER
                n_risk += at_risk
                positions.append({
                    "chain": m["chain"], "market": m["label"], "market_id": m["market_id"],
                    "borrower": addr,
                    "health": round(health, 4),
                    "distance_to_threshold_pct": round((health - 1) * 100, 2),
                    "debt_usd": round(debt_usd, 2),
                    "at_risk": at_risk,
                    "bucket": m["bucket"],
                    "correlated": m["bucket"] == "correlated",
                })
            meta_markets.append({
                "chain": m["chain"], "chain_id": m["chain_id"], "label": m["label"],
                "bucket": m["bucket"],
                "correlation": m["bucket"],
                "correlation_reason": m["correlation_reason"],
                "depegged_assets": m["depegged_assets"],
                "collateral_price_usd": m["collateral_price_usd"],
                "loan_price_usd": m["loan_price_usd"],
                "market_id": m["market_id"], "lltv": m["lltv"], "oracle": m["oracle"],
                "block": int(blocks[m["chain_id"]], 16),
                "active_positions": stats["total_active"],
                "verified_onchain": len(addr_list),
            })
            covered = idx
            if idx % 25 == 0 or idx == len(active_markets):
                print(f"  …{idx}/{len(active_markets)} markets "
                      f"({len(positions):,} positions verified)")
        except Exception as exc:  # noqa: BLE001 — skip the market, count, move on
            consecutive_failures += 1
            failed_markets.append({"label": m["label"], "chain": m["chain"], "error": str(exc)})
            print(f"  FAILURE on {m['label']} ({m['chain']}): {exc} — skipping")
            if consecutive_failures >= 5:
                print(f"\nABORTED: 5 consecutive failures (API/RPC down?). "
                      f"Coverage: {covered}/{len(active_markets)} markets.")
                raise

    if failed_markets:
        print(f"markets skipped due to failure: {len(failed_markets)}")

    positions.sort(key=lambda p: p["health"])
    at_risk = [p for p in positions if p["at_risk"]]
    out = {
        "snapshot_ts": snapshot_ts,
        "snapshot_iso": datetime.fromtimestamp(snapshot_ts, tz=UTC).isoformat(),
        "alert_buffer": ALERT_BUFFER,
        "rule": "at risk if on-chain health < 1.10 (same rule as the backtest)",
        "n_markets": len(meta_markets),
        "chains": [CHAIN_NAME[c] for c in CHAINS],
        "correlation_heuristic": CORRELATION_HEURISTIC,
        "depeg_rule": f"flag only below {DEPEG_BELOW} × native peg (EUR via FX); "
                      "above par = normal (yield-bearing wrapper)",
        "usd_valuation_flags": [
            {"label": m["label"], "chain": m["chain"], "depegged": m["depegged_assets"]}
            for m in meta_markets if any(
                d["side"] == "loan" for d in m["depegged_assets"]
            )
        ],
        "enumeration_cutoffs": {
            "market_min_borrow_usd": MARKET_MIN_BORROW_USD,
            "min_debt_usd": MIN_DEBT_USD,
            "sweep_health_lte": SWEEP_HEALTH_LTE,
            "sweep_min_debt_usd": SWEEP_MIN_DEBT_USD,
            "discovery_skipped": disc_skipped,
            "reverting_oracles_skipped": skipped_oracle,
            "failed_markets": failed_markets,
        },
        "markets": meta_markets,
        "positions": positions,
    }
    (RESULTS / "at_risk_snapshot.json").write_text(json.dumps(out, ensure_ascii=False))

    print("\n================ LIVE SNAPSHOT v1 ================")
    print(f"markets: {len(meta_markets)} | positions verified: {len(positions):,} | "
          f"AT RISK (<{ALERT_BUFFER}): {len(at_risk):,} | "
          f"debt at risk: ${sum(p['debt_usd'] for p in at_risk):,.0f}")
    print(f"JSON: {RESULTS / 'at_risk_snapshot.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

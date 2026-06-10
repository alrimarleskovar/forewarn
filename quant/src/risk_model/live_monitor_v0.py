# SPDX-License-Identifier: BUSL-1.1
# Licensed Work: Morpho Risk Tooling — Quant Module. See LICENSE-BSL at the repo root.
"""Live monitor v0 — single snapshot of at-risk positions (no service/alerting).

v0 markets: Base cbBTC/USDC and Ethereum wstETH/USDC (those of the Feb 2026 event).

Flow: enumerates active borrowers via the Morpho GraphQL API → reads CURRENT
on-chain state at a pinned block per chain (position() per borrower; market()
and idToMarketParams()/oracle.price() once per market) → health and distance
to the threshold using the SAME rule as the backtest (ALERT_BUFFER reused).

health = raw_collateral × oracle_price / 1e36 × LLTV / raw_debt
(the Morpho oracle price already comes at 1e36 scale adjusted for decimals;
debt = borrowShares→assets with virtual shares/assets, as in the backtest)

EXPLICIT enumeration cutoffs (logged, not silent):
- positions with debt < US$1,000 are left out of the ranking, EXCEPT when the
  API reports them with healthFactor ≤ 1.3 and debt ≥ US$100 (extra sweep).

Usage:
    uv run python -m risk_model.live_monitor_v0
"""

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

from risk_model.demo_prep_v1_1 import MORPHO, SEL_MARKET, SEL_POSITION
from risk_model.warning_window_v1 import ALERT_BUFFER, RESULTS

MORPHO_API = "https://blue-api.morpho.org/graphql"
SEL_ID_TO_PARAMS = "0x2c3c9157"  # idToMarketParams(bytes32) — keccak verified
SEL_ORACLE_PRICE = "0xa035b1fe"  # price()

MIN_DEBT_USD = 1_000.0
SWEEP_HEALTH_LTE = 1.3
SWEEP_MIN_DEBT_USD = 100.0

MARKETS = [
    {
        "chain_id": 8453,
        "chain": "base",
        "label": "cbBTC/USDC",
        "market_id": "0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836",
        "collateral_decimals": 8,
        "loan_decimals": 6,
    },
    {
        "chain_id": 1,
        "chain": "ethereum",
        "label": "wstETH/USDC",
        "market_id": "0xb323495f7e4148be5643a4ea4a8221eef163e4bccfdedc2a6f4696baacbc86cc",
        "collateral_decimals": 18,
        "loan_decimals": 6,
    },
]

POSITIONS_QUERY = """
query ($first: Int!, $skip: Int!, $chain: Int!, $mkt: String!, $orderBy: MarketPositionOrderBy!,
       $dir: OrderDirection!, $hfLte: Float) {
  marketPositions(
    first: $first, skip: $skip,
    where: { chainId_in: [$chain], marketUniqueKey_in: [$mkt], borrowShares_gte: 1,
             healthFactor_lte: $hfLte },
    orderBy: $orderBy, orderDirection: $dir
  ) {
    pageInfo { countTotal }
    items { user { address } healthFactor state { borrowAssetsUsd } }
  }
}
"""


def gql(query: str, variables: dict, retries: int = 6) -> dict:
    last = None
    for attempt in range(retries):
        try:
            resp = requests.post(
                MORPHO_API, json={"query": query, "variables": variables}, timeout=60
            )
            if resp.status_code in (429, 502, 503, 504):
                raise requests.exceptions.RetryError(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            payload = resp.json()
            if "errors" in payload:
                raise RuntimeError(f"Morpho API: {payload['errors']}")
            return payload["data"]
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
                requests.exceptions.RetryError) as exc:
            last = exc
            time.sleep(min(5 * 2**attempt, 120))  # backoff: 5s → 120s
    raise RuntimeError(f"Morpho API unavailable after {retries} attempts: {last}")


def enumerate_borrowers(mkt: dict) -> tuple[dict[str, dict], dict]:
    """{borrower: {api_health, api_debt_usd}} + cutoff metrics (for logging)."""
    out: dict[str, dict] = {}
    stats = {"enumerated": 0, "below_min_debt": 0, "sweep_added": 0, "total_active": 0}

    # main pass: largest debts first, stops once debt < MIN_DEBT_USD
    skip = 0
    stop = False
    while not stop:
        data = gql(POSITIONS_QUERY, {
            "first": 1000, "skip": skip, "chain": mkt["chain_id"], "mkt": mkt["market_id"],
            "orderBy": "BorrowShares", "dir": "Desc", "hfLte": None,
        })["marketPositions"]
        stats["total_active"] = data["pageInfo"]["countTotal"]
        items = data["items"]
        if not items:
            break
        for it in items:
            stats["enumerated"] += 1
            debt = it["state"]["borrowAssetsUsd"] or 0.0
            if debt < MIN_DEBT_USD:
                stats["below_min_debt"] += 1
                stop = True
                continue
            out[it["user"]["address"]] = {
                "api_health": it["healthFactor"], "api_debt_usd": debt,
            }
        skip += 1000

    # extra sweep: small ones already close to the threshold per the API
    skip = 0
    while True:
        data = gql(POSITIONS_QUERY, {
            "first": 1000, "skip": skip, "chain": mkt["chain_id"], "mkt": mkt["market_id"],
            "orderBy": "HealthFactor", "dir": "Asc", "hfLte": SWEEP_HEALTH_LTE,
        })["marketPositions"]
        items = data["items"]
        if not items:
            break
        for it in items:
            debt = it["state"]["borrowAssetsUsd"] or 0.0
            addr = it["user"]["address"]
            if addr not in out and debt >= SWEEP_MIN_DEBT_USD:
                out[addr] = {"api_health": it["healthFactor"], "api_debt_usd": debt}
                stats["sweep_added"] += 1
        skip += 1000
        if skip >= data["pageInfo"]["countTotal"]:
            break
    return out, stats


def onchain_market(chain_id: int, market_id: str, block_hex: str) -> dict:
    params = rpc_multi(
        chain_id, "eth_call", [{"to": MORPHO, "data": SEL_ID_TO_PARAMS + market_id[2:]}, block_hex]
    )[2:]
    oracle = "0x" + params[64 * 2 + 24 : 64 * 3]
    lltv = int(params[64 * 4 : 64 * 5], 16) / 1e18
    mres = rpc_multi(
        chain_id, "eth_call", [{"to": MORPHO, "data": SEL_MARKET + market_id[2:]}, block_hex]
    )[2:]
    total_borrow_assets = int(mres[128:192], 16)
    total_borrow_shares = int(mres[192:256], 16)
    price36 = int(
        rpc_multi(chain_id, "eth_call", [{"to": oracle, "data": SEL_ORACLE_PRICE}, block_hex]), 16
    )
    return {
        "oracle": oracle,
        "lltv": lltv,
        "tba": total_borrow_assets,
        "tbs": total_borrow_shares,
        "price36": price36,
    }


MULTICALL3 = "0xcA11bde05977b3631167028862bE2a173976CA11"  # same address on both chains
SEL_AGGREGATE = "0x252dba42"  # aggregate((address,bytes)[])
BATCH = 300

RPC_POOL = {
    1: ["https://ethereum-rpc.publicnode.com", "https://eth.drpc.org"],
    8453: ["https://base.drpc.org", "https://base-rpc.publicnode.com"],
}


def rpc_multi(chain_id: int, method: str, params: list, retries: int = 8):
    """eth_* with provider rotation — a 403/429 on one provider doesn't kill the run."""
    last = None
    for attempt in range(retries):
        url = RPC_POOL[chain_id][attempt % len(RPC_POOL[chain_id])]
        try:
            resp = requests.post(
                url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                timeout=60,
            )
            resp.raise_for_status()
            payload = resp.json()
            if "error" in payload:
                raise RuntimeError(payload["error"])
            return payload["result"]
        except Exception as exc:  # noqa: BLE001 — broad rotation with backoff
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"all RPCs failed ({method}): {last}")


def encode_aggregate(calls: list[tuple[str, str]]) -> str:
    """ABI-encodes aggregate(Call[]); calls = [(target, calldata_without_0x)]."""
    n = len(calls)
    tails = []
    for target, data in calls:
        dlen = len(data) // 2
        padded = data + "0" * (((32 - dlen % 32) % 32) * 2)
        tails.append(
            target[2:].lower().rjust(64, "0")
            + f"{0x40:064x}"
            + f"{dlen:064x}"
            + padded
        )
    heads, cum = [], 32 * n
    for t in tails:
        heads.append(f"{cum:064x}")
        cum += len(t) // 2
    array = f"{n:064x}" + "".join(heads) + "".join(tails)
    return SEL_AGGREGATE + f"{0x20:064x}" + array


def decode_aggregate(result_hex: str) -> list[str]:
    """Decodes (uint256, bytes[]) → list of hex returndata (without 0x)."""
    h = result_hex[2:] if result_hex.startswith("0x") else result_hex
    arr_off = int(h[64:128], 16) * 2
    n = int(h[arr_off : arr_off + 64], 16)
    base = arr_off + 64
    out = []
    for i in range(n):
        rel = int(h[base + i * 64 : base + (i + 1) * 64], 16) * 2
        start = base + rel
        blen = int(h[start : start + 64], 16)
        out.append(h[start + 64 : start + 64 + blen * 2])
    return out


def batch_positions(chain_id: int, market_id: str, borrowers: list[str], block_hex: str,
                    m: dict) -> dict[str, tuple[int, int]]:
    """{borrower: (raw_collateral, raw_debt)} via Multicall3, in batches of BATCH."""
    result: dict[str, tuple[int, int]] = {}
    for i in range(0, len(borrowers), BATCH):
        chunk = borrowers[i : i + BATCH]
        calls = [
            (MORPHO, SEL_POSITION[2:] + market_id[2:] + b[2:].lower().rjust(64, "0"))
            for b in chunk
        ]
        raw = rpc_multi(
            chain_id, "eth_call",
            [{"to": MULTICALL3, "data": encode_aggregate(calls)}, block_hex],
        )
        for borrower, ret in zip(chunk, decode_aggregate(raw), strict=True):
            borrow_shares, collateral = int(ret[64:128], 16), int(ret[128:192], 16)
            debt_raw = borrow_shares * (m["tba"] + 1) // (m["tbs"] + 10**6)
            result[borrower] = (collateral, debt_raw)
        time.sleep(0.3)
    return result


def main() -> int:
    snapshot_ts = int(time.time())
    blocks = {m["chain_id"]: rpc_multi(m["chain_id"], "eth_blockNumber", []) for m in MARKETS}
    print(f"Snapshot @ {datetime.fromtimestamp(snapshot_ts, tz=UTC).isoformat()} "
          f"| pinned blocks: { {cid: int(b, 16) for cid, b in blocks.items()} }")

    positions = []
    meta_markets = []
    for mkt in MARKETS:
        cid, mid = mkt["chain_id"], mkt["market_id"]
        block_hex = blocks[cid]
        m = onchain_market(cid, mid, block_hex)
        implied_price = m["price36"] / 1e36 * 10 ** (
            mkt["collateral_decimals"] - mkt["loan_decimals"]
        )
        print(f"\n[{mkt['label']} @ {mkt['chain']}] LLTV={m['lltv']:.2f} "
              f"implied oracle price ≈ ${implied_price:,.0f}")

        borrowers, stats = enumerate_borrowers(mkt)
        print(f"  active: {stats['total_active']} | candidates (debt ≥ ${MIN_DEBT_USD:,.0f}): "
              f"{len(borrowers) - stats['sweep_added']} | sweep HF≤{SWEEP_HEALTH_LTE} "
              f"(≥ ${SWEEP_MIN_DEBT_USD:,.0f}): +{stats['sweep_added']} | "
              f"below the cutoff: {stats['total_active'] - len(borrowers)}")
        meta_markets.append({**mkt, "lltv": m["lltv"], "oracle": m["oracle"],
                             "block": int(block_hex, 16), "active_positions": stats["total_active"],
                             "verified_onchain": len(borrowers)})

        addr_list = list(borrowers)
        print(f"  verifying {len(addr_list)} positions on-chain via Multicall3 "
              f"({(len(addr_list) + BATCH - 1) // BATCH} batches)…")
        states = batch_positions(cid, mid, addr_list, block_hex, m)
        for addr, (coll_raw, debt_raw) in states.items():
            if debt_raw == 0 or coll_raw == 0:
                continue
            health = coll_raw * m["price36"] / 1e36 * m["lltv"] / debt_raw
            debt_usd = debt_raw / 10 ** mkt["loan_decimals"]  # USDC ≈ USD
            positions.append({
                "chain": mkt["chain"], "market": mkt["label"], "market_id": mid,
                "borrower": addr,
                "health": round(health, 4),
                "distance_to_threshold_pct": round((health - 1) * 100, 2),
                "debt_usd": round(debt_usd, 2),
                "at_risk": health < ALERT_BUFFER,
            })

    positions.sort(key=lambda p: p["health"])
    at_risk = [p for p in positions if p["at_risk"]]
    out = {
        "snapshot_ts": snapshot_ts,
        "snapshot_iso": datetime.fromtimestamp(snapshot_ts, tz=UTC).isoformat(),
        "alert_buffer": ALERT_BUFFER,
        "rule": "at risk if on-chain health < 1.10 (same rule as the backtest)",
        "enumeration_cutoffs": {
            "min_debt_usd": MIN_DEBT_USD,
            "sweep_health_lte": SWEEP_HEALTH_LTE,
            "sweep_min_debt_usd": SWEEP_MIN_DEBT_USD,
        },
        "markets": meta_markets,
        "positions": positions,
    }
    out_path = RESULTS / "at_risk_snapshot.json"
    Path(out_path).write_text(json.dumps(out, indent=2, ensure_ascii=False))

    print("\n================ LIVE SNAPSHOT v0 ================")
    print(f"positions verified on-chain: {len(positions)} | AT RISK (<{ALERT_BUFFER}): "
          f"{len(at_risk)}")
    for p in at_risk[:15]:
        print(f"  {p['health']:.4f} ({p['distance_to_threshold_pct']:+.1f}%) "
              f"${p['debt_usd']:>12,.0f} {p['market']} {p['chain']} {p['borrower']}")
    if len(at_risk) > 15:
        print(f"  … and {len(at_risk) - 15} more (in the JSON)")
    print(f"JSON: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

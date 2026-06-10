# SPDX-License-Identifier: BUSL-1.1
# Licensed Work: Morpho Risk Tooling — Quant Module. See LICENSE-BSL at the repo root.
"""Attribution v1 — capacity to cure at the alert block (point-in-time).

For each position in results/warning_windows_v1.csv, at the block
corresponding to the alert hour (NEVER later):
- gas:   wallet's native (ETH) balance > ~US$2;
- funds: wallet balance of collateral + loan token + stablecoins, in USD;
- capacity = gas AND funds ≥ 10% of the debt (debt ≈ repaid_usd, v1 proxy).

Sources: public archival RPC (publicnode; archival verified against the
Beacon Chain deposit contract), block via DeFiLlama (adjusted to
timestamp ≤ alert), prices via the CoinGecko cache from warning_window_v1.

Documented limitations:
- Wallets that are smart contracts (is_contract flag) may pay gas via a
  paymaster (smart wallets on Base) — the gas proxy UNDERESTIMATES capacity.
- Funds in other wallets of the same owner are not observable → the ceiling
  is conservative (underestimated) for this reason too.

Usage:
    uv run python -m risk_model.attribution_v1
"""

import csv
import json
import statistics
import sys
import time

import requests

from risk_model.warning_window_v1 import (
    PRICE_CACHE,
    RESULTS,
    price_at_or_before,
)

RPC = {1: "https://ethereum-rpc.publicnode.com", 8453: "https://base-rpc.publicnode.com"}
LLAMA_CHAIN = {1: "ethereum", 8453: "base"}
CHAIN_ID = {"ethereum": 1, "base": 8453}

STABLES = {
    1: {
        "USDC": ("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 6),
        "USDT": ("0xdAC17F958D2ee523a2206206994597C13D831ec7", 6),
        "DAI": ("0x6B175474E89094C44Da98b954EedeAC495271d0F", 18),
    },
    8453: {
        "USDC": ("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", 6),
        "USDbC": ("0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA", 6),
        "DAI": ("0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb", 18),
    },
}

GAS_MIN_USD = 2.0
CURE_FRACTION = 0.10
ETH_PRICE_CACHE = PRICE_CACHE / "native_eth.json"


def rpc_call(chain_id: int, method: str, params: list, retries: int = 5):
    for attempt in range(retries):
        try:
            resp = requests.post(
                RPC[chain_id],
                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                timeout=30,
            )
            resp.raise_for_status()
            payload = resp.json()
            if "error" in payload:
                raise RuntimeError(payload["error"])
            time.sleep(0.12)
            return payload["result"]
        except Exception as exc:  # noqa: BLE001 — broad retry with backoff
            if attempt == retries - 1:
                raise RuntimeError(f"RPC {RPC[chain_id]} {method} failed: {exc}") from exc
            time.sleep(3 * (attempt + 1))


def block_at_or_before(chain_id: int, ts: int) -> int:
    """Block with timestamp ≤ ts: DeFiLlama gives the guess, RPC adjusts backward."""
    resp = requests.get(f"https://coins.llama.fi/block/{LLAMA_CHAIN[chain_id]}/{ts}", timeout=30)
    resp.raise_for_status()
    height = resp.json()["height"]
    while True:
        blk = rpc_call(chain_id, "eth_getBlockByNumber", [hex(height), False])
        if int(blk["timestamp"], 16) <= ts:
            return height
        height -= 1


def erc20_balance(chain_id: int, token: str, holder: str, block: int) -> int:
    data = "0x70a08231" + holder.lower().replace("0x", "").rjust(64, "0")
    raw = rpc_call(chain_id, "eth_call", [{"to": token, "data": data}, hex(block)])
    return int(raw, 16) if raw and raw != "0x" else 0


def load_eth_price_series() -> list[tuple]:
    if ETH_PRICE_CACHE.exists():
        return [tuple(p) for p in json.loads(ETH_PRICE_CACHE.read_text())]
    raise RuntimeError("ETH price series missing — run the preparation step")


def collateral_series(chain_id: int, address: str) -> list[tuple]:
    matches = sorted(PRICE_CACHE.glob(f"{chain_id}_{address.lower()}_*.json"))
    if not matches:
        raise RuntimeError(f"price cache missing for {address} (chain {chain_id})")
    return [tuple(p) for p in json.loads(matches[0].read_text())]


def main() -> int:
    windows = list(csv.DictReader((RESULTS / "warning_windows_v1.csv").open()))
    extraction = {
        r["tx_hash"]: r
        for r in csv.DictReader(
            (RESULTS / "liquidations_morpho_api_2026-01-25_2026-02-10.csv").open()
        )
    }
    eth_series = load_eth_price_series()

    out, n = [], len(windows)
    for i, w in enumerate(windows, 1):
        ext = extraction[w["tx_hash"]]
        chain_id = int(ext["chain_id"])
        borrower = w["borrower"]
        alert_ts = int(w["alert_ts"]) if w["alert_ts"] else int(w["timestamp"]) - 6 * 3600
        debt_usd = float(w["repaid_usd"])

        block = block_at_or_before(chain_id, alert_ts)

        native_wei = int(rpc_call(chain_id, "eth_getBalance", [borrower, hex(block)]), 16)
        eth_price = price_at_or_before(eth_series, alert_ts) or 0.0
        native_usd = native_wei / 1e18 * eth_price
        had_gas = native_usd > GAS_MIN_USD

        is_contract = rpc_call(chain_id, "eth_getCode", [borrower, hex(block)]) not in ("0x", None)

        # curable tokens: market collateral + loan token + stables (deduped by address)
        coll_addr = ext["collateral_address"]
        coll_dec = int(ext["collateral_decimals"])
        tokens = {coll_addr.lower(): ("collateral", coll_addr, coll_dec)}
        for sym, (addr, dec) in STABLES[chain_id].items():
            tokens.setdefault(addr.lower(), (sym, addr, dec))

        curable_usd = 0.0
        for label, addr, dec in tokens.values():
            bal = erc20_balance(chain_id, addr, borrower, block)
            if bal == 0:
                continue
            units = bal / 10**dec
            if label == "collateral":
                price = price_at_or_before(collateral_series(chain_id, addr), alert_ts) or 0.0
            else:
                price = 1.0  # stablecoins (including the USDC loan)
            curable_usd += units * price

        had_capacity = had_gas and curable_usd >= CURE_FRACTION * debt_usd
        out.append(
            {
                "chain": w["chain"],
                "tx_hash": w["tx_hash"],
                "borrower": borrower,
                "market_id": w["market_id"],
                "alert_ts": alert_ts,
                "alert_block": block,
                "is_contract": is_contract,
                "native_usd": round(native_usd, 2),
                "had_gas": had_gas,
                "curable_usd": round(curable_usd, 2),
                "debt_usd": round(debt_usd, 2),
                "cure_threshold_usd": round(CURE_FRACTION * debt_usd, 2),
                "had_capacity": had_capacity,
            }
        )
        print(f"  {i}/{n} {w['chain']} {borrower[:10]}… block {block} "
              f"gas={'Y' if had_gas else 'N'} curable=${curable_usd:,.0f} "
              f"debt=${debt_usd:,.0f} capacity={'YES' if had_capacity else 'NO'}")

    out_csv = RESULTS / "attribution_v1.csv"
    with out_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        writer.writeheader()
        writer.writerows(out)

    cap = [r for r in out if r["had_capacity"]]
    no_gas = sum(1 for r in out if not r["had_gas"])
    contracts = sum(1 for r in out if r["is_contract"])
    print("\n================ ATTRIBUTION v1 ================")
    print(f"positions: {len(out)}")
    print(f"WITH capacity to cure (addressable ceiling): {len(cap)}/{len(out)} "
          f"= {100 * len(cap) / len(out):.0f}%")
    print(f"WITHOUT capacity: {len(out) - len(cap)}/{len(out)} "
          f"= {100 * (len(out) - len(cap)) / len(out):.0f}%")
    print(f"  - no gas (native ≤ ${GAS_MIN_USD:.0f}): {no_gas}")
    print(f"  - contract wallets (gas via paymaster possible — proxy underestimates): {contracts}")
    if cap:
        med = statistics.median(r["curable_usd"] / r["debt_usd"] for r in cap)
        print(f"median curable/debt among those WITH capacity: {100 * med:.0f}%")
    print(f"CSV: {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

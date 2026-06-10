# SPDX-License-Identifier: BUSL-1.1
# Licensed Work: Morpho Risk Tooling — Quant Module. Ver LICENSE-BSL na raiz.
"""v1.1 da janela de aviso + preparação de dados do demo (último uso do backtest).

Mudanças vs. v1:
- lookback de 168h (vs. 48h) — para des-censurar a mediana;
- tamanho REAL da posição: ``position(marketId, borrower)`` e ``market(id)``
  lidos do contrato Morpho Blue no bloco imediatamente ANTERIOR à liquidação
  (RPC arquival). Dívida = borrowShares→assets (com shares/assets virtuais).
  Aproximação remanescente: tamanho tratado como constante no lookback.

Demo: 4 posições representativas → série horária de saúde nas ~72h antes da
liquidação, com hora do alerta (1º cruzamento de saúde < 1.10, walk-forward,
sem look-ahead) e hora da liquidação → results/demo_trajectories.json.

Selectors verificados por keccak local (o 4byte.directory retornou seletores
errados para estas assinaturas — não confiar nele sem verificação).

Uso:
    uv run python -m risk_model.demo_prep_v1_1
"""

import csv
import json
import statistics
import sys
import time
from datetime import UTC, datetime

from risk_model.attribution_v1 import block_at_or_before, rpc_call
from risk_model.warning_window_v1 import (
    ALERT_BUFFER,
    RESULTS,
    fetch_hourly_prices,
    price_at_or_before,
)

MORPHO = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"  # singleton (Ethereum e Base)
SEL_POSITION = "0x93c52062"  # position(bytes32,address)
SEL_MARKET = "0x5c60e39a"  # market(bytes32)
LOOKBACK_H = 168
DEMO_LOOKBACK_H = 72
RETAIL_DEBT_RANGE = (5_000.0, 150_000.0)


def tx_block(chain_id: int, tx_hash: str) -> int:
    # backends do balanceador às vezes respondem null para tx antigas — retry
    for attempt in range(6):
        tx = rpc_call(chain_id, "eth_getTransactionByHash", [tx_hash])
        if tx and tx.get("blockNumber"):
            return int(tx["blockNumber"], 16)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"tx não encontrada via RPC após retries: {tx_hash}")


def real_position(chain_id: int, market_id: str, borrower: str, block: int) -> tuple[int, int]:
    """(colateral_raw, dívida_raw em unidades do loan token) no bloco dado."""
    data = SEL_POSITION + market_id[2:] + borrower[2:].lower().rjust(64, "0")
    res = rpc_call(chain_id, "eth_call", [{"to": MORPHO, "data": data}, hex(block)])[2:]
    borrow_shares, collateral = int(res[64:128], 16), int(res[128:192], 16)
    mres = rpc_call(
        chain_id, "eth_call", [{"to": MORPHO, "data": SEL_MARKET + market_id[2:]}, hex(block)]
    )[2:]
    total_borrow_assets, total_borrow_shares = int(mres[128:192], 16), int(mres[192:256], 16)
    debt = borrow_shares * (total_borrow_assets + 1) // (total_borrow_shares + 10**6)
    return collateral, debt


def first_alert(units: float, debt_usd: float, lltv: float, series: list,
                liq_ts: int, lookback_h: int) -> int | None:
    """Walk-forward: 1ª hora t com units×preço(t)×LLTV < dívida×1.10. Sem look-ahead."""
    t0 = (liq_ts // 3600) * 3600 - lookback_h * 3600
    for t in range(t0, liq_ts + 1, 3600):
        p = price_at_or_before(series, t)
        if p is not None and units * p * lltv < debt_usd * ALERT_BUFFER:
            return t
    return None


def load_inputs() -> tuple[list[dict], dict[str, dict]]:
    windows = list(csv.DictReader((RESULTS / "warning_windows_v1.csv").open()))
    extraction = {
        r["tx_hash"]: r
        for r in csv.DictReader(
            (RESULTS / "liquidations_morpho_api_2026-01-25_2026-02-10.csv").open()
        )
    }
    return windows, extraction


def position_record(ext_row: dict) -> dict | None:
    """Lê tamanho real no bloco pré-liquidação; None se posição zerada/ilegível.

    O bloco da liquidação vem do timestamp (block_at_or_before) — o
    eth_getTransactionByHash dos RPCs públicos não tem txindex confiável."""
    chain_id = int(ext_row["chain_id"])
    blk = block_at_or_before(chain_id, int(ext_row["timestamp"]))
    coll_raw, debt_raw = real_position(
        chain_id, ext_row["market_id"], ext_row["borrower"], blk - 1
    )
    if coll_raw == 0 or debt_raw == 0:
        return None
    assert ext_row["loan_symbol"] == "USDC", f"loan não-USDC: {ext_row['loan_symbol']}"
    return {
        "chain_id": chain_id,
        "liq_block": blk,
        "units": coll_raw / 10 ** int(ext_row["collateral_decimals"]),
        "debt_usd": debt_raw / 1e6,  # USDC ≈ USD
    }


def main() -> int:
    windows, extraction = load_inputs()

    # séries de preço com range largo o bastante para 168h de lookback
    all_liq = [int(w["timestamp"]) for w in windows]
    t_from = min(all_liq) - (LOOKBACK_H + 2) * 3600
    t_to = max(all_liq) + 3600
    series: dict[tuple, list] = {}
    for w in windows:
        e = extraction[w["tx_hash"]]
        key = (int(e["chain_id"]), e["collateral_address"].lower())
        if key not in series:
            series[key] = fetch_hourly_prices(key[0], key[1], t_from, t_to)

    print(f"v1.1: lookback {LOOKBACK_H}h, tamanho real — {len(windows)} posições")
    rows_v11 = []
    for i, w in enumerate(windows, 1):
        e = extraction[w["tx_hash"]]
        pos = position_record(e)
        if pos is None:
            print(f"  {i}: posição ilegível em {w['tx_hash'][:12]}… — pulada")
            continue
        liq_ts = int(w["timestamp"])
        key = (pos["chain_id"], e["collateral_address"].lower())
        alert = first_alert(pos["units"], pos["debt_usd"], float(w["lltv"]),
                            series[key], liq_ts, LOOKBACK_H)
        t0 = (liq_ts // 3600) * 3600 - LOOKBACK_H * 3600
        window_h = (liq_ts - alert) / 3600 if alert is not None else 0.0
        rows_v11.append({
            "chain": w["chain"], "tx_hash": w["tx_hash"], "borrower": w["borrower"],
            "market_id": w["market_id"], "collateral_symbol": e["collateral_symbol"],
            "lltv": w["lltv"], "liq_ts": liq_ts,
            "real_collateral_units": round(pos["units"], 8),
            "real_debt_usd": round(pos["debt_usd"], 2),
            "alert_ts": alert, "window_hours": round(window_h, 2),
            "censored_168h": alert == t0, "no_alert": alert is None,
        })

    out_csv = RESULTS / "warning_windows_v1_1.csv"
    with out_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows_v11[0].keys()))
        writer.writeheader()
        writer.writerows(rows_v11)

    ws = sorted(r["window_hours"] for r in rows_v11)
    n = len(ws)
    q = statistics.quantiles(ws, n=4)
    ge2 = sum(1 for x in ws if x >= 2)
    cens = sum(1 for r in rows_v11 if r["censored_168h"])
    noal = sum(1 for r in rows_v11 if r["no_alert"])
    print("\n========== JANELA v1.1 (168h, tamanho real) ==========")
    print(f"posições: {n} | mediana: {statistics.median(ws):.1f} h")
    print(f"mín/Q1/Q2/Q3/máx: {ws[0]:.1f} / {q[0]:.1f} / {q[1]:.1f} / {q[2]:.1f} / {ws[-1]:.1f} h")
    print(f"≥ 2h: {ge2}/{n} = {100 * ge2 / n:.0f}% | "
          f"censuradas em 168h: {cens} | sem alerta: {noal}")
    print(f"CSV: {out_csv}")

    # ---------------- demo: 4 trajetórias ----------------
    print("\nSelecionando 4 posições para o demo…")
    attribution = {r["tx_hash"]: r for r in csv.DictReader((RESULTS / "attribution_v1.csv").open())}

    demo_rows: list[tuple[str, dict]] = []
    # 2 varejo EOA na Base (fora da amostra grande): cbBTC/USDC, dívida 5k–150k
    full = list(csv.DictReader(
        (RESULTS / "liquidations_morpho_api_2026-01-25_2026-02-10.csv").open()
    ))
    lo, hi = RETAIL_DEBT_RANGE
    retail_pool = sorted(
        (r for r in full
         if r["chain"] == "base" and r["loan_symbol"] == "USDC"
         and r["collateral_symbol"] == "cbBTC"
         and r["repaid_usd"] and lo <= float(r["repaid_usd"]) <= hi),
        key=lambda r: float(r["repaid_usd"]), reverse=True,
    )
    seen, found = set(), 0
    for r in retail_pool:
        if found == 2:
            break
        if r["borrower"] in seen:
            continue
        seen.add(r["borrower"])
        code = rpc_call(8453, "eth_getCode", [r["borrower"], "latest"])
        if code not in ("0x", None):
            continue  # contrato — queremos EOA/varejo
        demo_rows.append(("varejo EOA (Base)", r))
        found += 1

    # 1 institucional contrato na Base + 1 Ethereum (wstETH) da amostra
    base_inst = next(w for w in windows
                     if w["chain"] == "base"
                     and attribution[w["tx_hash"]]["is_contract"] == "True")
    eth_pick = next(w for w in windows
                    if w["chain"] == "ethereum"
                    and extraction[w["tx_hash"]]["collateral_symbol"] == "wstETH")
    demo_rows.append(("institucional contrato (Base)", extraction[base_inst["tx_hash"]]))
    demo_rows.append(("institucional (Ethereum, wstETH)", extraction[eth_pick["tx_hash"]]))

    trajectories = []
    for label, e in demo_rows:
        chain_id = int(e["chain_id"])
        pos = position_record(e)
        if pos is None:
            print(f"  AVISO: posição do demo ilegível ({label}) — pulada")
            continue
        liq_ts = int(e["timestamp"])
        key = (chain_id, e["collateral_address"].lower())
        if key not in series:
            series[key] = fetch_hourly_prices(key[0], key[1], t_from, t_to)
        lltv = float(e["lltv"])
        alert = first_alert(pos["units"], pos["debt_usd"], lltv, series[key],
                            liq_ts, DEMO_LOOKBACK_H)
        t0 = (liq_ts // 3600) * 3600 - DEMO_LOOKBACK_H * 3600
        pts = []
        for t in range(t0, liq_ts + 1, 3600):
            p = price_at_or_before(series[key], t)
            if p is None:
                continue
            health = pos["units"] * p * lltv / pos["debt_usd"]
            pts.append({
                "ts": t,
                "iso": datetime.fromtimestamp(t, tz=UTC).isoformat(),
                "health": round(health, 4),
                "collateral_price_usd": round(p, 2),
            })
        window_h = (liq_ts - alert) / 3600 if alert is not None else 0.0
        trajectories.append({
            "label": label,
            "chain": e["chain"],
            "tx_hash": e["tx_hash"],
            "borrower": e["borrower"],
            "market_id": e["market_id"],
            "collateral_symbol": e["collateral_symbol"],
            "loan_symbol": e["loan_symbol"],
            "lltv": lltv,
            "real_collateral_units": round(pos["units"], 8),
            "real_debt_usd": round(pos["debt_usd"], 2),
            "alert_ts": alert,
            "alert_iso": datetime.fromtimestamp(alert, tz=UTC).isoformat() if alert else None,
            "liquidation_ts": liq_ts,
            "liquidation_iso": datetime.fromtimestamp(liq_ts, tz=UTC).isoformat(),
            "window_hours": round(window_h, 2),
            "alert_rule": "primeira hora com saúde < 1.10 (buffer 10%), walk-forward",
            "approximations": [
                "tamanho real lido no bloco pré-liquidação, constante no lookback",
                "preço CoinGecko horário como proxy do oráculo",
                "dívida USDC tratada como US$ 1:1",
            ],
            "series": pts,
        })

    out_json = RESULTS / "demo_trajectories.json"
    out_json.write_text(json.dumps(trajectories, indent=2, ensure_ascii=False))
    print(f"\n========== DEMO ({len(trajectories)} trajetórias) ==========")
    for t in trajectories:
        print(f"  [{t['label']}] {t['collateral_symbol']}/{t['loan_symbol']} "
              f"dívida=${t['real_debt_usd']:,.0f} janela={t['window_hours']:.1f}h "
              f"({t['chain']}, {t['borrower'][:10]}…)")
    print(f"JSON: {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

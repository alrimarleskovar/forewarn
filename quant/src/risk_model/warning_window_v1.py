# SPDX-License-Identifier: BUSL-1.1
# Licensed Work: Morpho Risk Tooling — Quant Module. Ver LICENSE-BSL na raiz.
"""Medição v1 da janela de aviso de liquidação — walk-forward, SEM look-ahead.

Pipeline: liquidações via API GraphQL oficial da Morpho (Ethereum + Base,
25/jan–10/fev/2026) → amostra de ~40 (alocação por chain proporcional ao
volume USD; dentro da chain, maiores por repaidAssetsUsd, dedupe por
posição) → série de preço HORÁRIA do colateral via CoinGecko → walk-forward
hora a hora.

Regra de alerta (avaliada só com estado conhecido até t — INVIOLÁVEL):
    alerta na primeira hora t em que
        colateral_units × preço(t) × LLTV < dívida_usd × 1.10
    janela = hora_da_liquidação − hora_do_alerta.

Aproximações da v1 (documentadas):
- Tamanho da posição ≈ seizedAssets / repaidAssets do PRÓPRIO evento de
  liquidação. Liquidações parciais subestimam a posição; o viés é
  conservador e simétrico entre numerador (colateral) e denominador (dívida).
- Dívida em USD tratada como CONSTANTE = repaidAssetsUsd no momento da
  liquidação (loans da amostra são majoritariamente stablecoins; para loan
  volátil isto é proxy).
- Preço do colateral: série horária da CoinGecko em USD — PROXY do oráculo
  real do market (cada market Morpho tem oráculo próprio).
- Scan começa 48h antes da liquidação → janelas são CENSURADAS em 48h
  (posição já abaixo do limiar em t0 reporta 48h).
- Sem cruzamento até a liquidação → janela = 0 (nenhum aviso teria saído).

Uso:
    uv run python -m risk_model.warning_window_v1
"""

import csv
import json
import math
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

MORPHO_API = "https://blue-api.morpho.org/graphql"
COINGECKO_API = "https://api.coingecko.com/api/v3"
CG_PLATFORM = {1: "ethereum", 8453: "base"}
CHAIN_NAME = {1: "ethereum", 8453: "base"}

T_START = int(datetime(2026, 1, 25, tzinfo=UTC).timestamp())
T_END = int(datetime(2026, 2, 11, tzinfo=UTC).timestamp())  # exclusivo
SAMPLE_SIZE = 40
LOOKBACK_HOURS = 48
ALERT_BUFFER = 1.10
PAGE = 1000

REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS = REPO_ROOT / "results"
PRICE_CACHE = RESULTS / "prices"

TX_QUERY = """
query ($first: Int!, $skip: Int!) {
  transactions(
    first: $first, skip: $skip,
    where: { type_in: [MarketLiquidation], timestamp_gte: T_START, timestamp_lte: T_END,
             chainId_in: [1, 8453] },
    orderBy: Timestamp, orderDirection: Asc
  ) {
    pageInfo { countTotal }
    items {
      hash timestamp chain { id } user { address }
      data { ... on MarketLiquidationTransactionData {
        seizedAssets repaidAssets badDebtAssets seizedAssetsUsd repaidAssetsUsd
        market { marketId lltv
          collateralAsset { address symbol decimals }
          loanAsset { address symbol decimals } }
      } }
    }
  }
}
""".replace("T_START", str(T_START)).replace("T_END", str(T_END - 1))


def fetch_all_liquidations() -> list[dict]:
    rows, skip = [], 0
    while True:
        resp = requests.post(
            MORPHO_API,
            json={"query": TX_QUERY, "variables": {"first": PAGE, "skip": skip}},
            timeout=60,
        )
        resp.raise_for_status()
        payload = resp.json()
        if "errors" in payload:
            raise RuntimeError(f"Morpho API: {payload['errors']}")
        tx = payload["data"]["transactions"]
        for it in tx["items"]:
            d = it["data"] or {}
            mkt = d.get("market") or {}
            coll, loan = mkt.get("collateralAsset"), mkt.get("loanAsset")
            if not (coll and loan):
                continue
            rows.append(
                {
                    "chain": CHAIN_NAME[it["chain"]["id"]],
                    "chain_id": it["chain"]["id"],
                    "tx_hash": it["hash"],
                    "timestamp": it["timestamp"],
                    "borrower": it["user"]["address"],
                    "market_id": mkt["marketId"],
                    "lltv": int(mkt["lltv"]) / 1e18,
                    "collateral_symbol": coll["symbol"],
                    "collateral_address": coll["address"],
                    "collateral_decimals": coll["decimals"],
                    "loan_symbol": loan["symbol"],
                    "seized_assets": int(d["seizedAssets"]),
                    "repaid_assets": int(d["repaidAssets"]),
                    "bad_debt_assets": int(d.get("badDebtAssets") or 0),
                    "seized_usd": d.get("seizedAssetsUsd"),
                    "repaid_usd": d.get("repaidAssetsUsd"),
                }
            )
        skip += PAGE
        if skip >= tx["pageInfo"]["countTotal"]:
            return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def pick_sample(rows: list[dict], n: int = SAMPLE_SIZE) -> list[dict]:
    """Aloca n por chain proporcional ao volume USD repago; dentro da chain,
    maiores por repaid_usd, no máximo 1 evento por (market, borrower)."""
    usable = [r for r in rows if r["repaid_usd"] and r["seized_usd"]]
    vol = {c: sum(r["repaid_usd"] for r in usable if r["chain"] == c) for c in ("ethereum", "base")}
    total = sum(vol.values())
    quota = {c: max(2, round(n * v / total)) for c, v in vol.items()}
    while sum(quota.values()) != n:
        biggest = max(quota, key=lambda c: quota[c])
        quota[biggest] += n - sum(quota.values())

    sample = []
    for c, q in quota.items():
        seen_positions = set()
        ranked = sorted(
            (r for r in usable if r["chain"] == c), key=lambda r: r["repaid_usd"], reverse=True
        )
        picked = []
        for r in ranked:
            key = (r["market_id"], r["borrower"])
            if key in seen_positions:
                continue
            seen_positions.add(key)
            picked.append(r)
            if len(picked) == q:
                break
        sample.extend(picked)
    return sample


def fetch_hourly_prices(chain_id: int, address: str, t_from: int, t_to: int) -> list[tuple]:
    """Série horária [(ts_segundos, preço_usd)] via CoinGecko, com cache em disco.

    Levanta RuntimeError com mensagem clara em caso de bloqueio (429/401/404)."""
    PRICE_CACHE.mkdir(parents=True, exist_ok=True)
    cache = PRICE_CACHE / f"{chain_id}_{address.lower()}_{t_from}_{t_to}.json"
    if cache.exists():
        return [tuple(p) for p in json.loads(cache.read_text())]

    url = (
        f"{COINGECKO_API}/coins/{CG_PLATFORM[chain_id]}/contract/{address.lower()}"
        f"/market_chart/range?vs_currency=usd&from={t_from}&to={t_to}"
    )
    for attempt in range(6):
        resp = requests.get(url, timeout=60)
        if resp.status_code == 429:
            wait = 20 * (attempt + 1)
            print(f"  CoinGecko 429; aguardando {wait}s…", file=sys.stderr)
            time.sleep(wait)
            continue
        if resp.status_code == 404:
            raise LookupError(f"CoinGecko sem série para {address} em {CG_PLATFORM[chain_id]}")
        if resp.status_code in (401, 403):
            raise RuntimeError(f"CoinGecko bloqueou ({resp.status_code}): {resp.text[:200]}")
        resp.raise_for_status()
        prices = [(int(ts // 1000), float(p)) for ts, p in resp.json().get("prices", [])]
        if not prices:
            raise LookupError(f"CoinGecko retornou série vazia para {address}")
        cache.write_text(json.dumps(prices))
        time.sleep(2.5)  # cortesia com o rate limit público
        return prices
    raise RuntimeError("CoinGecko: rate limit persistente (429) após 6 tentativas")


def price_at_or_before(series: list[tuple], t: int) -> float | None:
    """Último preço com timestamp ≤ t. NUNCA olha à frente de t."""
    candidate = None
    for ts, p in series:
        if ts <= t:
            candidate = p
        else:
            break
    return candidate


def walk_forward(row: dict, series: list[tuple]) -> dict:
    liq_ts = row["timestamp"]
    units = row["seized_assets"] / 10 ** row["collateral_decimals"]
    debt_usd = row["repaid_usd"]
    lltv = row["lltv"]

    t0 = (liq_ts // 3600) * 3600 - LOOKBACK_HOURS * 3600
    alert_ts = None
    for t in range(t0, liq_ts + 1, 3600):
        p = price_at_or_before(series, t)
        if p is None:
            continue  # sem preço conhecido até t — não decide nada
        if units * p * lltv < debt_usd * ALERT_BUFFER:
            alert_ts = t
            break

    window_h = (liq_ts - alert_ts) / 3600 if alert_ts is not None else 0.0
    return {
        **{k: row[k] for k in (
            "chain", "tx_hash", "timestamp", "borrower", "market_id",
            "collateral_symbol", "loan_symbol", "lltv", "repaid_usd", "seized_usd",
        )},
        "alert_ts": alert_ts,
        "window_hours": round(window_h, 2),
        "censored_48h": alert_ts == t0,
        "no_alert": alert_ts is None,
    }


def main() -> int:
    print("1/4 Buscando liquidações na API da Morpho…")
    rows = fetch_all_liquidations()
    full_csv = RESULTS / "liquidations_morpho_api_2026-01-25_2026-02-10.csv"
    write_csv(full_csv, rows)
    by_chain = {c: sum(1 for r in rows if r["chain"] == c) for c in ("ethereum", "base")}
    print(f"   {len(rows)} liquidações ({by_chain}); CSV completo: {full_csv}")

    print("2/4 Amostrando…")
    sample = pick_sample(rows)
    print(f"   amostra: {len(sample)} "
          f"({ {c: sum(1 for r in sample if r['chain'] == c) for c in ('ethereum', 'base')} })")

    print("3/4 Preços horários (CoinGecko)…")
    tokens = sorted({(r["chain_id"], r["collateral_address"].lower()) for r in sample})
    t_from = min(r["timestamp"] for r in sample) - (LOOKBACK_HOURS + 2) * 3600
    t_to = max(r["timestamp"] for r in sample) + 3600
    series_by_token: dict[tuple, list] = {}
    dropped: list[str] = []
    for chain_id, addr in tokens:
        sym = next(r["collateral_symbol"] for r in sample
                   if r["collateral_address"].lower() == addr)
        try:
            series_by_token[(chain_id, addr)] = fetch_hourly_prices(chain_id, addr, t_from, t_to)
            print(f"   ok: {sym} ({CHAIN_NAME[chain_id]})")
        except LookupError as exc:
            dropped.append(f"{sym} ({CHAIN_NAME[chain_id]}): {exc}")
            print(f"   SEM SÉRIE: {sym} ({CHAIN_NAME[chain_id]}) — posições descartadas")

    print("4/4 Walk-forward…")
    results = []
    for r in sample:
        key = (r["chain_id"], r["collateral_address"].lower())
        if key not in series_by_token:
            continue
        results.append(walk_forward(r, series_by_token[key]))
    out_csv = RESULTS / "warning_windows_v1.csv"
    write_csv(out_csv, results)

    windows = sorted(x["window_hours"] for x in results)
    n = len(windows)
    q = statistics.quantiles(windows, n=4) if n >= 4 else [float("nan")] * 3
    ge2 = sum(1 for w in windows if w >= 2)
    no_alert = sum(1 for x in results if x["no_alert"])
    censored = sum(1 for x in results if x["censored_48h"])
    print("\n================ RESULTADO v1 ================")
    print(f"posições analisadas: {n} (descartadas sem série de preço: {len(sample) - n})")
    if dropped:
        print("  tokens sem série: " + "; ".join(dropped))
    print(f"janela mediana: {statistics.median(windows):.1f} h")
    print(f"mín/Q1/Q2/Q3/máx: {windows[0]:.1f} / {q[0]:.1f} / {q[1]:.1f} / "
          f"{q[2]:.1f} / {windows[-1]:.1f} h")
    print(f"fração com janela ≥ 2h: {ge2}/{n} = {100 * ge2 / n:.0f}%")
    print(f"sem alerta antes da liquidação (janela=0): {no_alert} | censuradas em 48h: {censored}")
    print(f"CSV: {out_csv}")
    if math.isnan(q[0]):
        print("AVISO: n < 4, quartis não calculados")
    return 0


if __name__ == "__main__":
    sys.exit(main())

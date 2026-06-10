# SPDX-License-Identifier: BUSL-1.1
# Licensed Work: Morpho Risk Tooling — Quant Module. Ver LICENSE-BSL na raiz.
"""Dashboard público v0 — HTML estático gerado de results/at_risk_snapshot.json.

Página única, sem JS externo nem backend: manchete (dívida na zona de aviso),
métricas por mercado, top-15 posições críticas com link pro explorer,
distribuição de saúde e rodapé de método/ressalvas.

Uso:
    uv run python -m risk_model.dashboard_v0
"""

import json
import sys
from datetime import UTC, datetime

from risk_model.warning_window_v1 import RESULTS

EXPLORER = {"ethereum": "https://etherscan.io/address/", "base": "https://basescan.org/address/"}
BANDS = [(1.00, 1.03, "1.00–1.03"), (1.03, 1.06, "1.03–1.06"), (1.06, 1.10, "1.06–1.10")]
TOP_N = 15


def fmt_usd(v: float) -> str:
    if v >= 1e6:
        return f"${v / 1e6:,.2f}M"
    return f"${v:,.0f}"


def render(snapshot: dict) -> str:
    pos = snapshot["positions"]
    risk = [p for p in pos if p["at_risk"]]
    risk_debt = sum(p["debt_usd"] for p in risk)
    ts = datetime.fromtimestamp(snapshot["snapshot_ts"], tz=UTC).strftime("%b %d, %Y %H:%M UTC")
    blocks = " · ".join(
        f"{m['chain']} block {m['block']:,}" for m in snapshot["markets"]
    )

    market_rows = ""
    for m in snapshot["markets"]:
        mp = [p for p in pos if p["market_id"] == m["market_id"]]
        mr = [p for p in mp if p["at_risk"]]
        market_rows += f"""
        <tr>
          <td><strong>{m['label']}</strong> <span class="chip">{m['chain']}</span></td>
          <td class="num">{m['active_positions']:,}</td>
          <td class="num">{len(mp):,}</td>
          <td class="num warn">{len(mr):,}</td>
          <td class="num warn">{fmt_usd(sum(p['debt_usd'] for p in mr))}</td>
        </tr>"""

    top_rows = ""
    for p in sorted(risk, key=lambda x: x["health"])[:TOP_N]:
        short = p["borrower"][:6] + "…" + p["borrower"][-4:]
        top_rows += f"""
        <tr>
          <td class="num crit">{p['health']:.4f}</td>
          <td class="num">+{p['distance_to_threshold_pct']:.1f}%</td>
          <td class="num">{fmt_usd(p['debt_usd'])}</td>
          <td>{p['market']}</td>
          <td><span class="chip">{p['chain']}</span></td>
          <td class="mono"><a href="{EXPLORER[p['chain']]}{p['borrower']}"
              target="_blank" rel="noopener">{short}</a></td>
        </tr>"""

    band_html = ""
    max_count = max(
        sum(1 for p in risk if lo <= p["health"] < hi) for lo, hi, _ in BANDS
    ) or 1
    for lo, hi, label in BANDS:
        in_band = [p for p in risk if lo <= p["health"] < hi]
        pct_width = 100 * len(in_band) / max_count
        band_debt = fmt_usd(sum(p["debt_usd"] for p in in_band))
        band_html += f"""
        <div class="band">
          <div class="band-label">{label}</div>
          <div class="band-track">
            <div class="band-fill" style="width:{pct_width:.0f}%"></div>
          </div>
          <div class="band-meta">{len(in_band):,} positions · {band_debt}</div>
        </div>"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Morpho Liquidation Early-Warning — Live Risk Snapshot</title>
<style>
  :root {{
    --bg: #0c0f14; --panel: #141923; --line: #232b3a;
    --text: #e8edf4; --dim: #8b97a8; --accent: #ffb454; --crit: #ff6b6b;
  }}
  * {{ box-sizing: border-box; margin: 0; }}
  body {{
    background: var(--bg); color: var(--text);
    font: 16px/1.55 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    padding: 48px 20px 64px;
  }}
  .wrap {{ max-width: 880px; margin: 0 auto; }}
  .kicker {{
    color: var(--accent); font-size: 13px; font-weight: 600;
    letter-spacing: .12em; text-transform: uppercase; margin-bottom: 12px;
  }}
  h1 {{ font-size: clamp(28px, 5vw, 40px); line-height: 1.15; letter-spacing: -.01em; }}
  h1 .hl {{ color: var(--accent); }}
  .sub {{ color: var(--dim); margin-top: 10px; font-size: 14px; }}
  h2 {{ font-size: 15px; letter-spacing: .08em; text-transform: uppercase;
       color: var(--dim); margin: 44px 0 14px; }}
  table {{ width: 100%; border-collapse: collapse; background: var(--panel);
          border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }}
  th, td {{ padding: 10px 14px; text-align: left; font-size: 14px; }}
  th {{ color: var(--dim); font-weight: 600; font-size: 12px;
       text-transform: uppercase; letter-spacing: .06em;
       border-bottom: 1px solid var(--line); }}
  tr + tr td {{ border-top: 1px solid var(--line); }}
  .num {{ font-variant-numeric: tabular-nums; text-align: right; }}
  th.num {{ text-align: right; }}
  .warn {{ color: var(--accent); font-weight: 600; }}
  .crit {{ color: var(--crit); font-weight: 700; }}
  .chip {{ display: inline-block; padding: 1px 8px; border-radius: 999px;
          font-size: 11px; font-weight: 600; background: #1d2535; color: var(--dim);
          text-transform: uppercase; letter-spacing: .05em; }}
  .mono {{ font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: 13px; }}
  a {{ color: #7fb4ff; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .band {{ display: grid; grid-template-columns: 90px 1fr 220px; gap: 14px;
          align-items: center; padding: 10px 14px; background: var(--panel);
          border: 1px solid var(--line); border-radius: 10px; margin-bottom: 8px; }}
  .band-label {{ font-variant-numeric: tabular-nums; font-weight: 600; font-size: 14px; }}
  .band-track {{ background: #1d2535; border-radius: 6px; height: 14px; }}
  .band-fill {{ background: linear-gradient(90deg, var(--accent), var(--crit));
               height: 100%; border-radius: 6px; min-width: 2px; }}
  .band-meta {{ color: var(--dim); font-size: 13px; text-align: right;
               font-variant-numeric: tabular-nums; }}
  footer {{ margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--line);
           color: var(--dim); font-size: 13px; }}
  footer ul {{ margin: 8px 0 0 18px; }}
  footer li {{ margin-bottom: 4px; }}
  @media (max-width: 640px) {{
    .band {{ grid-template-columns: 80px 1fr; }}
    .band-meta {{ grid-column: 1 / -1; text-align: left; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="kicker">Morpho Blue · Liquidation Early-Warning · Live Snapshot v0</div>
  <h1><span class="hl">{fmt_usd(risk_debt)}</span> of debt is inside the 10% warning
      buffer across <span class="hl">{len(risk):,}</span> positions</h1>
  <div class="sub">Snapshot {ts} · {blocks} · health read on-chain from each
      market's own oracle · warning rule: health &lt; 1.10</div>

  <h2>Markets monitored</h2>
  <table>
    <tr><th>Market</th><th class="num">Active</th><th class="num">Verified on-chain</th>
        <th class="num">At risk</th><th class="num">Debt at risk</th></tr>
    {market_rows}
  </table>

  <h2>Most critical positions</h2>
  <table>
    <tr><th class="num">Health</th><th class="num">To threshold</th><th class="num">Debt</th>
        <th>Market</th><th>Chain</th><th>Borrower</th></tr>
    {top_rows}
  </table>

  <h2>Health distribution of at-risk positions</h2>
  {band_html}

  <footer>
    <strong>Method.</strong> Borrowers enumerated via the official Morpho API; every
    position then verified on-chain at a pinned block per chain (Multicall3 batched
    <span class="mono">position()</span> reads). Health = collateral × oracle price ×
    LLTV ÷ debt, using each market's own oracle (<span class="mono">price()</span>,
    1e36 scale) — the same engine validated on the Feb 2026 liquidation backtest.
    <ul>
      <li>Single snapshot — not a continuously updating feed yet.</li>
      <li>Coverage: 2 markets (Base cbBTC/USDC, Ethereum wstETH/USDC).</li>
      <li>Positions with debt &lt; $1,000 excluded from ranking unless API health ≤ 1.3
          (cutoffs logged in the snapshot metadata).</li>
      <li>USDC valued at $1.00.</li>
      <li>Informational only — not financial advice, no execution, no custody.</li>
    </ul>
  </footer>
</div>
</body>
</html>
"""


def main() -> int:
    snapshot = json.loads((RESULTS / "at_risk_snapshot.json").read_text())
    out = RESULTS / "dashboard.html"
    out.write_text(render(snapshot))
    risk = [p for p in snapshot["positions"] if p["at_risk"]]
    print(f"dashboard: {out}")
    print(f"  {len(risk):,} posições em risco | {fmt_usd(sum(p['debt_usd'] for p in risk))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# SPDX-License-Identifier: BUSL-1.1
# Licensed Work: Morpho Risk Tooling — Quant Module. See LICENSE-BSL at the repo root.
"""Public dashboard v0 — static HTML generated from results/at_risk_snapshot.json.

Single page, no external JS or backend: headline (debt inside the warning
zone), per-market metrics, top-15 critical positions with explorer links,
health distribution and a method/caveats footer.

Usage:
    uv run python -m risk_model.dashboard_v0
"""

import json
import sys
from datetime import UTC, datetime

from risk_model.live_monitor_v1 import classify_market
from risk_model.warning_window_v1 import REPO_ROOT, RESULTS

# Fill in after publishing the research. Empty = link omitted.
METHODOLOGY_URL = ""
CODE_URL = "https://github.com/alrimarleskovar/forewarn"

EXPLORER = {"ethereum": "https://etherscan.io/address/", "base": "https://basescan.org/address/"}
BANDS = [(1.00, 1.03, "1.00–1.03"), (1.03, 1.06, "1.03–1.06"), (1.06, 1.10, "1.06–1.10")]
TOP_N = 15


def fmt_usd(v: float) -> str:
    if v >= 1e6:
        return f"${v / 1e6:,.2f}M"
    return f"${v:,.0f}"


def render(snapshot: dict) -> str:
    pos = snapshot["positions"]
    ts = datetime.fromtimestamp(snapshot["snapshot_ts"], tz=UTC).strftime("%b %d, %Y %H:%M UTC")
    n_markets = snapshot.get("n_markets", len(snapshot["markets"]))
    blocks = " · ".join(
        f"{chain} block {block:,}"
        for chain, block in sorted({(m["chain"], m["block"]) for m in snapshot["markets"]})
    )

    # bucket: uses the snapshot's stamp (v1.2, with peg-check); 2-way fallback by label
    corr_by_market: dict[str, str] = {}
    for m in snapshot["markets"]:
        c = m.get("bucket") or m.get("correlation")
        if not c:
            c, _ = classify_market(*m["label"].split("/", 1))
        corr_by_market[m["market_id"]] = c

    risk = [p for p in pos if p["at_risk"]]
    dir_risk = [p for p in risk if corr_by_market[p["market_id"]] == "directional"]
    cor_risk = [p for p in risk if corr_by_market[p["market_id"]] == "correlated"]
    anom_risk = [p for p in risk if corr_by_market[p["market_id"]] == "anomalous"]
    dir_debt = sum(p["debt_usd"] for p in dir_risk)
    cor_debt = sum(p["debt_usd"] for p in cor_risk)
    anom_debt = sum(p["debt_usd"] for p in anom_risk)

    per_market = []
    for m in snapshot["markets"]:
        mp = [p for p in pos if p["market_id"] == m["market_id"]]
        mr = [p for p in mp if p["at_risk"]]
        per_market.append((m, mp, mr, sum(p["debt_usd"] for p in mr)))
    per_market.sort(key=lambda x: x[3], reverse=True)
    dir_markets = [x for x in per_market if corr_by_market[x[0]["market_id"]] == "directional"]
    cor_markets = [x for x in per_market if corr_by_market[x[0]["market_id"]] == "correlated"]
    anom_markets = [x for x in per_market if corr_by_market[x[0]["market_id"]] == "anomalous"]

    market_rows = ""
    top_markets = dir_markets[:10]
    for m, mp, mr, mr_debt in top_markets:
        market_rows += f"""
        <tr>
          <td><strong>{m['label']}</strong> <span class="chip">{m['chain']}</span></td>
          <td class="num">{m['active_positions']:,}</td>
          <td class="num">{len(mp):,}</td>
          <td class="num warn">{len(mr):,}</td>
          <td class="num warn">{fmt_usd(mr_debt)}</td>
        </tr>"""
    rest = dir_markets[10:]
    if rest:
        market_rows += f"""
        <tr>
          <td><em>+ {len(rest)} more directional markets</em></td>
          <td class="num">{sum(m['active_positions'] for m, *_ in rest):,}</td>
          <td class="num">{sum(len(mp) for _, mp, _, _ in rest):,}</td>
          <td class="num warn">{sum(len(mr) for *_, mr, _ in rest):,}</td>
          <td class="num warn">{fmt_usd(sum(d for *_, d in rest))}</td>
        </tr>"""

    cor_rows = ""
    for m, mp, mr, mr_debt in cor_markets[:5]:
        cor_rows += f"""
        <tr>
          <td><strong>{m['label']}</strong> <span class="chip">{m['chain']}</span></td>
          <td class="num">{len(mp):,}</td>
          <td class="num">{len(mr):,}</td>
          <td class="num">{fmt_usd(mr_debt)}</td>
        </tr>"""
    cor_rest = cor_markets[5:]
    if cor_rest:
        cor_rows += f"""
        <tr>
          <td><em>+ {len(cor_rest)} more correlated markets</em></td>
          <td class="num">{sum(len(mp) for _, mp, _, _ in cor_rest):,}</td>
          <td class="num">{sum(len(mr) for *_, mr, _ in cor_rest):,}</td>
          <td class="num">{fmt_usd(sum(d for *_, d in cor_rest))}</td>
        </tr>"""

    anom_rows = ""
    for m, mp, mr, mr_debt in anom_markets:
        depegs = ", ".join(
            f"{d['symbol']} ${d['price_usd']:.3f}" if d.get("price_usd") is not None
            else f"{d['symbol']} (no price)"
            for d in m.get("depegged_assets", [])
        ) or "—"
        anom_rows += f"""
        <tr>
          <td><strong>{m['label']}</strong> <span class="chip">{m['chain']}</span></td>
          <td class="crit">{depegs}</td>
          <td class="num">{len(mp):,}</td>
          <td class="num">{len(mr):,}</td>
          <td class="num">{fmt_usd(mr_debt)}</td>
        </tr>"""

    top_rows = ""
    for p in sorted(dir_risk, key=lambda x: x["health"])[:TOP_N]:
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
        sum(1 for p in dir_risk if lo <= p["health"] < hi) for lo, hi, _ in BANDS
    ) or 1
    for lo, hi, label in BANDS:
        in_band = [p for p in dir_risk if lo <= p["health"] < hi]
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

    links = []
    if METHODOLOGY_URL:
        links.append(f'<a href="{METHODOLOGY_URL}" target="_blank" rel="noopener">'
                     "Methodology — full research post →</a>")
    if CODE_URL:
        links.append(f'<a href="{CODE_URL}" target="_blank" rel="noopener">Code →</a>')
    links_html = (
        '<p style="margin-bottom:12px">' + " · ".join(links) + "</p>" if links else ""
    )

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
  <h1><span class="hl">{fmt_usd(dir_debt)}</span> of directional debt is inside the
      10% warning buffer across <span class="hl">{len(dir_risk):,}</span> positions</h1>
  <div class="sub">Snapshot {ts} · {n_markets} markets on Ethereum + Base · {blocks} ·
      health read on-chain from each market's own oracle · warning rule:
      health &lt; 1.10 · plus {fmt_usd(cor_debt)} in healthy correlated pairs and
      {fmt_usd(anom_debt)} in depegged/anomalous markets (both shown separately
      below)</div>

  <h2>Directional markets — top 10 by debt at risk</h2>
  <table>
    <tr><th>Market</th><th class="num">Active</th><th class="num">Verified on-chain</th>
        <th class="num">At risk</th><th class="num">Debt at risk</th></tr>
    {market_rows}
  </table>

  <h2>Most critical positions — directional markets</h2>
  <table>
    <tr><th class="num">Health</th><th class="num">To threshold</th><th class="num">Debt</th>
        <th>Market</th><th>Chain</th><th>Borrower</th></tr>
    {top_rows}
  </table>

  <h2>Health distribution of at-risk positions (directional)</h2>
  {band_html}

  <h2>Correlated pairs (peg-checked) — intentional high leverage, low liquidation risk</h2>
  <p style="color:var(--dim);font-size:14px;margin-bottom:10px">
    Collateral and debt move together (stable/stable, LST/underlying) and every
    stable side trades at or above ~97% of its native peg (yield-bearing wrappers
    above par are normal). Positions are commonly run near the threshold by design.
    {fmt_usd(cor_debt)} across {len(cor_risk):,} positions sits
    inside the buffer — shown for transparency, excluded from the headline.</p>
  <table>
    <tr><th>Market</th><th class="num">Verified</th><th class="num">In buffer</th>
        <th class="num">Debt in buffer</th></tr>
    {cor_rows}
  </table>

  <h2>Anomalous / depegged — a "stable" side is off its peg</h2>
  <p style="color:var(--dim);font-size:14px;margin-bottom:10px">
    These pairs would be classified as correlated, but a stable side trades below
    ~97% of its native peg (or has no price) — they are NOT safe-leverage markets
    right now, and their USD figures are valued at the depegged price (treat with
    caution).
    {fmt_usd(anom_debt)} across {len(anom_risk):,} positions in the buffer.</p>
  <table>
    <tr><th>Market</th><th>Depegged asset</th><th class="num">Verified</th>
        <th class="num">In buffer</th><th class="num">Debt in buffer</th></tr>
    {anom_rows}
  </table>

  <footer>
    {links_html}<strong>Method.</strong> Borrowers enumerated via the official Morpho API; every
    position then verified on-chain at a pinned block per chain (Multicall3 batched
    <span class="mono">position()</span> reads). Health = collateral × oracle price ×
    LLTV ÷ debt, using each market's own oracle (<span class="mono">price()</span>,
    1e36 scale) — the same engine validated on the Feb 2026 liquidation backtest.
    <ul>
      <li>Single snapshot — not a continuously updating feed yet.
          Refreshed {ts} · {n_markets} markets monitored.</li>
      <li>Coverage: all non-idle Morpho markets on Ethereum + Base with borrow ≥ $50k;
          reverting oracles skipped (counts in snapshot metadata).</li>
      <li>Positions with debt &lt; $1,000 excluded from ranking unless API health ≤ 1.3
          (cutoffs logged in the snapshot metadata).</li>
      <li>Health is fully on-chain; USD figures use loan-asset prices from the
          Morpho API (ranking only).</li>
      <li>Correlated vs directional is a symbol-based heuristic (stable-stable and
          same-family LST/underlying = correlated) — an approximation. Stables are
          peg-checked against their native peg (EUR stables vs ECB EUR/USD), flagged
          only below ~97% of it — above-par yield wrappers are normal. PT-style
          tokens trading at maturity discount can land in "anomalous" by design.</li>
      <li>Informational only — not financial advice, no execution, no custody.</li>
    </ul>
  </footer>
</div>
</body>
</html>
"""


def main() -> int:
    snapshot = json.loads((RESULTS / "at_risk_snapshot.json").read_text())
    out = REPO_ROOT / "site" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(render(snapshot))
    corr = {
        m["market_id"]: m.get("bucket") or m.get("correlation")
        or classify_market(*m["label"].split("/", 1))[0]
        for m in snapshot["markets"]
    }
    risk = [p for p in snapshot["positions"] if p["at_risk"]]
    print(f"dashboard: {out}")
    for bucket, tag in [("directional", "DIRECTIONAL (headline)"),
                        ("correlated", "healthy correlated"),
                        ("anomalous", "anomalous/depeg")]:
        sel = [p for p in risk if corr[p["market_id"]] == bucket]
        print(f"  {tag}: {len(sel):,} positions | {fmt_usd(sum(p['debt_usd'] for p in sel))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

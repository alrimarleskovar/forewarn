# SPDX-License-Identifier: BUSL-1.1
# Licensed Work: Morpho Risk Tooling — Quant Module. See LICENSE-BSL at the repo root.
"""Morpho Blue liquidation fetcher via the Dune API.

Raw extraction only (no model, no warning-window computation).
Runs a query SAVED on Dune (query_id) and materializes the result as CSV
under ``results/`` (gitignored).

Prerequisites:
- ``.env`` at the repo root with ``DUNE_API_KEY=...``
- query saved on Dune with the SQL from
  ``dune/queries/morpho_blue_liquidations_2026-01-25_2026-02-10.sql``;
  the id comes from ``--query-id`` or the ``DUNE_QUERY_ID`` var (.env).

Usage:
    uv run python -m risk_model.fetch_liquidations --query-id 1234567
"""

import argparse
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

API_BASE = "https://api.dune.com/api/v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = REPO_ROOT / "results"
DEFAULT_OUT = RESULTS_DIR / "morpho_blue_liquidations_2026-01-25_2026-02-10.csv"
POLL_SECONDS = 5
TIMEOUT_SECONDS = 600

TERMINAL_FAILURE_STATES = {
    "QUERY_STATE_FAILED",
    "QUERY_STATE_CANCELLED",
    "QUERY_STATE_EXPIRED",
}


def _headers(api_key: str) -> dict:
    return {"X-Dune-API-Key": api_key}


def execute_query(api_key: str, query_id: int, performance: str = "medium") -> str:
    """Triggers execution of the saved query and returns the execution_id."""
    resp = requests.post(
        f"{API_BASE}/query/{query_id}/execute",
        headers=_headers(api_key),
        json={"performance": performance},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["execution_id"]


def wait_for_completion(api_key: str, execution_id: str) -> None:
    """Polls the status until completion (or failure/timeout)."""
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while True:
        resp = requests.get(
            f"{API_BASE}/execution/{execution_id}/status",
            headers=_headers(api_key),
            timeout=30,
        )
        resp.raise_for_status()
        state = resp.json()["state"]
        if state == "QUERY_STATE_COMPLETED":
            return
        if state in TERMINAL_FAILURE_STATES:
            raise RuntimeError(f"Execution {execution_id} ended in {state}")
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"Execution {execution_id} did not complete within {TIMEOUT_SECONDS}s "
                f"(last state: {state})"
            )
        time.sleep(POLL_SECONDS)


def download_csv(api_key: str, execution_id: str, out_path: Path) -> Path:
    """Downloads the execution result as CSV (paginated via next_uri if present)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"{API_BASE}/execution/{execution_id}/results/csv"
    first = True
    with out_path.open("wb") as fh:
        while url:
            resp = requests.get(url, headers=_headers(api_key), timeout=120)
            resp.raise_for_status()
            content = resp.content
            if not first:
                # subsequent pages repeat the CSV header — drop the 1st line
                content = content.split(b"\n", 1)[1] if b"\n" in content else b""
            fh.write(content)
            first = False
            url = resp.headers.get("x-dune-next-uri") or None
    return out_path


def report_counts(csv_path: Path) -> dict[str, int]:
    """Counts liquidations per chain in the materialized CSV."""
    import pandas as pd

    df = pd.read_csv(csv_path)
    return df.groupby("chain").size().to_dict()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query-id", type=int, default=None, help="id of the query saved on Dune")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output CSV path")
    parser.add_argument(
        "--performance", choices=["medium", "large"], default="medium", help="execution tier"
    )
    args = parser.parse_args(argv)

    load_dotenv(REPO_ROOT / ".env")
    api_key = os.environ.get("DUNE_API_KEY")
    if not api_key:
        print("ERROR: DUNE_API_KEY missing from the .env at the repo root", file=sys.stderr)
        return 1

    query_id = args.query_id or (
        int(os.environ["DUNE_QUERY_ID"]) if os.environ.get("DUNE_QUERY_ID") else None
    )
    if not query_id:
        print(
            "ERROR: query_id missing. Save the query on Dune and pass --query-id N "
            "(or DUNE_QUERY_ID in .env). SQL in dune/queries/.",
            file=sys.stderr,
        )
        return 1

    print(f"Running query {query_id} (performance={args.performance})…")
    execution_id = execute_query(api_key, query_id, args.performance)
    print(f"execution_id={execution_id}; waiting for completion…")
    wait_for_completion(api_key, execution_id)
    out = download_csv(api_key, execution_id, args.out)
    counts = report_counts(out)
    total = sum(counts.values())
    print(f"CSV: {out}")
    by_chain = " | ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"Liquidations: total={total} | {by_chain}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# SPDX-License-Identifier: BUSL-1.1
# Licensed Work: Morpho Risk Tooling — Quant Module. Ver LICENSE-BSL na raiz.
"""Fetcher de liquidações Morpho Blue via Dune API.

Extração bruta apenas (sem modelo, sem cálculo de janela de aviso).
Executa uma query SALVA no Dune (query_id) e materializa o resultado em CSV
em ``results/`` (gitignored).

Pré-requisitos:
- ``.env`` na raiz do repo com ``DUNE_API_KEY=...``
- query salva no Dune com o SQL de
  ``dune/queries/morpho_blue_liquidations_2026-01-25_2026-02-10.sql``;
  o id vem de ``--query-id`` ou da var ``DUNE_QUERY_ID`` (.env).

Uso:
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
    """Dispara a execução da query salva e retorna o execution_id."""
    resp = requests.post(
        f"{API_BASE}/query/{query_id}/execute",
        headers=_headers(api_key),
        json={"performance": performance},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["execution_id"]


def wait_for_completion(api_key: str, execution_id: str) -> None:
    """Faz polling do status até completar (ou falhar/estourar o timeout)."""
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
            raise RuntimeError(f"Execução {execution_id} terminou em {state}")
        if time.monotonic() > deadline:
            raise TimeoutError(
                f"Execução {execution_id} não completou em {TIMEOUT_SECONDS}s "
                f"(último estado: {state})"
            )
        time.sleep(POLL_SECONDS)


def download_csv(api_key: str, execution_id: str, out_path: Path) -> Path:
    """Baixa o resultado da execução em CSV (paginado via next_uri se houver)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"{API_BASE}/execution/{execution_id}/results/csv"
    first = True
    with out_path.open("wb") as fh:
        while url:
            resp = requests.get(url, headers=_headers(api_key), timeout=120)
            resp.raise_for_status()
            content = resp.content
            if not first:
                # páginas seguintes repetem o header CSV — descarta a 1ª linha
                content = content.split(b"\n", 1)[1] if b"\n" in content else b""
            fh.write(content)
            first = False
            url = resp.headers.get("x-dune-next-uri") or None
    return out_path


def report_counts(csv_path: Path) -> dict[str, int]:
    """Conta liquidações por chain no CSV materializado."""
    import pandas as pd

    df = pd.read_csv(csv_path)
    return df.groupby("chain").size().to_dict()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query-id", type=int, default=None, help="id da query salva no Dune")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="caminho do CSV de saída")
    parser.add_argument(
        "--performance", choices=["medium", "large"], default="medium", help="tier de execução"
    )
    args = parser.parse_args(argv)

    load_dotenv(REPO_ROOT / ".env")
    api_key = os.environ.get("DUNE_API_KEY")
    if not api_key:
        print("ERRO: DUNE_API_KEY ausente no .env da raiz do repo", file=sys.stderr)
        return 1

    query_id = args.query_id or (
        int(os.environ["DUNE_QUERY_ID"]) if os.environ.get("DUNE_QUERY_ID") else None
    )
    if not query_id:
        print(
            "ERRO: query_id ausente. Salve a query no Dune e passe --query-id N "
            "(ou DUNE_QUERY_ID no .env). SQL em dune/queries/.",
            file=sys.stderr,
        )
        return 1

    print(f"Executando query {query_id} (performance={args.performance})…")
    execution_id = execute_query(api_key, query_id, args.performance)
    print(f"execution_id={execution_id}; aguardando conclusão…")
    wait_for_completion(api_key, execution_id)
    out = download_csv(api_key, execution_id, args.out)
    counts = report_counts(out)
    total = sum(counts.values())
    print(f"CSV: {out}")
    by_chain = " | ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"Liquidações: total={total} | {by_chain}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

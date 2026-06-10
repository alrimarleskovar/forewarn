# SPDX-License-Identifier: BUSL-1.1
# Licensed Work: Morpho Risk Tooling — Quant Module. Ver LICENSE-BSL na raiz.
"""Refresh de um comando: monitor v1 (todos os mercados) → dashboard → site/index.html.

Uso:
    uv run python -m risk_model.refresh
"""

import sys

from risk_model import dashboard_v0, live_monitor_v1


def main() -> int:
    rc = live_monitor_v1.main()
    if rc != 0:
        return rc
    return dashboard_v0.main()


if __name__ == "__main__":
    sys.exit(main())

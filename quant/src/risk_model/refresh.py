# SPDX-License-Identifier: BUSL-1.1
# Licensed Work: Morpho Risk Tooling — Quant Module. See LICENSE-BSL at the repo root.
"""One-command refresh: monitor v1 (all markets) → dashboard → site/index.html.

Usage:
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

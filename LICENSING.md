# LICENSING

This is a **mixed-license** monorepo. The license governing each file is that of its directory, per the table below — not whatever single label GitHub displays.

| Directory | License | File |
|---|---|---|
| `packages/ingestion/` | **MIT** | `LICENSE-MIT` |
| `dune/` | **MIT** | `LICENSE-MIT` |
| `quant/` | **BUSL-1.1** (Change License: Apache-2.0) | `LICENSE-BSL` |
| All other files (docs, configs, root) | **MIT** | `LICENSE-MIT` |

## Rationale for the split

- **Commodity infrastructure** (ingestion, Dune queries, helpers) → **MIT**: maximizes adoption and auditability; this is not where the defensibility lies.
- **Risk model** (`quant/`) → **BUSL-1.1** (source-available): code open for reading and evaluation, but with a restriction on production use until the Change Date, when it converts to **Apache-2.0**. Direct precedent: the Morpho Blue core is BUSL-1.1.

The BUSL parameters (Licensor, Change Date, etc.) are in `LICENSE-BSL`. The Additional Use Grant permits use limited to **non-production research and internal evaluation**.

## Note on the GitHub label

GitHub detects licenses heuristically and may label this repo imprecisely (e.g., showing only "MIT" or "license not detected") because it is a mixed-license monorepo. **The per-directory license files and this table govern**, not the UI label.

## Headers

Source files in `quant/` carry a BUSL-1.1 header; source files in `packages/ingestion/` carry an MIT header.

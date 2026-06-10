# Validation Pre-Registration — Morpho Risk Tooling

> **COURTESY TRANSLATION.** The canonical, signed document is the Portuguese
> original [`validation-preregistration.md`](./validation-preregistration.md),
> committed and externally anchored BEFORE any liquidation data was inspected:
> - attestation commit: `f5bcfd1e9dd11b80e07344043f9b07b795b3e4ee`
> - final thresholds (§ 4) commit: `b9b9d9cada9bb79dbffbee4cdfb3ba9507d8d2a0`
>
> In case of any divergence, the Portuguese original governs.

> **GOLDEN RULE:** this file is filled in and committed **before any liquidation
> data is viewed**. After seeing the data, pre-registering is logically
> impossible. Do not fill any number on this page based on data already observed.

---

## 0. Pre-registration attestation

- **Author(s):** `ALRIMAR`
- **Commit date/time:** `2026-06-10 01:50 TZ`
- **Commit hash:** `[filled by git]`
- **I attest that no Feb/2026 or Oct/2025 liquidation data was inspected before this commit:** `[x] YES`

---

## 1. Hypothesis under test

> A neutral, borrower/integrator-facing risk model delivers useful, actionable
> liquidation warning earlier (or with better conversion to action) than current
> solutions.

- **Directional prediction (filled before data — expected vs. observed is compared on all 3 axes):**
  - **Expected signal:** addressable ceiling ~`[___]%`, median realized window ~`[___]`.
  - **Expected space:** `[ OPEN / CONTESTED / CLOSED ]` — rationale: `[___]`.
  - **Expected ramp:** `[ HAS / THIN / NONE ]` — warm/2nd-degree contacts currently known: `[___]`.

  *(Recording the expectation on all 3 axes forces honesty in the later reading — not just on Signal.)*

---

## 2. Metric definitions (frozen)

**2.1 Point-in-time realized window** — time between the first moment a
*walk-forward* model (using only data knowable at that timestamp) would have
issued a risk alert and the moment the liquidation executed. **No look-ahead bias.**

**2.2 Theoretical window (upper bound)** — same, but with after-the-fact
visibility. Used only as a ceiling, **not** as a sales claim.

**2.3 Capacity to cure (observable on-chain)** — within the realized window, did
the position have **sufficient gas** `AND` **accessible collateral/funds** to
top up/repay and restore health? `(yes/no)`

**2.4 Addressable market ceiling** — fraction of liquidations with
**capacity = yes** that were liquidated anyway. It is the upper bound of what a
warning product could have prevented.

**2.5 Awareness/willingness (not observable on-chain)** — only refinable with
integrator alert-delivery data (Test 2). Does **not** enter the on-chain number;
recorded as a pending item.

---

## 3. Data and scope (frozen)

- **Primary event:** Feb/2026.
- **Out-of-sample event:** Oct/2025.
- **Liquidations reconstructed per event:** `[5–10]`
- **Selection criterion:** `[e.g.: largest by value / stratified random sample by collateral — TO DEFINE]`
- **Sources:** Dune + Etherscan + Morpho subgraph + official GraphQL; **historical oracle price per block via** `[archival node / feed — TO DEFINE]`.
- **Chains in scope:** Ethereum, Base.

---

## 4. Pre-committed thresholds

> Reference defaults below. **Confirm or deliberately adjust BEFORE seeing data.** Mark each as confirmed.

### 4.1 Signal (Test 1)
| Class | Criterion (default to confirm) | Confirmed? |
|---|---|---|
| **STRONG** | median realized window **≥ 2h** `AND/OR` addressable ceiling **≥ 40%**, **stable across both regimes** | `[ ]` final value: `2h / 40%` |
| **MEDIUM** | window **1–2h** `OR` unstable signal across regimes / mixed attribution | `[ ]` final window value: `<1h` |
| **WEAK** | window **< 1h** `AND` addressable ceiling **< `25%`** | `[ ]` final window value: `<1h` / ceiling: `25%` |

**Definition of "stable across regimes":** the class does not change between
Feb/2026 and Oct/2025; divergence downgrades to MEDIUM at most. `[ ]` confirmed

### 4.2 Space (Test 2)
| Class | Criterion (default to confirm) | Confirmed? |
|---|---|---|
| **OPEN** | ≥1 explicit signal (Morpho or integrator) that a neutral third party has a place | `[x ]` |
| **CONTESTED** | Hypernative likely extends `OR` integrator signals preference for in-house build | `[x ]` |
| **CLOSED** | official partner will cover it `AND` integrators building internally | `[x ]` |

### 4.3 Ramp (Test 3)
| Class | Criterion (default to confirm) | Confirmed? |
|---|---|---|
| **HAS** | **≥ 3** warm/2nd-degree contacts in the right roles | `[x]` final value: `[]` |
| **THIN** | 1–2 | `[x ]` |
| **NONE** | 0–1 | `[x ]` |

---

ALRIMAR SOBRINHO 10-06-2026

## 5. Decision rule (frozen)

| Space | Verdict (Signal STRONG/MEDIUM) | Role of the Ramp |
|---|---|---|
| OPEN | **Full GO** | HAS/THIN → outbound+inbound · NONE → inbound-led |
| CONTESTED | **Accelerated GO with obsolescence clause** (+ defensibility plan) | HAS/THIN → outbound-led · NONE → inbound-led |
| CLOSED | **NO-GO in the current format** | — |

**WEAK signal (any Space/Ramp):** **Pivot** — evaluate an automatic-action
product (more regulated) or another wedge. Do not build the warning product.

- **Team agreement to follow this rule even if the result is inconvenient:** `[ ] YES`

---

## 6. Threshold change clause

Any threshold adjustment **after** seeing data requires, in this file:
- **Date of adjustment:** `[___]`
- **Old → new threshold:** `[___]`
- **Explicit reason (not "the result would look better"):** `[___]`
- **Expectation reset recorded:** `[ ]`
- **Approved by:** `[___]`

> Change log (append-only):
> - `[none so far]`

---

## 7. Pending items that depend on external data (do not block the on-chain verdict)

- [ ] Integrator alert-delivery data → refines the addressable ceiling by removing "saw and declined".
- [ ] Confirm historical oracle price granularity at the chosen source.

---

## 8. Signatures

- `[NAME]` — `[DATE]`
- `[NAME]` — `[DATE]`

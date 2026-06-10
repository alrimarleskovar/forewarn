# SPDX-License-Identifier: BUSL-1.1
# Licensed Work: Morpho Risk Tooling — Quant Module. See LICENSE-BSL at the repo root.
"""Base schema; the model (Black-Cox/Merton, point-in-time) is NOT implemented in this phase.

Structure only (pydantic types), no logic. MVP chains: Ethereum + Base.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class Chain(StrEnum):
    """Chains in scope for the MVP."""

    ETHEREUM = "ethereum"
    BASE = "base"


class Market(BaseModel):
    """A Morpho market (permissionless: each market defines its own oracle/IRM)."""

    market_id: str
    collateral_asset: str
    loan_asset: str
    lltv: float
    oracle: str
    irm: str
    chain: Chain


class OraclePriceObservation(BaseModel):
    """Oracle price of a market at a historical block."""

    market_id: str
    block: int
    timestamp: datetime
    price: float


class Position(BaseModel):
    """A borrower's position in a market."""

    market_id: str
    borrower: str
    collateral_amount: float
    debt_amount: float


class HealthSnapshot(BaseModel):
    """Health of a position at an instant (walk-forward reconstruction)."""

    position: Position
    timestamp: datetime
    health_factor: float
    distance_to_lltv: float


class LiquidationEvent(BaseModel):
    """Liquidation executed on-chain."""

    position: Position
    timestamp: datetime
    block: int
    tx_hash: str
    seized: float
    repaid: float


class WarningSignal(BaseModel):
    """Warning signal reconstructed for a liquidated position.

    capacity_to_cure = had_sufficient_gas AND had_recoverable_collateral
    (observable on-chain). Awareness/willingness is NOT observable on-chain —
    it comes from the integrator's alert-delivery data (Test 2) and is not
    included here.
    """

    position: Position
    timestamp: datetime
    realized_window_seconds: int
    theoretical_window_seconds: int
    had_sufficient_gas: bool
    had_recoverable_collateral: bool

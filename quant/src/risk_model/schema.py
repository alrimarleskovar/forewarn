# SPDX-License-Identifier: BUSL-1.1
# Licensed Work: Morpho Risk Tooling — Quant Module. Ver LICENSE-BSL na raiz.
"""Esquema base; o modelo (Black-Cox/Merton, point-in-time) NÃO é implementado nesta fase.

Apenas estrutura (tipos pydantic), sem lógica. Chains do MVP: Ethereum + Base.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class Chain(StrEnum):
    """Chains no escopo do MVP."""

    ETHEREUM = "ethereum"
    BASE = "base"


class Market(BaseModel):
    """Um market Morpho (permissionless: cada market define oráculo/IRM próprios)."""

    market_id: str
    collateral_asset: str
    loan_asset: str
    lltv: float
    oracle: str
    irm: str
    chain: Chain


class OraclePriceObservation(BaseModel):
    """Preço do oráculo de um market em um bloco histórico."""

    market_id: str
    block: int
    timestamp: datetime
    price: float


class Position(BaseModel):
    """Posição de um borrower em um market."""

    market_id: str
    borrower: str
    collateral_amount: float
    debt_amount: float


class HealthSnapshot(BaseModel):
    """Saúde de uma posição em um instante (reconstrução walk-forward)."""

    position: Position
    timestamp: datetime
    health_factor: float
    distance_to_lltv: float


class LiquidationEvent(BaseModel):
    """Liquidação executada on-chain."""

    position: Position
    timestamp: datetime
    block: int
    tx_hash: str
    seized: float
    repaid: float


class WarningSignal(BaseModel):
    """Sinal de aviso reconstruído para uma posição liquidada.

    capacity_to_cure = had_sufficient_gas AND had_recoverable_collateral
    (observável on-chain). Consciência/vontade NÃO é observável on-chain —
    vem do dado de alert-delivery do integrador (Teste 2) e não entra aqui.
    """

    position: Position
    timestamp: datetime
    realized_window_seconds: int
    theoretical_window_seconds: int
    had_sufficient_gas: bool
    had_recoverable_collateral: bool

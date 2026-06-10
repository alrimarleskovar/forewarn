-- Morpho Blue — Liquidate events, Ethereum + Base
-- Window: 2026-01-25 00:00 UTC (inclusive) → 2026-02-11 00:00 UTC (exclusive),
--         i.e. Jan 25 through Feb 10, 2026, in full.
--
-- Pre-registration (docs/validation-preregistration.md), committed BEFORE this query:
--   f5bcfd1e9dd11b80e07344043f9b07b795b3e4ee  chore(validation): commit pre-registered thresholds
--   b9b9d9cada9bb79dbffbee4cdfb3ba9507d8d2a0  chore(validation): preencher valores finais do §4
--
-- Scope: raw extraction only — no model, no warning-window computation.
-- Decoded tables confirmed in Dune's official spellbook
-- (sources/_sector/lending/borrow/{ethereum,base}/_sources.yml).

SELECT
    'ethereum' AS chain,
    id,
    borrower,
    seizedAssets,
    repaidAssets,
    badDebtAssets,
    evt_block_time,
    evt_block_number,
    evt_tx_hash
FROM morpho_blue_ethereum.MorphoBlue_evt_Liquidate
WHERE evt_block_time >= TIMESTAMP '2026-01-25 00:00:00'
  AND evt_block_time <  TIMESTAMP '2026-02-11 00:00:00'

UNION ALL

SELECT
    'base' AS chain,
    id,
    borrower,
    seizedAssets,
    repaidAssets,
    badDebtAssets,
    evt_block_time,
    evt_block_number,
    evt_tx_hash
FROM morpho_blue_base.MorphoBlue_evt_Liquidate
WHERE evt_block_time >= TIMESTAMP '2026-01-25 00:00:00'
  AND evt_block_time <  TIMESTAMP '2026-02-11 00:00:00'

ORDER BY evt_block_time, evt_block_number

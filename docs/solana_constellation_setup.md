# Solana Constellation setup

## 1) Minimal env (smoke test)
These values are only to confirm ingestion. Replace with real addresses for production.

```
SOLANA_RPC_URL=https://your-solana-rpc
SPARKY_SOLANA_DSN=postgresql://user:pass@host:5432/db
SPARKY_SOLANA_REFRESH_TOKEN=change-me
HELIUS_API_KEY=

# Smoke test addresses (noisy, replace later)
SOLANA_TRACKED_PROGRAMS=BPFLoaderUpgradeab1e11111111111111111111111,TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA
SOLANA_GOVERNANCE_PROGRAMS=GovER5Lthms3LrS6YpGmz3chxj41a1pybGJ4P94sKM
SOLANA_GOVERNANCE_REALMS=BzGL6wbCvBisQ7s1cNQvDGZwDRWwKK6bhrV93RYdetzJ
SOLANA_TRACKED_MINTS=
SOLANA_TREASURY_ACCOUNTS=
SOLANA_SUPPLY_ALLOW_MINT=on
```

## 2) Production watch list (recommended)
Keep the list small and specific. Add only addresses you care about.

```
# Governance programs (SPL Governance is the core Realms flow)
SOLANA_GOVERNANCE_PROGRAMS=GovER5Lthms3LrS6YpGmz3chxj41a1pybGJ4P94sKM

# Realms DAO realm account(s) to scope governance to a single DAO
SOLANA_GOVERNANCE_REALMS=<realms_dao_realm_account>

# Programs you want to watch for upgrades or authority changes
SOLANA_TRACKED_PROGRAMS=BPFLoaderUpgradeab1e11111111111111111111111

# Token mints that matter for supply and unlock pressure
SOLANA_TRACKED_MINTS=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v,Es9vMFrzaCERmJfrF4H2FYD4Kco3Pt5pEw7P5nE5r
SOLANA_SUPPLY_UNLOCK_THRESHOLD=100000
SOLANA_SUPPLY_ALLOW_MINT=off

# Treasury accounts and multisigs (2–3 examples)
SOLANA_TREASURY_ACCOUNTS=<dao_multisig_1>,<dao_multisig_2>,<dao_multisig_3>

# Optional thresholds
SOLANA_TREASURY_SOL_THRESHOLD=25
SOLANA_TREASURY_SOL_CRITICAL=250
# Optional (Helius)
# If SOLANA_RPC_URL is empty, the Helius key will be used with
# https://api-mainnet.helius-rpc.com/
HELIUS_API_KEY=
```

## 3) Refresh script
```
./scripts/solana_constellation_refresh.sh
```

## 4) Cron (example)
Every 15 minutes:
```
*/15 * * * * /path/to/scripts/solana_constellation_refresh.sh >> /var/log/solana_constellation_refresh.log 2>&1
```

## 5) Verify
- `POST /planet/solana/api/refresh`
- `GET /planet/solana/api/stars` should show non-zero `raw_events` after refresh.

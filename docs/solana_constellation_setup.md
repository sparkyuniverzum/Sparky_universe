# Solana Constellation setup

## 1) Minimal env (smoke test)
These values are only to confirm ingestion. Replace with real addresses for production.

```
SOLANA_RPC_URL=https://your-solana-rpc
SPARKY_SOLANA_DSN=postgresql://user:pass@host:5432/db
SPARKY_SOLANA_REFRESH_TOKEN=change-me

# Smoke test addresses (noisy, replace later)
SOLANA_TRACKED_PROGRAMS=BPFLoaderUpgradeab1e11111111111111111111111,TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA
SOLANA_GOVERNANCE_PROGRAMS=
SOLANA_TRACKED_MINTS=
SOLANA_TREASURY_ACCOUNTS=
```

## 2) Production watch list (recommended)
Keep the list small and specific. Add only addresses you care about.

```
# Governance programs (your DAO / Realms program IDs)
SOLANA_GOVERNANCE_PROGRAMS=<governance_program_id_1>,<governance_program_id_2>

# Programs you want to watch for upgrades or authority changes
SOLANA_TRACKED_PROGRAMS=<program_id_1>,<program_id_2>

# Token mints that matter for supply and unlock pressure
SOLANA_TRACKED_MINTS=<mint_address_1>,<mint_address_2>

# Treasury accounts and multisigs
SOLANA_TREASURY_ACCOUNTS=<treasury_address_1>,<treasury_address_2>

# Optional thresholds
SOLANA_TREASURY_SOL_THRESHOLD=25
SOLANA_TREASURY_SOL_CRITICAL=250
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

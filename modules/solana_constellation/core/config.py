from __future__ import annotations

from dataclasses import dataclass
import os
from typing import List


TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
UPGRADEABLE_LOADER_ID = "BPFLoaderUpgradeab1e11111111111111111111111"
LAMPORTS_PER_SOL = 1_000_000_000


@dataclass(frozen=True)
class SolanaConfig:
    rpc_url: str
    governance_programs: List[str]
    tracked_programs: List[str]
    tracked_mints: List[str]
    treasury_accounts: List[str]
    treasury_threshold_sol: float
    treasury_critical_sol: float
    refresh_token: str


def _split_env(name: str) -> List[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value


def load_config() -> SolanaConfig:
    return SolanaConfig(
        rpc_url=os.getenv("SOLANA_RPC_URL", "").strip(),
        governance_programs=_split_env("SOLANA_GOVERNANCE_PROGRAMS"),
        tracked_programs=_split_env("SOLANA_TRACKED_PROGRAMS"),
        tracked_mints=_split_env("SOLANA_TRACKED_MINTS"),
        treasury_accounts=_split_env("SOLANA_TREASURY_ACCOUNTS"),
        treasury_threshold_sol=_float_env("SOLANA_TREASURY_SOL_THRESHOLD", 25.0),
        treasury_critical_sol=_float_env("SOLANA_TREASURY_SOL_CRITICAL", 250.0),
        refresh_token=os.getenv("SPARKY_SOLANA_REFRESH_TOKEN", "").strip(),
    )

from __future__ import annotations

from dataclasses import dataclass
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from typing import List


TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
UPGRADEABLE_LOADER_ID = "BPFLoaderUpgradeab1e11111111111111111111111"
LAMPORTS_PER_SOL = 1_000_000_000


@dataclass(frozen=True)
class SolanaConfig:
    rpc_url: str
    governance_programs: List[str]
    governance_realms: List[str]
    tracked_programs: List[str]
    tracked_mints: List[str]
    treasury_accounts: List[str]
    treasury_threshold_sol: float
    treasury_critical_sol: float
    supply_unlock_threshold: float
    supply_allow_mint: bool
    refresh_token: str
    signature_batch_limit: int
    signature_max_pages: int


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


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value


def _flag(name: str, default: str = "off") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def _resolve_rpc_url() -> str:
    base = os.getenv("SOLANA_RPC_URL", "").strip()
    api_key = os.getenv("HELIUS_API_KEY", "").strip()
    if not base and api_key:
        base = "https://api-mainnet.helius-rpc.com/"
    if not base:
        return ""
    if not api_key:
        return base
    parts = urlsplit(base)
    query = dict(parse_qsl(parts.query))
    if any(key in query for key in ("api-key", "api_key", "apikey")):
        return base
    query["api-key"] = api_key
    new_query = urlencode(query)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def load_config() -> SolanaConfig:
    return SolanaConfig(
        rpc_url=_resolve_rpc_url(),
        governance_programs=_split_env("SOLANA_GOVERNANCE_PROGRAMS"),
        governance_realms=_split_env("SOLANA_GOVERNANCE_REALMS"),
        tracked_programs=_split_env("SOLANA_TRACKED_PROGRAMS"),
        tracked_mints=_split_env("SOLANA_TRACKED_MINTS"),
        treasury_accounts=_split_env("SOLANA_TREASURY_ACCOUNTS"),
        treasury_threshold_sol=_float_env("SOLANA_TREASURY_SOL_THRESHOLD", 25.0),
        treasury_critical_sol=_float_env("SOLANA_TREASURY_SOL_CRITICAL", 250.0),
        supply_unlock_threshold=_float_env("SOLANA_SUPPLY_UNLOCK_THRESHOLD", 0.0),
        supply_allow_mint=_flag("SOLANA_SUPPLY_ALLOW_MINT", "off"),
        refresh_token=os.getenv("SPARKY_SOLANA_REFRESH_TOKEN", "").strip(),
        signature_batch_limit=_int_env("SOLANA_SIGNATURE_BATCH_LIMIT", 100),
        signature_max_pages=_int_env("SOLANA_SIGNATURE_MAX_PAGES", 0),
    )

from __future__ import annotations

from dataclasses import dataclass
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from typing import List


TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
UPGRADEABLE_LOADER_ID = "BPFLoaderUpgradeab1e11111111111111111111111"
LAMPORTS_PER_SOL = 1_000_000_000
DEFAULT_PUBLIC_RPC = "https://api.mainnet-beta.solana.com"


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


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value


def _split_url_env(name: str) -> List[str]:
    raw = os.getenv(name, "")
    if not raw:
        return []
    raw = raw.replace("\n", ",")
    items: List[str] = []
    for chunk in raw.split(","):
        value = _strip_quotes(chunk)
        if value:
            items.append(value)
    return items


def _normalize_rpc_url(url: str, api_key: str) -> str:
    value = _strip_quotes(url)
    if "api-mainnet.helius-rpc.com" in value:
        value = value.replace("api-mainnet.helius-rpc.com", "mainnet.helius-rpc.com")
    if not api_key:
        return value
    if "helius-rpc.com" not in value and "rpc.helius.xyz" not in value:
        return value
    parts = urlsplit(value)
    query = dict(parse_qsl(parts.query))
    if any(key in query for key in ("api-key", "api_key", "apikey")):
        return value
    query["api-key"] = api_key
    new_query = urlencode(query)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def _resolve_rpc_url() -> str:
    base = _strip_quotes(os.getenv("SOLANA_RPC_URL", ""))
    api_key = _strip_quotes(os.getenv("HELIUS_API_KEY", ""))
    if not base and api_key:
        base = "https://mainnet.helius-rpc.com/"
    if not base:
        return ""
    return _normalize_rpc_url(base, api_key)


def _public_rpc_fallback_enabled() -> bool:
    return _flag("SOLANA_PUBLIC_RPC_FALLBACK", "on")


def load_rpc_urls() -> List[str]:
    api_key = _strip_quotes(os.getenv("HELIUS_API_KEY", ""))
    urls: List[str] = []

    primary_list = _split_url_env("SOLANA_RPC_URLS")
    if primary_list:
        urls.extend(_normalize_rpc_url(url, api_key) for url in primary_list if url)
    else:
        primary = _resolve_rpc_url()
        if primary:
            urls.append(primary)

    fallback_list = _split_url_env("SOLANA_RPC_FALLBACK_URLS")
    urls.extend(_normalize_rpc_url(url, api_key) for url in fallback_list if url)

    if _public_rpc_fallback_enabled():
        urls.append(DEFAULT_PUBLIC_RPC)

    seen = set()
    ordered: List[str] = []
    for url in urls:
        if url and url not in seen:
            ordered.append(url)
            seen.add(url)
    return ordered


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

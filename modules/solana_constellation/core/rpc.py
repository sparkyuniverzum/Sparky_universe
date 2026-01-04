from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen

from modules.solana_constellation.core.config import load_config


class SolanaRpcError(RuntimeError):
    pass


def _rpc_request(method: str, params: list[Any]) -> Dict[str, Any]:
    config = load_config()
    if not config.rpc_url:
        raise SolanaRpcError("SOLANA_RPC_URL is not configured.")
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    req = Request(
        config.rpc_url,
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    if "error" in data:
        raise SolanaRpcError(str(data["error"]))
    return data


def get_signatures_for_address(
    address: str,
    *,
    limit: int = 20,
    before: str | None = None,
) -> List[Dict[str, Any]]:
    params: List[Any] = [address, {"limit": limit}]
    if before:
        params[1]["before"] = before
    response = _rpc_request("getSignaturesForAddress", params)
    return response.get("result") or []


def get_transaction(signature: str) -> Optional[Dict[str, Any]]:
    params = [signature, {"encoding": "json", "maxSupportedTransactionVersion": 0}]
    response = _rpc_request("getTransaction", params)
    return response.get("result")

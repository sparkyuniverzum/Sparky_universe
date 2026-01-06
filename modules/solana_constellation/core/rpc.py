from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from modules.solana_constellation.core.config import load_rpc_urls


class SolanaRpcError(RuntimeError):
    pass


def _rpc_request(method: str, params: list[Any]) -> Dict[str, Any]:
    urls = load_rpc_urls()
    if not urls:
        raise SolanaRpcError("SOLANA_RPC_URL is not configured.")

    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    retryable_status = {401, 403, 404, 429, 500, 502, 503, 504}
    last_error: Exception | None = None

    for url in urls:
        try:
            req = Request(
                url,
                data=payload.encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            if "error" in data:
                raise SolanaRpcError(str(data["error"]))
            return data
        except HTTPError as exc:
            last_error = exc
            if exc.code in retryable_status:
                continue
            raise SolanaRpcError(f"RPC HTTP error {exc.code}.") from exc
        except (URLError, TimeoutError) as exc:
            last_error = exc
            continue

    if last_error is not None:
        raise SolanaRpcError(f"RPC request failed: {last_error}") from last_error
    raise SolanaRpcError("RPC request failed.")


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
    params = [
        signature,
        {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0},
    ]
    response = _rpc_request("getTransaction", params)
    return response.get("result")

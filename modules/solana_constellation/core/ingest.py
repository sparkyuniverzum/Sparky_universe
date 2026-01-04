from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from modules.solana_constellation.core.config import (
    LAMPORTS_PER_SOL,
    TOKEN_PROGRAM_ID,
    UPGRADEABLE_LOADER_ID,
    load_config,
)
from modules.solana_constellation.core.rpc import SolanaRpcError, get_signatures_for_address, get_transaction
from modules.solana_constellation.core.storage import (
    record_event,
    record_raw,
    event_count,
    raw_count,
    set_last_ingest_at,
)
from modules.solana_constellation.core.stars import STAR_DEFS


def _iso_time(block_time: Optional[int]) -> str:
    if not block_time:
        return datetime.now(timezone.utc).isoformat()
    return datetime.fromtimestamp(block_time, tz=timezone.utc).isoformat()


def _normalize_keys(keys: List[Any]) -> List[str]:
    normalized = []
    for item in keys:
        if isinstance(item, dict) and "pubkey" in item:
            normalized.append(str(item["pubkey"]))
        else:
            normalized.append(str(item))
    return normalized


def _extract_accounts(message: Dict[str, Any], meta: Dict[str, Any]) -> List[str]:
    account_keys = _normalize_keys(message.get("accountKeys") or [])
    loaded = meta.get("loadedAddresses") or {}
    account_keys.extend(loaded.get("writable") or [])
    account_keys.extend(loaded.get("readonly") or [])
    return account_keys


def _extract_program_ids(message: Dict[str, Any], accounts: List[str]) -> List[str]:
    program_ids: List[str] = []
    for instr in message.get("instructions") or []:
        if isinstance(instr, dict):
            program_id = instr.get("programId")
            if not program_id and "programIdIndex" in instr:
                idx = instr.get("programIdIndex")
                if isinstance(idx, int) and 0 <= idx < len(accounts):
                    program_id = accounts[idx]
            if program_id:
                program_ids.append(str(program_id))
    return program_ids


def _log_contains(logs: Iterable[str], token: str) -> bool:
    token_lower = token.lower()
    for line in logs:
        if token_lower in str(line).lower():
            return True
    return False


def _base_event(
    *,
    star: str,
    action: str,
    impact_level: int,
    source_signature: str,
    valid_from: str,
    extra: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    info = STAR_DEFS.get(star, {})
    payload: Dict[str, Any] = {
        "constellation": "solana",
        "star": star,
        "entity": f"{star}_event",
        "action": action,
        "scope": "protocol",
        "impact_level": impact_level,
        "affected_roles": info.get("roles", []),
        "valid_from": valid_from,
        "valid_to": None,
        "source_refs": [source_signature],
    }
    if extra:
        payload["details"] = extra
    return payload


def _detect_governance(
    *,
    program_ids: List[str],
    logs: List[str],
    signature: str,
    block_time: Optional[int],
    governance_programs: List[str],
) -> List[Dict[str, Any]]:
    if not governance_programs:
        return []
    if not any(pid in governance_programs for pid in program_ids):
        return []

    actions = [
        ("createproposal", "proposal_created", 4),
        ("updateproposal", "proposal_updated", 3),
        ("editproposal", "proposal_updated", 3),
        ("castvote", "vote_cast", 2),
        ("execut", "proposal_executed", 4),
        ("finalize", "proposal_finalized", 4),
        ("setgovernance", "rules_changed", 4),
    ]
    for token, action, impact in actions:
        if _log_contains(logs, token):
            return [
                _base_event(
                    star="governance",
                    action=action,
                    impact_level=impact,
                    source_signature=signature,
                    valid_from=_iso_time(block_time),
                )
            ]
    return []


def _detect_program(
    *,
    program_ids: List[str],
    logs: List[str],
    signature: str,
    block_time: Optional[int],
    tracked_programs: List[str],
) -> List[Dict[str, Any]]:
    if UPGRADEABLE_LOADER_ID not in program_ids:
        return []
    if tracked_programs:
        if not any(program in tracked_programs for program in program_ids):
            return []
    if _log_contains(logs, "instruction: upgrade"):
        return [
            _base_event(
                star="program",
                action="program_upgraded",
                impact_level=4,
                source_signature=signature,
                valid_from=_iso_time(block_time),
            )
        ]
    if _log_contains(logs, "instruction: setauthority"):
        return [
            _base_event(
                star="program",
                action="program_authority_changed",
                impact_level=3,
                source_signature=signature,
                valid_from=_iso_time(block_time),
            )
        ]
    return []


def _detect_supply(
    *,
    program_ids: List[str],
    logs: List[str],
    accounts: List[str],
    signature: str,
    block_time: Optional[int],
    tracked_mints: List[str],
) -> List[Dict[str, Any]]:
    if TOKEN_PROGRAM_ID not in program_ids:
        return []
    if tracked_mints and not any(mint in accounts for mint in tracked_mints):
        return []

    if _log_contains(logs, "instruction: mintto"):
        return [
            _base_event(
                star="supply",
                action="minted",
                impact_level=3,
                source_signature=signature,
                valid_from=_iso_time(block_time),
            )
        ]
    if _log_contains(logs, "instruction: setauthority"):
        return [
            _base_event(
                star="supply",
                action="authority_changed",
                impact_level=4,
                source_signature=signature,
                valid_from=_iso_time(block_time),
            )
        ]
    return []


def _lamport_delta(
    accounts: List[str],
    meta: Dict[str, Any],
    watched: List[str],
) -> Dict[str, float]:
    pre = meta.get("preBalances") or []
    post = meta.get("postBalances") or []
    deltas: Dict[str, float] = {}
    for address in watched:
        if address not in accounts:
            continue
        idx = accounts.index(address)
        if idx >= len(pre) or idx >= len(post):
            continue
        delta = abs(post[idx] - pre[idx]) / LAMPORTS_PER_SOL
        deltas[address] = delta
    return deltas


def _detect_treasury(
    *,
    accounts: List[str],
    meta: Dict[str, Any],
    signature: str,
    block_time: Optional[int],
    treasury_accounts: List[str],
    threshold_sol: float,
    critical_sol: float,
) -> List[Dict[str, Any]]:
    if not treasury_accounts:
        return []
    if not any(account in accounts for account in treasury_accounts):
        return []

    deltas = _lamport_delta(accounts, meta, treasury_accounts)
    if deltas:
        max_delta = max(deltas.values())
        if max_delta >= critical_sol:
            impact = 4
        elif max_delta >= threshold_sol:
            impact = 3
        else:
            return []
        return [
            _base_event(
                star="treasury",
                action="treasury_move",
                impact_level=impact,
                source_signature=signature,
                valid_from=_iso_time(block_time),
                extra={"largest_delta_sol": round(max_delta, 3)},
            )
        ]

    return [
        _base_event(
            star="treasury",
            action="treasury_activity",
            impact_level=1,
            source_signature=signature,
            valid_from=_iso_time(block_time),
        )
    ]


def _events_from_transaction(signature: str, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    transaction = entry.get("transaction") or {}
    message = transaction.get("message") or {}
    meta = entry.get("meta") or {}
    logs = meta.get("logMessages") or []
    accounts = _extract_accounts(message, meta)
    program_ids = _extract_program_ids(message, accounts)

    config = load_config()
    events: List[Dict[str, Any]] = []
    events.extend(
        _detect_governance(
            program_ids=program_ids,
            logs=logs,
            signature=signature,
            block_time=entry.get("blockTime"),
            governance_programs=config.governance_programs,
        )
    )
    events.extend(
        _detect_program(
            program_ids=program_ids,
            logs=logs,
            signature=signature,
            block_time=entry.get("blockTime"),
            tracked_programs=config.tracked_programs,
        )
    )
    events.extend(
        _detect_supply(
            program_ids=program_ids,
            logs=logs,
            accounts=accounts,
            signature=signature,
            block_time=entry.get("blockTime"),
            tracked_mints=config.tracked_mints,
        )
    )
    events.extend(
        _detect_treasury(
            accounts=accounts,
            meta=meta,
            signature=signature,
            block_time=entry.get("blockTime"),
            treasury_accounts=config.treasury_accounts,
            threshold_sol=config.treasury_threshold_sol,
            critical_sol=config.treasury_critical_sol,
        )
    )
    return events


def refresh_from_rpc(max_signatures: int = 20) -> Dict[str, Any]:
    config = load_config()
    if not config.rpc_url:
        raise SolanaRpcError("SOLANA_RPC_URL is not configured.")

    watch_addresses = set(
        config.governance_programs
        + config.tracked_programs
        + config.tracked_mints
        + config.treasury_accounts
    )
    if not watch_addresses:
        return {
            "ok": False,
            "detail": "No watch addresses configured.",
            "raw_added": 0,
            "events_added": 0,
        }

    raw_before = raw_count()
    events_before = event_count()
    seen_signatures = set()

    for address in watch_addresses:
        signatures = get_signatures_for_address(address, limit=max_signatures)
        for entry in signatures:
            signature = entry.get("signature")
            if not signature or signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            tx = get_transaction(signature)
            if not tx:
                continue
            message = tx.get("transaction", {}).get("message", {})
            meta = tx.get("meta", {})
            accounts = _extract_accounts(message, meta)
            program_ids = _extract_program_ids(message, accounts)
            instructions = message.get("instructions") or []
            logs = meta.get("logMessages") or []
            raw_payload = {
                "signature": signature,
                "slot": tx.get("slot"),
                "block_time": tx.get("blockTime"),
                "program_ids": program_ids,
                "accounts": accounts,
                "instructions": instructions,
                "logs": logs,
                "raw": tx,
            }
            inserted = record_raw(raw_payload)
            if not inserted:
                continue
            for event in _events_from_transaction(signature, tx):
                record_event(event)

    set_last_ingest_at()
    return {
        "ok": True,
        "detail": "Ingest complete.",
        "raw_added": raw_count() - raw_before,
        "events_added": event_count() - events_before,
    }

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
    get_cursor,
    set_cursor,
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


def _cursor_key(address: str) -> str:
    return f"sig:{address}"


def _load_last_signature(address: str) -> str:
    cursor = get_cursor(_cursor_key(address)) or {}
    signature = cursor.get("signature")
    if not signature:
        return ""
    return str(signature).strip()


def _store_last_signature(address: str, signature: str) -> None:
    if not signature:
        return
    set_cursor(_cursor_key(address), {"signature": signature})


def _collect_new_signatures(
    *,
    address: str,
    limit: int,
    max_pages: int,
    last_signature: str,
) -> tuple[List[Dict[str, Any]], str]:
    before = None
    newest = ""
    entries: List[Dict[str, Any]] = []
    pages = 0
    while True:
        batch = get_signatures_for_address(address, limit=limit, before=before)
        if not batch:
            break
        if not newest:
            newest = str(batch[0].get("signature") or "").strip()
        stop = False
        for entry in batch:
            signature = str(entry.get("signature") or "").strip()
            if not signature:
                continue
            if last_signature and signature == last_signature:
                stop = True
                break
            entries.append(entry)
        if stop:
            break
        if len(batch) < limit:
            break
        before = str(batch[-1].get("signature") or "").strip()
        if not before:
            break
        pages += 1
        if max_pages > 0 and pages >= max_pages:
            break
    return entries, newest


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
    accounts: List[str],
    signature: str,
    block_time: Optional[int],
    governance_programs: List[str],
    governance_realms: List[str],
) -> List[Dict[str, Any]]:
    if not governance_programs:
        return []
    if not any(pid in governance_programs for pid in program_ids):
        return []
    if governance_realms and not any(realm in accounts for realm in governance_realms):
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
    meta: Dict[str, Any],
    message: Dict[str, Any],
    signature: str,
    block_time: Optional[int],
    tracked_mints: List[str],
    unlock_threshold: float,
    allow_mint: bool,
) -> List[Dict[str, Any]]:
    if TOKEN_PROGRAM_ID not in program_ids:
        return []
    if tracked_mints and not any(mint in accounts for mint in tracked_mints):
        return []

    events: List[Dict[str, Any]] = []
    events.extend(
        _detect_supply_authority(
            message=message,
            tracked_mints=tracked_mints,
            signature=signature,
            block_time=block_time,
        )
    )
    if not events and _log_contains(logs, "instruction: setauthority"):
        events.append(
            _base_event(
                star="supply",
                action="authority_changed",
                impact_level=4,
                source_signature=signature,
                valid_from=_iso_time(block_time),
                extra={"instruction": "setAuthority"},
            )
        )
    if not events and allow_mint and _log_contains(logs, "instruction: mintto"):
        events.append(
            _base_event(
                star="supply",
                action="minted",
                impact_level=3,
                source_signature=signature,
                valid_from=_iso_time(block_time),
            )
        )
    if unlock_threshold > 0:
        unlock_event = _detect_supply_unlock(
            meta=meta,
            tracked_mints=tracked_mints,
            threshold=unlock_threshold,
            signature=signature,
            block_time=block_time,
        )
        if unlock_event:
            events.append(unlock_event)
    return events


def _authority_action(authority_type: str) -> str:
    lowered = authority_type.lower()
    if "mint" in lowered:
        return "mint_authority_changed"
    if "freeze" in lowered:
        return "freeze_authority_changed"
    return "authority_changed"


def _detect_supply_authority(
    *,
    message: Dict[str, Any],
    tracked_mints: List[str],
    signature: str,
    block_time: Optional[int],
) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for instr in message.get("instructions") or []:
        if not isinstance(instr, dict):
            continue
        program = instr.get("program") or ""
        program_id = instr.get("programId") or ""
        if program != "spl-token" and program_id != TOKEN_PROGRAM_ID:
            continue
        parsed = instr.get("parsed") or {}
        if parsed.get("type") != "setAuthority":
            continue
        info = parsed.get("info") or {}
        account = str(info.get("account") or info.get("mint") or "").strip()
        if tracked_mints and account not in tracked_mints:
            continue
        action = _authority_action(str(info.get("authorityType") or ""))
        events.append(
            _base_event(
                star="supply",
                action=action,
                impact_level=4,
                source_signature=signature,
                valid_from=_iso_time(block_time),
                extra={
                    "authority_type": info.get("authorityType"),
                    "account": account,
                },
            )
        )
    return events


def _token_balance_total(entries: List[Dict[str, Any]]) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    for item in entries:
        mint = item.get("mint")
        amount_info = item.get("uiTokenAmount") or {}
        raw_amount = amount_info.get("amount")
        decimals = amount_info.get("decimals", 0)
        if mint is None or raw_amount is None:
            continue
        try:
            amount = int(raw_amount) / (10 ** int(decimals))
        except (ValueError, TypeError):
            continue
        totals[mint] = totals.get(mint, 0.0) + amount
    return totals


def _detect_supply_unlock(
    *,
    meta: Dict[str, Any],
    tracked_mints: List[str],
    threshold: float,
    signature: str,
    block_time: Optional[int],
) -> Dict[str, Any] | None:
    pre = meta.get("preTokenBalances") or []
    post = meta.get("postTokenBalances") or []
    pre_totals = _token_balance_total(pre)
    post_totals = _token_balance_total(post)
    for mint in tracked_mints:
        delta = post_totals.get(mint, 0.0) - pre_totals.get(mint, 0.0)
        if delta >= threshold:
            return _base_event(
                star="supply",
                action="supply_unlocked",
                impact_level=4,
                source_signature=signature,
                valid_from=_iso_time(block_time),
                extra={"mint": mint, "delta": round(delta, 4)},
            )
    return None


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
            accounts=accounts,
            signature=signature,
            block_time=entry.get("blockTime"),
            governance_programs=config.governance_programs,
            governance_realms=config.governance_realms,
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
            meta=meta,
            message=message,
            signature=signature,
            block_time=entry.get("blockTime"),
            tracked_mints=config.tracked_mints,
            unlock_threshold=config.supply_unlock_threshold,
            allow_mint=config.supply_allow_mint,
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


def refresh_from_rpc(max_signatures: int | None = None) -> Dict[str, Any]:
    config = load_config()
    if not config.rpc_url:
        raise SolanaRpcError("SOLANA_RPC_URL is not configured.")

    governance_watch = (
        config.governance_realms if config.governance_realms else config.governance_programs
    )
    watch_addresses = set(
        governance_watch
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

    batch_limit = max_signatures or config.signature_batch_limit
    max_pages = config.signature_max_pages

    for address in watch_addresses:
        last_signature = _load_last_signature(address)
        signatures, newest_signature = _collect_new_signatures(
            address=address,
            limit=batch_limit,
            max_pages=max_pages,
            last_signature=last_signature,
        )
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
        if newest_signature:
            _store_last_signature(address, newest_signature)

    set_last_ingest_at()
    return {
        "ok": True,
        "detail": "Ingest complete.",
        "raw_added": raw_count() - raw_before,
        "events_added": event_count() - events_before,
    }

from __future__ import annotations

import hmac
import hashlib
import os
import smtplib
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from email.message import EmailMessage
from typing import Any, Dict, Tuple

from universe.satellite_crypto_orbit import COIN_IDS, ensure_latest_snapshot
from universe.satellite_finance_orbit import EXCHANGE_CODES, fetch_latest_snapshot

try:  # Optional if running without DB yet.
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None

try:  # Optional if Stripe is not configured.
    import stripe
except Exception:  # pragma: no cover
    stripe = None


FREE_PLAN = "free"
PRO_PLAN = "pro"

FREQUENCIES = {
    "daily": 24 * 60 * 60,
    "hourly": 60 * 60,
}

COMPARATORS = {"gt", "lt", "change_abs", "change_pct"}

FINANCE_SOURCE = "finance-orbit"
CRYPTO_SOURCE = "crypto-orbit"


def _flag(name: str, default: str = "off") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def monitoring_enabled() -> bool:
    return _flag("SPARKY_MONITORING", "on")


def monitor_price_label() -> str:
    return os.getenv("SPARKY_MONITOR_PRICE_LABEL", "Pro (hourly)")


def _dsn() -> str | None:
    return os.getenv("SPARKY_DB_DSN") or os.getenv("DATABASE_URL")


def _db_available() -> bool:
    return bool(_dsn()) and psycopg is not None


def _smtp_settings() -> Dict[str, Any]:
    host = os.getenv("SPARKY_SMTP_HOST", "").strip()
    port = int(os.getenv("SPARKY_SMTP_PORT", "587"))
    user = os.getenv("SPARKY_SMTP_USER", "").strip()
    password = os.getenv("SPARKY_SMTP_PASSWORD", "").strip()
    sender = os.getenv("SPARKY_SMTP_FROM", "").strip()
    tls = _flag("SPARKY_SMTP_TLS", "on")
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "sender": sender,
        "tls": tls,
    }


def smtp_configured() -> bool:
    settings = _smtp_settings()
    return bool(settings["host"] and settings["sender"])


def stripe_configured() -> bool:
    return bool(
        stripe is not None
        and os.getenv("SPARKY_STRIPE_SECRET_KEY")
        and os.getenv("SPARKY_STRIPE_PRICE_ID")
    )


def public_base_url(default: str | None = None) -> str:
    value = os.getenv("SPARKY_PUBLIC_BASE_URL", "").strip()
    if value:
        return value.rstrip("/")
    if default:
        return default.rstrip("/")
    return ""


def _monitor_secret() -> str:
    return os.getenv("SPARKY_MONITOR_SECRET", "").strip()


def _watcher_token(watcher_id: str) -> str | None:
    secret = _monitor_secret()
    if not secret:
        return None
    digest = hmac.new(
        secret.encode("utf-8"),
        watcher_id.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest


def build_unsubscribe_url(watcher_id: str, base_url: str) -> str | None:
    token = _watcher_token(watcher_id)
    if not token:
        return None
    return f"{base_url}/monitoring/unsubscribe?id={watcher_id}&sig={token}"


def finance_metrics(snapshot: Dict[str, Any] | None = None) -> list[Dict[str, str]]:
    metrics = []
    for code in EXCHANGE_CODES:
        key = f"{code}_CZK"
        metrics.append({"key": key, "label": f"{code}/CZK rate"})
    metrics.append({"key": "REPO_RATE", "label": "CNB repo rate"})
    return metrics


def crypto_metrics(snapshot: Dict[str, Any] | None = None) -> list[Dict[str, str]]:
    entries = snapshot.get("data", []) if snapshot else []
    by_key = {item.get("key"): item for item in entries if isinstance(item, dict)}
    metrics = []
    for coin_id in COIN_IDS:
        entry = by_key.get(coin_id, {})
        symbol = str(entry.get("symbol") or coin_id).upper()
        metrics.append({"key": f"{coin_id}.price", "label": f"{symbol} price (USD)"})
    return metrics


def _parse_decimal(value: str) -> Decimal | None:
    raw = str(value).strip().replace(" ", "")
    if not raw:
        return None
    if "," in raw and "." not in raw:
        raw = raw.replace(",", ".")
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


def parse_threshold(value: str) -> Decimal | None:
    return _parse_decimal(value)


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _normalize_comparator(value: str) -> str | None:
    normalized = value.strip().lower()
    if normalized in COMPARATORS:
        return normalized
    return None


def _normalize_frequency(value: str) -> str | None:
    normalized = value.strip().lower()
    if normalized in FREQUENCIES:
        return normalized
    return None


def _allowed_metric(source_key: str, metric_key: str) -> bool:
    if source_key == FINANCE_SOURCE:
        allowed = {f"{code}_CZK" for code in EXCHANGE_CODES} | {"REPO_RATE"}
        return metric_key in allowed
    if source_key == CRYPTO_SOURCE:
        return any(metric_key == f"{coin}.price" for coin in COIN_IDS)
    return False


def metric_allowed(source_key: str, metric_key: str) -> bool:
    return _allowed_metric(source_key, metric_key)


def _ensure_schema(conn: Any) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sparky_watchers (
            id UUID PRIMARY KEY,
            email TEXT NOT NULL,
            source_key TEXT NOT NULL,
            metric_key TEXT NOT NULL,
            comparator TEXT NOT NULL,
            threshold NUMERIC,
            frequency TEXT NOT NULL,
            plan TEXT NOT NULL,
            status TEXT NOT NULL,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_checked_at TIMESTAMPTZ,
            last_value NUMERIC,
            last_triggered_at TIMESTAMPTZ
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sparky_watchers_status
        ON sparky_watchers (status);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sparky_watchers_email
        ON sparky_watchers (email);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sparky_watchers_subscription
        ON sparky_watchers (stripe_subscription_id);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sparky_watcher_deliveries (
            id UUID PRIMARY KEY,
            watcher_id UUID NOT NULL REFERENCES sparky_watchers(id) ON DELETE CASCADE,
            channel TEXT NOT NULL,
            status TEXT NOT NULL,
            detail TEXT,
            payload JSONB,
            sent_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )


def _free_limit() -> int:
    return int(os.getenv("SPARKY_MONITOR_FREE_LIMIT", "1"))


def _pro_limit() -> int:
    return int(os.getenv("SPARKY_MONITOR_PRO_LIMIT", "50"))


def create_free_watcher(
    *,
    email: str,
    source_key: str,
    metric_key: str,
    comparator: str,
    threshold: Decimal,
    frequency: str,
) -> Tuple[str | None, str | None]:
    if not _db_available():
        return None, "db_unavailable"
    if not smtp_configured():
        return None, "email_not_configured"
    if not email or "@" not in email:
        return None, "invalid_email"
    if comparator not in COMPARATORS:
        return None, "invalid_request"
    if frequency not in FREQUENCIES:
        return None, "invalid_request"
    if not _allowed_metric(source_key, metric_key):
        return None, "invalid_metric"

    watcher_id = str(uuid.uuid4())
    normalized_email = _normalize_email(email)
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        _ensure_schema(conn)
        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM sparky_watchers
            WHERE email = %s AND plan = %s AND status = 'active';
            """,
            (normalized_email, FREE_PLAN),
        ).fetchone()[0]
        if count >= _free_limit():
            return None, "limit_reached"
        existing = conn.execute(
            """
            SELECT id
            FROM sparky_watchers
            WHERE email = %s
              AND source_key = %s
              AND metric_key = %s
              AND comparator = %s
              AND threshold = %s
              AND frequency = %s
              AND status = 'active'
            LIMIT 1;
            """,
            (
                normalized_email,
                source_key,
                metric_key,
                comparator,
                threshold,
                frequency,
            ),
        ).fetchone()
        if existing:
            return existing[0], "duplicate"
        conn.execute(
            """
            INSERT INTO sparky_watchers (
                id, email, source_key, metric_key, comparator, threshold, frequency,
                plan, status, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, 'active', now()
            );
            """,
            (
                watcher_id,
                normalized_email,
                source_key,
                metric_key,
                comparator,
                threshold,
                frequency,
                FREE_PLAN,
            ),
        )
    return watcher_id, None


def create_paid_watcher(
    *,
    email: str,
    source_key: str,
    metric_key: str,
    comparator: str,
    threshold: Decimal,
    frequency: str,
    subscription_id: str | None,
    customer_id: str | None,
) -> Tuple[str | None, str | None]:
    if not _db_available():
        return None, "db_unavailable"
    if not email or "@" not in email:
        return None, "invalid_email"
    if comparator not in COMPARATORS:
        return None, "invalid_request"
    if frequency not in FREQUENCIES:
        return None, "invalid_request"
    if not _allowed_metric(source_key, metric_key):
        return None, "invalid_metric"
    if subscription_id is None:
        return None, "missing_subscription"

    watcher_id = str(uuid.uuid4())
    normalized_email = _normalize_email(email)
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        _ensure_schema(conn)
        existing = conn.execute(
            """
            SELECT id
            FROM sparky_watchers
            WHERE email = %s
              AND source_key = %s
              AND metric_key = %s
              AND comparator = %s
              AND threshold = %s
              AND frequency = %s
              AND status = 'active'
            LIMIT 1;
            """,
            (
                normalized_email,
                source_key,
                metric_key,
                comparator,
                threshold,
                frequency,
            ),
        ).fetchone()
        if existing:
            return existing[0], "duplicate"
        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM sparky_watchers
            WHERE email = %s AND plan = %s AND status = 'active';
            """,
            (normalized_email, PRO_PLAN),
        ).fetchone()[0]
        if count >= _pro_limit():
            return None, "limit_reached"
        conn.execute(
            """
            INSERT INTO sparky_watchers (
                id, email, source_key, metric_key, comparator, threshold, frequency,
                plan, status, stripe_customer_id, stripe_subscription_id, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, 'active', %s, %s, now()
            );
            """,
            (
                watcher_id,
                normalized_email,
                source_key,
                metric_key,
                comparator,
                threshold,
                frequency,
                PRO_PLAN,
                customer_id,
                subscription_id,
            ),
        )
    return watcher_id, None


def active_subscription_for_email(email: str) -> str | None:
    if not _db_available():
        return None
    normalized_email = _normalize_email(email)
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        _ensure_schema(conn)
        row = conn.execute(
            """
            SELECT stripe_subscription_id
            FROM sparky_watchers
            WHERE email = %s
              AND plan = %s
              AND status = 'active'
              AND stripe_subscription_id IS NOT NULL
            LIMIT 1;
            """,
            (normalized_email, PRO_PLAN),
        ).fetchone()
    if not row:
        return None
    return row[0]


def update_watchers_status(subscription_id: str, status: str) -> None:
    if not _db_available():
        return
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            UPDATE sparky_watchers
            SET status = %s
            WHERE stripe_subscription_id = %s;
            """,
            (status, subscription_id),
        )


def create_checkout_session(
    *,
    email: str,
    source_key: str,
    metric_key: str,
    comparator: str,
    threshold: Decimal,
    frequency: str,
    success_url: str,
    cancel_url: str,
) -> Tuple[str | None, str | None]:
    if stripe is None:
        return None, "stripe_missing"
    secret_key = os.getenv("SPARKY_STRIPE_SECRET_KEY", "").strip()
    price_id = os.getenv("SPARKY_STRIPE_PRICE_ID", "").strip()
    if not secret_key or not price_id:
        return None, "stripe_not_configured"
    stripe.api_key = secret_key
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        customer_email=email,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "kind": "watcher",
            "source_key": source_key,
            "metric_key": metric_key,
            "comparator": comparator,
            "threshold": str(threshold),
            "frequency": frequency,
            "email": email,
        },
    )
    return session.url, None


def verify_stripe_event(payload: bytes, sig_header: str) -> Tuple[Any | None, str | None]:
    if stripe is None:
        return None, "stripe_missing"
    secret = os.getenv("SPARKY_STRIPE_WEBHOOK_SECRET", "").strip()
    if not secret:
        return None, "stripe_not_configured"
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except Exception as exc:
        return None, str(exc)
    return event, None


def apply_stripe_event(event: Any) -> None:
    event_type = str(event.get("type", ""))
    data = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        if data.get("mode") != "subscription":
            return
        metadata = data.get("metadata") or {}
        if metadata.get("kind") != "watcher":
            return
        email = (
            data.get("customer_email")
            or (data.get("customer_details") or {}).get("email")
            or metadata.get("email")
            or ""
        )
        source_key = metadata.get("source_key", "")
        metric_key = metadata.get("metric_key", "")
        comparator = metadata.get("comparator", "")
        threshold = _parse_decimal(metadata.get("threshold", ""))
        frequency = metadata.get("frequency", "")
        if not threshold:
            return
        create_paid_watcher(
            email=email,
            source_key=source_key,
            metric_key=metric_key,
            comparator=comparator,
            threshold=threshold,
            frequency=frequency,
            subscription_id=data.get("subscription"),
            customer_id=data.get("customer"),
        )
        return

    if event_type.startswith("customer.subscription."):
        subscription_id = data.get("id")
        status = str(data.get("status", ""))
        if not subscription_id:
            return
        if status == "active":
            update_watchers_status(subscription_id, "active")
        else:
            update_watchers_status(subscription_id, "paused")


def _metric_value(
    source_key: str,
    metric_key: str,
    finance_snapshot: Dict[str, Any] | None,
    crypto_snapshot: Dict[str, Any] | None,
) -> Tuple[Decimal | None, str, str]:
    label = metric_key
    unit = ""
    if source_key == FINANCE_SOURCE and finance_snapshot:
        data_entries = finance_snapshot.get("data", [])
        for entry in data_entries:
            if entry.get("key") == metric_key:
                value = _parse_decimal(entry.get("value", ""))
                label = metric_key.replace("_", "/")
                unit = str(entry.get("unit") or "")
                return value, label, unit
        return None, label, unit

    if source_key == CRYPTO_SOURCE and crypto_snapshot:
        if "." in metric_key:
            coin_id, field = metric_key.split(".", 1)
        else:
            coin_id, field = metric_key, "price"
        data_entries = crypto_snapshot.get("data", [])
        for entry in data_entries:
            if entry.get("key") != coin_id:
                continue
            value = _parse_decimal(entry.get(field, ""))
            symbol = str(entry.get("symbol") or coin_id).upper()
            if field == "price":
                label = f"{symbol} price"
                unit = "USD"
            elif field == "change_24h_pct":
                label = f"{symbol} 24h change"
                unit = "%"
            else:
                label = f"{symbol} {field}"
            return value, label, unit
    return None, label, unit


def _should_trigger(
    comparator: str,
    current_value: Decimal,
    last_value: Decimal | None,
    threshold: Decimal,
) -> bool:
    if comparator == "gt":
        return current_value > threshold
    if comparator == "lt":
        return current_value < threshold
    if comparator == "change_abs":
        if last_value is None:
            return False
        return abs(current_value - last_value) >= threshold
    if comparator == "change_pct":
        if last_value is None or last_value == 0:
            return False
        change = abs((current_value - last_value) / last_value) * Decimal("100")
        return change >= threshold
    return False


def _frequency_due(last_checked: datetime | None, frequency: str) -> bool:
    interval = FREQUENCIES.get(frequency)
    if interval is None:
        return False
    if last_checked is None:
        return True
    return datetime.now(timezone.utc) - last_checked >= timedelta(seconds=interval)


def _notify_due(last_triggered: datetime | None, frequency: str) -> bool:
    if last_triggered is None:
        return True
    interval = FREQUENCIES.get(frequency)
    if interval is None:
        return True
    return datetime.now(timezone.utc) - last_triggered >= timedelta(seconds=interval)


def _send_email(to_email: str, subject: str, body: str) -> Tuple[bool, str | None]:
    settings = _smtp_settings()
    if not settings["host"] or not settings["sender"]:
        return False, "SMTP not configured"
    message = EmailMessage()
    message["From"] = settings["sender"]
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    try:
        with smtplib.SMTP(settings["host"], settings["port"], timeout=12) as server:
            if settings["tls"]:
                server.starttls()
            if settings["user"] and settings["password"]:
                server.login(settings["user"], settings["password"])
            server.send_message(message)
        return True, None
    except Exception as exc:
        return False, str(exc)


def _record_delivery(
    conn: Any,
    watcher_id: str,
    status: str,
    detail: str | None,
    payload: Dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO sparky_watcher_deliveries (
            id, watcher_id, channel, status, detail, payload, sent_at
        ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, now());
        """,
        (
            str(uuid.uuid4()),
            watcher_id,
            "email",
            status,
            detail,
            payload,
        ),
    )


def run_watchers() -> Dict[str, int]:
    results = {"checked": 0, "triggered": 0, "sent": 0, "failed": 0}
    if not monitoring_enabled():
        return results
    if not _db_available():
        return results

    finance_snapshot: Dict[str, Any] | None = None
    crypto_snapshot: Dict[str, Any] | None = None
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        _ensure_schema(conn)
        watchers = conn.execute(
            """
            SELECT
                id, email, source_key, metric_key, comparator, threshold,
                frequency, status, last_checked_at, last_value, last_triggered_at
            FROM sparky_watchers
            WHERE status = 'active';
            """
        ).fetchall()

        for row in watchers:
            (
                watcher_id,
                email,
                source_key,
                metric_key,
                comparator,
                threshold,
                frequency,
                status,
                last_checked_at,
                last_value,
                last_triggered_at,
            ) = row
            if status != "active":
                continue
            if not _frequency_due(last_checked_at, frequency):
                continue

            results["checked"] += 1
            if source_key == FINANCE_SOURCE and finance_snapshot is None:
                finance_snapshot, _ = fetch_latest_snapshot()
            if source_key == CRYPTO_SOURCE and crypto_snapshot is None:
                crypto_snapshot, _ = ensure_latest_snapshot()

            current_value, label, unit = _metric_value(
                source_key,
                metric_key,
                finance_snapshot,
                crypto_snapshot,
            )
            if current_value is None:
                conn.execute(
                    """
                    UPDATE sparky_watchers
                    SET last_checked_at = now()
                    WHERE id = %s;
                    """,
                    (watcher_id,),
                )
                _record_delivery(
                    conn,
                    str(watcher_id),
                    "failed",
                    "Metric unavailable",
                    {"metric_key": metric_key, "source_key": source_key},
                )
                results["failed"] += 1
                continue

            threshold_value = _parse_decimal(threshold)
            if threshold_value is None:
                threshold_value = _parse_decimal(str(threshold))
            if threshold_value is None:
                conn.execute(
                    """
                    UPDATE sparky_watchers
                    SET last_checked_at = now()
                    WHERE id = %s;
                    """,
                    (watcher_id,),
                )
                continue

            last_value_dec = _parse_decimal(last_value) if last_value is not None else None
            triggered = _should_trigger(
                comparator,
                current_value,
                last_value_dec,
                threshold_value,
            )

            should_notify = triggered and _notify_due(last_triggered_at, frequency)
            if should_notify and smtp_configured():
                base_url = public_base_url()
                unsubscribe_url = (
                    build_unsubscribe_url(str(watcher_id), base_url)
                    if base_url
                    else None
                )
                subject = f"Sparky alert: {label}"
                body_lines = [
                    f"Metric: {label}",
                    f"Current value: {current_value}",
                    f"Threshold: {threshold_value}",
                    f"Condition: {comparator}",
                    "",
                    f"Source: {source_key}",
                ]
                if unit:
                    body_lines.insert(2, f"Unit: {unit}")
                if unsubscribe_url:
                    body_lines.extend(["", f"Stop alerts: {unsubscribe_url}"])
                ok, error = _send_email(email, subject, "\n".join(body_lines))
                if ok:
                    results["sent"] += 1
                    results["triggered"] += 1
                    conn.execute(
                        """
                        UPDATE sparky_watchers
                        SET last_checked_at = now(),
                            last_value = %s,
                            last_triggered_at = now()
                        WHERE id = %s;
                        """,
                        (current_value, watcher_id),
                    )
                    _record_delivery(
                        conn,
                        str(watcher_id),
                        "sent",
                        None,
                        {
                            "metric_key": metric_key,
                            "source_key": source_key,
                            "current_value": str(current_value),
                        },
                    )
                else:
                    results["failed"] += 1
                    conn.execute(
                        """
                        UPDATE sparky_watchers
                        SET last_checked_at = now(),
                            last_value = %s
                        WHERE id = %s;
                        """,
                        (current_value, watcher_id),
                    )
                    _record_delivery(
                        conn,
                        str(watcher_id),
                        "failed",
                        error,
                        {
                            "metric_key": metric_key,
                            "source_key": source_key,
                            "current_value": str(current_value),
                        },
                    )
            else:
                conn.execute(
                    """
                    UPDATE sparky_watchers
                    SET last_checked_at = now(),
                        last_value = %s
                    WHERE id = %s;
                    """,
                    (current_value, watcher_id),
                )
    return results


def remove_watcher(watcher_id: str, signature: str | None) -> bool:
    token = _watcher_token(watcher_id)
    if not token or signature != token:
        return False
    if not _db_available():
        return False
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            UPDATE sparky_watchers
            SET status = 'inactive'
            WHERE id = %s;
            """,
            (watcher_id,),
        )
    return True

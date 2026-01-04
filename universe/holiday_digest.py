from __future__ import annotations

import hmac
import hashlib
import json
import os
import smtplib
import uuid
from calendar import month_name
from datetime import date, datetime, timezone
from email.message import EmailMessage
from typing import Any, Dict, List, Tuple

from universe.satellite_bavaria_holiday_orbit import ensure_latest_snapshot

try:  # Optional if running without DB yet.
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None

try:  # Optional if Stripe is not configured.
    import stripe
except Exception:  # pragma: no cover
    stripe = None


HOLIDAY_PLAN = "holiday_digest"


def _flag(name: str, default: str = "off") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


def holiday_digest_enabled() -> bool:
    return _flag("SPARKY_HOLIDAY_DIGEST", "on")


def holiday_price_label() -> str:
    return os.getenv("SPARKY_HOLIDAY_PRICE_LABEL", "Monthly alerts")


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


def _price_id() -> str:
    return (
        os.getenv("SPARKY_STRIPE_HOLIDAY_PRICE_ID", "").strip()
        or os.getenv("SPARKY_STRIPE_PRICE_ID", "").strip()
    )


def stripe_configured() -> bool:
    return bool(stripe is not None and os.getenv("SPARKY_STRIPE_SECRET_KEY") and _price_id())


def db_available() -> bool:
    return _db_available()


def _digest_secret() -> str:
    return os.getenv("SPARKY_HOLIDAY_DIGEST_SECRET", "").strip()


def _digest_token(subscriber_id: str) -> str | None:
    secret = _digest_secret()
    if not secret:
        return None
    return hmac.new(
        secret.encode("utf-8"),
        subscriber_id.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def build_unsubscribe_url(subscriber_id: str, base_url: str) -> str | None:
    token = _digest_token(subscriber_id)
    if not token:
        return None
    return f"{base_url}/satellites/bavaria-holiday-orbit/unsubscribe?id={subscriber_id}&sig={token}"


def _ensure_schema(conn: Any) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sparky_holiday_subscribers (
            id UUID PRIMARY KEY,
            email TEXT NOT NULL,
            status TEXT NOT NULL,
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_sent_at TIMESTAMPTZ
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sparky_holiday_sub_status
        ON sparky_holiday_subscribers (status);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sparky_holiday_sub_email
        ON sparky_holiday_subscribers (email);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sparky_holiday_sub_subscription
        ON sparky_holiday_subscribers (stripe_subscription_id);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sparky_holiday_deliveries (
            id UUID PRIMARY KEY,
            subscriber_id UUID NOT NULL REFERENCES sparky_holiday_subscribers(id) ON DELETE CASCADE,
            status TEXT NOT NULL,
            detail TEXT,
            payload JSONB,
            sent_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )


def create_checkout_session(email: str, success_url: str, cancel_url: str) -> Tuple[str | None, str | None]:
    if stripe is None:
        return None, "stripe_missing"
    secret_key = os.getenv("SPARKY_STRIPE_SECRET_KEY", "").strip()
    price_id = _price_id()
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
            "kind": HOLIDAY_PLAN,
            "email": email,
        },
    )
    return session.url, None


def active_subscription_for_email(email: str) -> str | None:
    if not _db_available():
        return None
    normalized_email = email.strip().lower()
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        _ensure_schema(conn)
        row = conn.execute(
            """
            SELECT stripe_subscription_id
            FROM sparky_holiday_subscribers
            WHERE email = %s AND status = 'active' AND stripe_subscription_id IS NOT NULL
            LIMIT 1;
            """,
            (normalized_email,),
        ).fetchone()
    if not row:
        return None
    return row[0]


def create_subscription(email: str, subscription_id: str | None, customer_id: str | None) -> Tuple[str | None, str | None]:
    if not _db_available():
        return None, "db_unavailable"
    if not email or "@" not in email:
        return None, "invalid_email"
    if subscription_id is None:
        return None, "missing_subscription"

    subscriber_id = str(uuid.uuid4())
    normalized_email = email.strip().lower()
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        _ensure_schema(conn)
        existing = conn.execute(
            """
            SELECT id
            FROM sparky_holiday_subscribers
            WHERE stripe_subscription_id = %s
            LIMIT 1;
            """,
            (subscription_id,),
        ).fetchone()
        if existing:
            return existing[0], None
        conn.execute(
            """
            INSERT INTO sparky_holiday_subscribers (
                id, email, status, stripe_customer_id, stripe_subscription_id, created_at
            ) VALUES (%s, %s, 'active', %s, %s, now());
            """,
            (subscriber_id, normalized_email, customer_id, subscription_id),
        )
    return subscriber_id, None


def update_subscription_status(subscription_id: str, status: str) -> None:
    if not _db_available():
        return
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            UPDATE sparky_holiday_subscribers
            SET status = %s
            WHERE stripe_subscription_id = %s;
            """,
            (status, subscription_id),
        )


def apply_stripe_event(event: Any) -> None:
    event_type = str(event.get("type", ""))
    data = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        if data.get("mode") != "subscription":
            return
        metadata = data.get("metadata") or {}
        if metadata.get("kind") != HOLIDAY_PLAN:
            return
        email = (
            data.get("customer_email")
            or (data.get("customer_details") or {}).get("email")
            or metadata.get("email")
            or ""
        )
        create_subscription(
            email=email,
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
            update_subscription_status(subscription_id, "active")
        else:
            update_subscription_status(subscription_id, "inactive")


def _next_month(target_date: date) -> date:
    year = target_date.year
    month = target_date.month + 1
    if month == 13:
        month = 1
        year += 1
    return date(year, month, 1)


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
    subscriber_id: str,
    status: str,
    detail: str | None,
    payload: Dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO sparky_holiday_deliveries (
            id, subscriber_id, status, detail, payload, sent_at
        ) VALUES (%s, %s, %s, %s, %s::jsonb, now());
        """,
        (str(uuid.uuid4()), subscriber_id, status, detail, json.dumps(payload)),
    )


def run_holiday_digest() -> Dict[str, int]:
    results = {"checked": 0, "sent": 0, "failed": 0}
    if not holiday_digest_enabled():
        return results
    if not _db_available():
        return results
    if not smtp_configured():
        return results

    snapshot, error = ensure_latest_snapshot()
    if error or not snapshot:
        return results

    next_month_date = _next_month(date.today())
    month_label = month_name[next_month_date.month]
    year_label = next_month_date.year
    target_prefix = f"{year_label}-{next_month_date.month:02d}-"

    holidays: List[Dict[str, Any]] = []
    for entry in snapshot.get("data", []):
        if not isinstance(entry, dict):
            continue
        if str(entry.get("date", "")).startswith(target_prefix):
            holidays.append(entry)

    with psycopg.connect(_dsn(), autocommit=True) as conn:
        _ensure_schema(conn)
        subscribers = conn.execute(
            """
            SELECT id, email, last_sent_at
            FROM sparky_holiday_subscribers
            WHERE status = 'active';
            """
        ).fetchall()

        for subscriber_id, email, last_sent_at in subscribers:
            if last_sent_at and last_sent_at.year == year_label and last_sent_at.month == next_month_date.month:
                continue
            results["checked"] += 1

            body_lines = [
                f"Holidays for {month_label} {year_label} (CZ + Bavaria)",
                "",
            ]
            if holidays:
                for entry in holidays:
                    marker = " (overlap)" if entry.get("overlap") else ""
                    body_lines.append(
                        f"- {entry.get('date')} · {entry.get('local_name') or entry.get('name')}"
                        f" · {entry.get('country')}{marker}"
                    )
            else:
                body_lines.append("No holidays found for this month.")

            base_url = os.getenv("SPARKY_PUBLIC_BASE_URL", "").strip().rstrip("/")
            unsubscribe_url = build_unsubscribe_url(str(subscriber_id), base_url) if base_url else None
            if unsubscribe_url:
                body_lines.extend(["", f"Unsubscribe: {unsubscribe_url}"])

            ok, detail = _send_email(
                email,
                f"Sparky holidays · {month_label} {year_label}",
                "\n".join(body_lines),
            )
            if ok:
                results["sent"] += 1
                conn.execute(
                    """
                    UPDATE sparky_holiday_subscribers
                    SET last_sent_at = now()
                    WHERE id = %s;
                    """,
                    (subscriber_id,),
                )
                _record_delivery(
                    conn,
                    str(subscriber_id),
                    "sent",
                    None,
                    {"month": target_prefix},
                )
            else:
                results["failed"] += 1
                _record_delivery(
                    conn,
                    str(subscriber_id),
                    "failed",
                    detail,
                    {"month": target_prefix},
                )

    return results


def remove_subscription(subscriber_id: str, signature: str | None) -> bool:
    token = _digest_token(subscriber_id)
    if not token or signature != token:
        return False
    if not _db_available():
        return False
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            UPDATE sparky_holiday_subscribers
            SET status = 'inactive'
            WHERE id = %s;
            """,
            (subscriber_id,),
        )
    return True

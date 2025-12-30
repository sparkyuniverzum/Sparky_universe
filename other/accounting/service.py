from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Iterable, Sequence

from typing import TYPE_CHECKING, Iterable

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.domains.accounting.models import (
    AccountingMapping,
    Account,
    JournalEntry,
    JournalLine,
    NumberSequence,
)

if TYPE_CHECKING:
    from app.domains.payments.model import Payment
    from app.domains.sales.models.sale import Sale
    from app.domains.inventory.models.receipt import Receipt


def _dec(v: Decimal | float | int | str) -> Decimal:
    return Decimal(str(v))


async def _get_account_id(db: AsyncSession, key: str) -> str:
    row = (
        await db.execute(
            select(Account.id)
            .join(AccountingMapping, AccountingMapping.account_id == Account.id)
            .where(AccountingMapping.key == key)
        )
    ).scalar_one_or_none()
    if not row:
        raise DomainError(f"account mapping '{key}' missing", code="account_mapping_missing")
    return str(row)


async def _next_sequence(db: AsyncSession, code: str) -> str:
    stmt = (
        update(NumberSequence)
        .where(NumberSequence.code == code)
        .values(last_value=NumberSequence.last_value + 1)
        .returning(NumberSequence.prefix, NumberSequence.padding, NumberSequence.last_value)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise DomainError(f"number sequence '{code}' missing", code="number_sequence_missing")
    prefix, padding, value = row
    num = str(value).rjust(padding or 0, "0")
    return f"{prefix or ''}{num}"


async def generate_document_number(db: AsyncSession, code: str) -> str | None:
    """
    Public helper pro generování čísla dokladu z tabulky number_sequences.
    Pokud sequence neexistuje, vrací None (doklad se uloží bez čísla).
    """
    try:
        return await _next_sequence(db, code=code)
    except DomainError:
        return None


def _sum_dec(values: Iterable[Decimal]) -> Decimal:
    total = Decimal("0")
    for v in values:
        total += _dec(v)
    return total


async def post_cogs(db: AsyncSession, sale: "Sale", *, lines: list[dict]) -> JournalEntry | None:
    """
    Zaúčtuje náklad prodaného zboží a snížení zásob.
    lines: [{qty: Decimal, unit_cost: Decimal}]
    """
    if not lines:
        return None
    cogs_account = await _get_account_id(db, "sales_cogs")
    inventory_account = await _get_account_id(db, "inventory_asset")

    currency = getattr(sale, "currency", "CZK")
    rate = getattr(sale, "exchange_rate", Decimal("1.000000"))
    partner_id = getattr(sale, "partner_id", None)

    total_cost = _sum_dec(_dec(li["qty"]) * _dec(li["unit_cost"]) for li in lines)
    if total_cost <= 0:
        return None

    line = [
        JournalLine(
            account_id=cogs_account,
            partner_id=partner_id,
            debit=total_cost,
            credit=Decimal("0.00"),
            amount_currency=total_cost,
        ),
        JournalLine(
            account_id=inventory_account,
            partner_id=partner_id,
            debit=Decimal("0.00"),
            credit=total_cost,
            amount_currency=total_cost,
        ),
    ]
    return await _persist_entry(
        db,
        document_type="sale_cogs",
        document_id=str(sale.id),
        currency=currency,
        rate=_dec(rate),
        note="cogs posting",
        lines=line,
    )


async def reverse_entries(
    db: AsyncSession,
    *,
    document_type: str,
    document_id: str,
    note: str | None = "void",
) -> JournalEntry | None:
    """
    Vytvoří reverzní zápis k existujícím journal entries pro daný dokument.
    - původní entries označí jako void
    - vytvoří nový entry s otočeným debit/credit
    """
    rows = (
        await db.execute(
            select(JournalEntry).where(
                JournalEntry.document_type == document_type,
                JournalEntry.document_id == document_id,
            )
        )
    ).scalars().all()
    if not rows:
        return None

    # označ původní jako void
    for row in rows:
        row.status = "void"
        db.add(row)

    entry = rows[0]
    entry_id = entry.id
    # načti lines spojené s první (předpoklad 1 entry na dokument v současném modelu)
    line_rows = (
        await db.execute(
            select(JournalLine).where(JournalLine.journal_entry_id == entry_id)
        )
    ).scalars().all()

    reversed_lines = [
        JournalLine(
            account_id=ln.account_id,
            partner_id=ln.partner_id,
            product_id=ln.product_id,
            batch_id=ln.batch_id,
            tax_code_id=ln.tax_code_id,
            debit=_dec(ln.credit),
            credit=_dec(ln.debit),
            amount_currency=_dec(ln.amount_currency),
        )
        for ln in line_rows
    ]

    return await _persist_entry(
        db,
        document_type=document_type,
        document_id=document_id,
        currency=entry.currency,
        rate=_dec(entry.rate),
        note=note or "void",
        lines=reversed_lines,
        status="void",
    )


async def _persist_entry(
    db: AsyncSession,
    *,
    document_type: str,
    document_id: str | None,
    currency: str,
    rate: Decimal,
    note: str | None,
    lines: Sequence[JournalLine],
    status: str = "posted",
) -> JournalEntry:
    debit_total = _sum_dec(l.debit for l in lines)
    credit_total = _sum_dec(l.credit for l in lines)
    if debit_total.quantize(Decimal("0.01")) != credit_total.quantize(Decimal("0.01")):
        raise DomainError(
            "journal not balanced",
            code="journal_unbalanced",
        )

    entry_no = None
    try:
        entry_no = await _next_sequence(db, code="JE")
    except DomainError:
        # fallback – still store entry but without human-friendly number
        entry_no = None

    entry = JournalEntry(
        id=str(uuid.uuid4()),
        entry_no=entry_no,
        document_type=document_type,
        document_id=document_id,
        currency=currency,
        rate=rate,
        status=status,
        note=note,
    )
    db.add(entry)
    await db.flush()

    for ln in lines:
        ln.journal_entry_id = entry.id
        db.add(ln)

    await db.flush()
    return entry


async def post_sale(db: AsyncSession, sale: "Sale", partner_id: str | None = None, *, caller: str | None = None) -> JournalEntry:
    ar_account = await _get_account_id(db, "accounts_receivable")
    revenue_account = await _get_account_id(db, "sales_revenue")
    vat_output_account = await _get_account_id(db, "vat_output")

    currency = getattr(sale, "currency", "CZK")
    rate = getattr(sale, "exchange_rate", Decimal("1.000000"))

    lines: list[JournalLine] = [
        JournalLine(
            account_id=ar_account,
            partner_id=partner_id or getattr(sale, "partner_id", None),
            debit=sale.total_amount,
            credit=Decimal("0.00"),
            amount_currency=sale.total_amount,
        ),
        JournalLine(
            account_id=revenue_account,
            partner_id=partner_id or getattr(sale, "partner_id", None),
            debit=Decimal("0.00"),
            credit=sale.subtotal,
            amount_currency=sale.subtotal,
        ),
    ]

    vat_total = getattr(sale, "vat_total", Decimal("0"))
    if _dec(vat_total) > 0:
        lines.append(
            JournalLine(
                account_id=vat_output_account,
                partner_id=partner_id or getattr(sale, "partner_id", None),
                debit=Decimal("0.00"),
                credit=_dec(vat_total),
                amount_currency=_dec(vat_total),
            )
        )

    return await _persist_entry(
        db,
        document_type="sale",
        document_id=str(sale.id),
        currency=currency,
        rate=_dec(rate),
        note="sale posting",
        lines=lines,
    )


async def post_receipt(db: AsyncSession, receipt: "Receipt", *, amount: Decimal, vat_amount: Decimal) -> JournalEntry:
    inventory_account = await _get_account_id(db, "inventory_asset")
    ap_account = await _get_account_id(db, "accounts_payable")
    vat_input_account = await _get_account_id(db, "vat_input")

    currency = getattr(receipt, "currency", "CZK")
    rate = getattr(receipt, "exchange_rate", Decimal("1.000000"))
    partner_id = getattr(receipt, "partner_id", None)

    net_amount = _dec(amount)
    vat_amount = _dec(vat_amount)
    total = net_amount + vat_amount

    lines = [
        JournalLine(
            account_id=inventory_account,
            partner_id=partner_id,
            debit=net_amount,
            credit=Decimal("0.00"),
            amount_currency=net_amount,
        )
    ]
    if vat_amount > 0:
        lines.append(
            JournalLine(
                account_id=vat_input_account,
                partner_id=partner_id,
                debit=vat_amount,
                credit=Decimal("0.00"),
                amount_currency=vat_amount,
            )
        )

    lines.append(
        JournalLine(
            account_id=ap_account,
            partner_id=partner_id,
            debit=Decimal("0.00"),
            credit=total,
            amount_currency=total,
        )
    )

    return await _persist_entry(
        db,
        document_type="receipt",
        document_id=str(receipt.id),
        currency=currency,
        rate=_dec(rate),
        note="receipt posting",
        lines=lines,
    )


async def post_payment(db: AsyncSession, payment: "Payment", *, partner_id: str | None = None, target_account: str | None = None) -> JournalEntry:
    cash_account = await _get_account_id(db, "cash")
    bank_account = await _get_account_id(db, "bank")
    ar_account = await _get_account_id(db, "accounts_receivable")

    account_in = target_account or (cash_account if payment.type.lower() == "cash" else bank_account)

    currency = getattr(payment, "currency", "CZK")
    rate = getattr(payment, "exchange_rate", Decimal("1.000000"))

    amt = _dec(payment.amount)
    lines = [
        JournalLine(
            account_id=account_in,
            partner_id=partner_id,
            debit=amt,
            credit=Decimal("0.00"),
            amount_currency=amt,
        ),
        JournalLine(
            account_id=ar_account,
            partner_id=partner_id,
            debit=Decimal("0.00"),
            credit=amt,
            amount_currency=amt,
        ),
    ]

    return await _persist_entry(
        db,
        document_type="payment",
        document_id=str(payment.id),
        currency=currency,
        rate=_dec(rate),
        note="payment posting",
        lines=lines,
    )


async def post_payment_refund(
    db: AsyncSession,
    payment: "Payment",
    *,
    amount: Decimal,
    partner_id: str | None = None,
    target_account: str | None = None,
) -> JournalEntry:
    """
    Zaúčtuje refund platby (částku nebo plný refund).
    Revertuje původní platbu jen v dané výši, nikoliv celý dokument.
    """
    cash_account = await _get_account_id(db, "cash")
    bank_account = await _get_account_id(db, "bank")
    ar_account = await _get_account_id(db, "accounts_receivable")

    account_out = target_account or (cash_account if payment.type.lower() == "cash" else bank_account)

    currency = getattr(payment, "currency", "CZK")
    rate = getattr(payment, "exchange_rate", Decimal("1.000000"))

    amt = _dec(amount)
    lines = [
        JournalLine(
            account_id=ar_account,
            partner_id=partner_id,
            debit=amt,
            credit=Decimal("0.00"),
            amount_currency=amt,
        ),
        JournalLine(
            account_id=account_out,
            partner_id=partner_id,
            debit=Decimal("0.00"),
            credit=amt,
            amount_currency=amt,
        ),
    ]

    return await _persist_entry(
        db,
        document_type="payment_refund",
        document_id=str(payment.id),
        currency=currency,
        rate=_dec(rate),
        note="payment refund",
        lines=lines,
    )


__all__ = [
    "post_sale",
    "post_receipt",
    "post_payment",
    "post_payment_refund",
    "reverse_entries",
    "generate_document_number",
    "post_cogs",
]

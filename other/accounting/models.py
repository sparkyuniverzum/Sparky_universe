from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.db_base import Base, uuid_column


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = uuid_column()
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # asset/liability/equity/revenue/expense
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    allow_manual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class TaxCode(Base):
    __tablename__ = "tax_codes"

    id: Mapped[str] = uuid_column()
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 2, asdecimal=True), nullable=False, default=Decimal("0.00"), server_default="0.00")
    country: Mapped[str | None] = mapped_column(String(8), nullable=True)
    reverse_charge: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Partner(Base):
    __tablename__ = "partners"

    id: Mapped[str] = uuid_column()
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    partner_type: Mapped[str] = mapped_column(String(32), nullable=False, default="customer", server_default="customer")
    vat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    registration_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class NumberSequence(Base):
    __tablename__ = "number_sequences"

    id: Mapped[str] = uuid_column()
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prefix: Mapped[str | None] = mapped_column(String(16), nullable=True)
    padding: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default="5")
    last_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[str] = uuid_column()
    entry_no: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    document_type: Mapped[str] = mapped_column(String(32), nullable=False)
    document_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CZK", server_default="CZK")
    rate: Mapped[Decimal] = mapped_column(Numeric(12, 6, asdecimal=True), nullable=False, default=Decimal("1.000000"), server_default="1.000000")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft", server_default="draft")
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id: Mapped[str] = uuid_column()
    journal_entry_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    partner_id: Mapped[str | None] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("partners.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id: Mapped[str | None] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    batch_id: Mapped[str | None] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("batches.id", ondelete="SET NULL"), nullable=True, index=True)
    tax_code_id: Mapped[str | None] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("tax_codes.id", ondelete="SET NULL"), nullable=True, index=True)
    debit: Mapped[Decimal] = mapped_column(Numeric(14, 2, asdecimal=True), nullable=False, default=Decimal("0.00"), server_default="0.00")
    credit: Mapped[Decimal] = mapped_column(Numeric(14, 2, asdecimal=True), nullable=False, default=Decimal("0.00"), server_default="0.00")
    amount_currency: Mapped[Decimal] = mapped_column(Numeric(14, 2, asdecimal=True), nullable=False, default=Decimal("0.00"), server_default="0.00")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("journal_entry_id", "id", name="uq_journal_line_entry_line"),
        Index("ix_journal_lines_account_created", "account_id", "created_at"),
    )


class AccountingMapping(Base):
    __tablename__ = "accounting_mappings"

    id: Mapped[str] = uuid_column()
    key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    account_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


__all__ = [
    "Account",
    "TaxCode",
    "Partner",
    "NumberSequence",
    "JournalEntry",
    "JournalLine",
    "AccountingMapping",
]

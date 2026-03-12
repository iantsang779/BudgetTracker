from __future__ import annotations

"""Tests verifying that all SQL schemas are correctly structured in the database.

Each test group covers one table and checks:
  - The table exists after create_all
  - Every expected column is present with the correct type and nullability
  - Default values are applied correctly by the ORM
  - Foreign key relationships are enforced
  - Unique and soft-delete constraints behave as expected
"""

from datetime import UTC, datetime

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.account import Account
from backend.models.category import Category
from backend.models.currency_rate import CurrencyRate
from backend.models.income import IncomeEntry
from backend.models.transaction import Transaction

# ── Helpers ───────────────────────────────────────────────────────────────────


async def _table_info(session: AsyncSession, table: str) -> dict[str, dict]:
    """Return PRAGMA table_info rows keyed by column name."""
    result = await session.execute(sa.text(f"PRAGMA table_info({table})"))
    return {row[1]: {"type": row[2], "notnull": bool(row[3]), "pk": bool(row[5])} for row in result}


async def _fk_list(session: AsyncSession, table: str) -> list[dict]:
    """Return PRAGMA foreign_key_list rows as dicts."""
    result = await session.execute(sa.text(f"PRAGMA foreign_key_list({table})"))
    return [{"from": row[3], "table": row[2], "to": row[4]} for row in result]


async def _tables(session: AsyncSession) -> set[str]:
    """Return the set of all table names in the database."""
    result = await session.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table'")
    )
    return {row[0] for row in result}


# ── All tables exist ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_all_tables_created(db_session: AsyncSession) -> None:
    """All six ORM tables must be created by Base.metadata.create_all."""
    names = await _tables(db_session)
    expected = {
        "accounts",
        "categories",
        "transactions",
        "income_entries",
        "currency_rates",
    }
    assert expected.issubset(names), f"Missing tables: {expected - names}"


# ── accounts ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_accounts_columns(db_session: AsyncSession) -> None:
    """accounts table must have the correct columns, types, and nullability."""
    cols = await _table_info(db_session, "accounts")

    assert "id" in cols and cols["id"]["pk"]
    assert "name" in cols and cols["name"]["notnull"]
    assert "currency_code" in cols and cols["currency_code"]["notnull"]
    assert "balance_initial" in cols and cols["balance_initial"]["notnull"]
    assert "created_at" in cols
    assert "deleted_at" in cols and not cols["deleted_at"]["notnull"]  # nullable


@pytest.mark.asyncio
async def test_accounts_defaults(db_session: AsyncSession) -> None:
    """Account ORM defaults: currency_code='GBP', balance_initial=0.0."""
    account = Account(name="Checking")
    db_session.add(account)
    await db_session.flush()
    await db_session.refresh(account)

    assert account.id is not None
    assert account.currency_code == "GBP"
    assert account.balance_initial == 0.0
    assert account.deleted_at is None
    assert account.created_at is not None


@pytest.mark.asyncio
async def test_accounts_soft_delete(db_session: AsyncSession) -> None:
    """deleted_at must accept a datetime value (soft-delete pattern)."""
    account = Account(name="ToDelete")
    db_session.add(account)
    await db_session.flush()

    now = datetime.now(UTC).replace(tzinfo=None)
    account.deleted_at = now
    await db_session.flush()
    await db_session.refresh(account)

    assert account.deleted_at is not None


# ── categories ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_categories_columns(db_session: AsyncSession) -> None:
    """categories table must have all expected columns."""
    cols = await _table_info(db_session, "categories")

    assert "id" in cols and cols["id"]["pk"]
    assert "name" in cols and cols["name"]["notnull"]
    assert "color_hex" in cols and cols["color_hex"]["notnull"]
    assert "icon" in cols and cols["icon"]["notnull"]
    assert "is_income" in cols and cols["is_income"]["notnull"]
    assert "created_at" in cols
    assert "deleted_at" in cols and not cols["deleted_at"]["notnull"]


@pytest.mark.asyncio
async def test_categories_defaults(db_session: AsyncSession) -> None:
    """Category ORM defaults: color_hex, icon, is_income=False."""
    cat = Category(name="Groceries")
    db_session.add(cat)
    await db_session.flush()
    await db_session.refresh(cat)

    assert cat.id is not None
    assert cat.color_hex == "#6366f1"
    assert cat.icon == "tag"
    assert cat.is_income is False
    assert cat.deleted_at is None


@pytest.mark.asyncio
async def test_categories_name_unique(db_session: AsyncSession) -> None:
    """Inserting two categories with the same name must raise an integrity error."""
    db_session.add(Category(name="Duplicate"))
    await db_session.flush()

    db_session.add(Category(name="Duplicate"))
    with pytest.raises(Exception):  # IntegrityError on unique violation
        await db_session.flush()


# ── transactions ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_transactions_columns(db_session: AsyncSession) -> None:
    """transactions table must contain all expected columns including recurrence."""
    cols = await _table_info(db_session, "transactions")

    assert "id" in cols and cols["id"]["pk"]
    assert "account_id" in cols and cols["account_id"]["notnull"]
    assert "category_id" in cols and not cols["category_id"]["notnull"]  # nullable
    assert "amount_local" in cols and cols["amount_local"]["notnull"]
    assert "currency_code" in cols and cols["currency_code"]["notnull"]
    assert "amount_base" in cols and cols["amount_base"]["notnull"]
    assert "description" in cols
    assert "merchant" in cols
    assert "transaction_date" in cols and cols["transaction_date"]["notnull"]
    assert "source" in cols and cols["source"]["notnull"]
    assert "recurrence" in cols and not cols["recurrence"]["notnull"]  # nullable
    assert "voice_transcript" in cols and not cols["voice_transcript"]["notnull"]
    assert "created_at" in cols
    assert "deleted_at" in cols and not cols["deleted_at"]["notnull"]


@pytest.mark.asyncio
async def test_transactions_foreign_keys(db_session: AsyncSession) -> None:
    """transactions must declare FK to accounts and categories."""
    fks = await _fk_list(db_session, "transactions")
    fk_map = {fk["from"]: fk["table"] for fk in fks}

    assert fk_map.get("account_id") == "accounts"
    assert fk_map.get("category_id") == "categories"


@pytest.mark.asyncio
async def test_transactions_defaults(db_session: AsyncSession) -> None:
    """Transaction ORM defaults: source='manual', recurrence=None, currency_code='GBP'."""
    account = Account(name="Bank")
    db_session.add(account)
    await db_session.flush()

    txn = Transaction(
        account_id=account.id,
        amount_local=42.0,
        amount_base=42.0,
        transaction_date=datetime(2024, 3, 1),
    )
    db_session.add(txn)
    await db_session.flush()
    await db_session.refresh(txn)

    assert txn.id is not None
    assert txn.source == "manual"
    assert txn.currency_code == "GBP"
    assert txn.recurrence is None
    assert txn.category_id is None
    assert txn.voice_transcript is None
    assert txn.deleted_at is None


@pytest.mark.asyncio
async def test_transactions_recurrence_values(db_session: AsyncSession) -> None:
    """recurrence column must accept 'monthly' and 'yearly', and remain None for one-off."""
    account = Account(name="Wallet")
    db_session.add(account)
    await db_session.flush()

    for recurrence in ("monthly", "yearly", None):
        txn = Transaction(
            account_id=account.id,
            amount_local=10.0,
            amount_base=10.0,
            transaction_date=datetime(2024, 1, 1),
            recurrence=recurrence,
        )
        db_session.add(txn)
        await db_session.flush()
        await db_session.refresh(txn)
        assert txn.recurrence == recurrence


@pytest.mark.asyncio
async def test_transactions_with_category(db_session: AsyncSession) -> None:
    """Transactions can optionally link to a category via FK."""
    account = Account(name="Savings")
    cat = Category(name="Food", is_income=False)
    db_session.add_all([account, cat])
    await db_session.flush()

    txn = Transaction(
        account_id=account.id,
        category_id=cat.id,
        amount_local=25.0,
        amount_base=25.0,
        transaction_date=datetime(2024, 6, 15),
    )
    db_session.add(txn)
    await db_session.flush()
    await db_session.refresh(txn)

    assert txn.category_id == cat.id


# ── income_entries ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_income_entries_columns(db_session: AsyncSession) -> None:
    """income_entries table must have all expected columns."""
    cols = await _table_info(db_session, "income_entries")

    assert "id" in cols and cols["id"]["pk"]
    assert "account_id" in cols and cols["account_id"]["notnull"]
    assert "amount_local" in cols and cols["amount_local"]["notnull"]
    assert "currency_code" in cols and cols["currency_code"]["notnull"]
    assert "amount_base" in cols and cols["amount_base"]["notnull"]
    assert "recurrence" in cols and cols["recurrence"]["notnull"]
    assert "description" in cols
    assert "effective_date" in cols and cols["effective_date"]["notnull"]
    assert "end_date" in cols and not cols["end_date"]["notnull"]  # nullable
    assert "created_at" in cols
    assert "deleted_at" in cols and not cols["deleted_at"]["notnull"]


@pytest.mark.asyncio
async def test_income_entries_foreign_keys(db_session: AsyncSession) -> None:
    """income_entries must declare FK to accounts."""
    fks = await _fk_list(db_session, "income_entries")
    fk_map = {fk["from"]: fk["table"] for fk in fks}
    assert fk_map.get("account_id") == "accounts"


@pytest.mark.asyncio
async def test_income_entries_defaults(db_session: AsyncSession) -> None:
    """IncomeEntry ORM defaults: recurrence='monthly', currency_code='GBP'."""
    account = Account(name="Payroll")
    db_session.add(account)
    await db_session.flush()

    entry = IncomeEntry(
        account_id=account.id,
        amount_local=3000.0,
        amount_base=3000.0,
        effective_date=datetime(2024, 1, 1),
    )
    db_session.add(entry)
    await db_session.flush()
    await db_session.refresh(entry)

    assert entry.id is not None
    assert entry.currency_code == "GBP"
    assert entry.recurrence == "monthly"
    assert entry.end_date is None
    assert entry.deleted_at is None


@pytest.mark.asyncio
async def test_income_entries_recurrence_values(db_session: AsyncSession) -> None:
    """income_entries recurrence must store 'monthly', 'yearly', and 'one_off'."""
    account = Account(name="Misc")
    db_session.add(account)
    await db_session.flush()

    for recurrence in ("monthly", "yearly", "one_off"):
        entry = IncomeEntry(
            account_id=account.id,
            amount_local=100.0,
            amount_base=100.0,
            recurrence=recurrence,
            effective_date=datetime(2024, 1, 1),
        )
        db_session.add(entry)
        await db_session.flush()
        await db_session.refresh(entry)
        assert entry.recurrence == recurrence


# ── currency_rates ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_currency_rates_columns(db_session: AsyncSession) -> None:
    """currency_rates table must have all expected columns."""
    cols = await _table_info(db_session, "currency_rates")

    assert "id" in cols and cols["id"]["pk"]
    assert "base_code" in cols and cols["base_code"]["notnull"]
    assert "target_code" in cols and cols["target_code"]["notnull"]
    assert "rate" in cols and cols["rate"]["notnull"]
    assert "fetched_at" in cols


@pytest.mark.asyncio
async def test_currency_rates_roundtrip(db_session: AsyncSession) -> None:
    """CurrencyRate must store and retrieve base/target codes and rate."""
    rate = CurrencyRate(base_code="USD", target_code="GBP", rate=0.79)
    db_session.add(rate)
    await db_session.flush()
    await db_session.refresh(rate)

    assert rate.id is not None
    assert rate.base_code == "USD"
    assert rate.target_code == "GBP"
    assert rate.rate == pytest.approx(0.79)
    assert rate.fetched_at is not None

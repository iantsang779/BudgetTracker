from __future__ import annotations

"""Shared helpers for income amount normalisation."""


def monthly_base(amount_base: float, recurrence: str) -> float:
    """Convert an income entry's base amount to a monthly equivalent.

    Args:
        amount_base: Amount in base currency (USD).
        recurrence: One of ``'weekly'``, ``'monthly'``, or ``'yearly'``.

    Returns:
        Monthly equivalent of the income amount.
    """
    if recurrence == "weekly":
        return amount_base * 52.0 / 12.0
    if recurrence == "yearly":
        return amount_base / 12.0
    return amount_base

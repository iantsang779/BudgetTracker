from __future__ import annotations

"""Shared helpers for income amount normalisation."""


def monthly_base(amount_base: float, recurrence: str) -> float:
    """Convert an income entry's base amount to a monthly equivalent.

    One-off entries are excluded from recurring monthly totals and return 0.

    Args:
        amount_base: Amount in base currency (USD).
        recurrence: One of ``'monthly'``, ``'yearly'``, or ``'one_off'``.

    Returns:
        Monthly equivalent of the income amount.
    """
    if recurrence == "yearly":
        return amount_base / 12.0
    if recurrence == "one_off":
        return 0.0
    return amount_base

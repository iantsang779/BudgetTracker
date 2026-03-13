from __future__ import annotations

"""Voice NLP parser: extracts structured transaction fields from a transcript."""

import re
from datetime import date, timedelta

from backend.schemas.voice import VoiceParseResponse

# ── Currency keyword map ───────────────────────────────────────────────────────

_CURRENCY_KEYWORDS: dict[str, list[str]] = {
    "USD": ["dollar", "dollars", "usd", "buck", "bucks"],
    "GBP": ["pound", "pounds", "gbp", "quid"],
    "EUR": ["euro", "euros", "eur"],
    "CAD": ["canadian dollar", "cad"],
    "AUD": ["australian dollar", "aud"],
    "JPY": ["yen", "jpy"],
    "CHF": ["franc", "francs", "chf"],
    "INR": ["rupee", "rupees", "inr"],
}

# ── Category hint keyword map ──────────────────────────────────────────────────

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Groceries": [
        "grocer",
        "grocery",
        "groceries",
        "supermarket",
        "tesco",
        "asda",
        "sainsbury",
        "lidl",
        "aldi",
        "walmart",
        "costco",
    ],
    "Eating Out": [
        "coffee",
        "cafe",
        "restaurant",
        "lunch",
        "dinner",
        "breakfast",
        "brunch",
        "starbucks",
        "mcdonald",
        "burger",
        "pizza",
        "sushi",
        "takeaway",
        "takeout",
        "nando",
        "subway",
        "kfc",
        "chipotle",
    ],
    "Transport": [
        "uber",
        "lyft",
        "taxi",
        "cab",
        "bus",
        "train",
        "metro",
        "tube",
        "rail",
        "petrol",
        "gas station",
        "fuel",
        "transport",
        "ride",
    ],
    "Health & Medical": [
        "pharmacy",
        "chemist",
        "doctor",
        "dentist",
        "hospital",
        "medicine",
        "prescription",
        "gym",
        "fitness",
    ],
    "Entertainment": [
        "cinema",
        "movie",
        "theatre",
        "theater",
        "concert",
        "netflix",
        "spotify",
        "game",
        "ticket",
    ],
    "Shopping": [
        "amazon",
        "ebay",
        "clothing",
        "shoes",
        "clothes",
        "shirt",
        "jacket",
        "pants",
        "dress",
    ],
    "Bills & Utilities": [
        "electric",
        "electricity",
        "water",
        "gas",
        "bill",
        "utility",
        "utilities",
        "internet",
        "phone",
        "broadband",
    ],
    "Rent": ["rent", "mortgage", "landlord"],
    "Travel": ["flight", "hotel", "airbnb", "booking", "holiday", "vacation", "airport"],
    "Education": ["book", "books", "course", "tuition", "school", "university", "college"],
}

# ── Date keyword extraction ────────────────────────────────────────────────────

_MONTH_MAP: dict[str, int] = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}


def _extract_date(text: str) -> str | None:
    """Extract a date from normalized text, returning ISO date string or None."""
    today = date.today()

    if re.search(r"\btoday\b", text):
        return today.isoformat()
    if re.search(r"\byesterday\b", text):
        return (today - timedelta(days=1)).isoformat()

    # "last monday" etc.
    last_match = _LAST_WEEKDAY_RE.search(text)
    if last_match:
        target_day = _WEEKDAY_NAMES.index(last_match.group(1))
        days_back = (today.weekday() - target_day) % 7 or 7
        return (today - timedelta(days=days_back)).isoformat()

    # ISO format: 2026-03-05
    iso_match = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if iso_match:
        return iso_match.group(0)

    # Numeric: 3/5 or 3/5/2026
    slash_match = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{4}))?\b", text)
    if slash_match:
        m, d_num, y = int(slash_match.group(1)), int(slash_match.group(2)), slash_match.group(3)
        yr = int(y) if y else today.year
        try:
            return date(yr, m, d_num).isoformat()
        except ValueError:
            pass

    # "march 5" or "5 march"
    named_match = _NAMED_DATE_RE.search(text)
    if named_match:
        m = _MONTH_MAP[named_match.group(1).lower()]
        d_num = int(named_match.group(2))
        try:
            return date(today.year, m, d_num).isoformat()
        except ValueError:
            pass

    named_rev = _NAMED_DATE_REV_RE.search(text)
    if named_rev:
        d_num = int(named_rev.group(1))
        m = _MONTH_MAP[named_rev.group(2).lower()]
        try:
            return date(today.year, m, d_num).isoformat()
        except ValueError:
            pass

    return None


# ── Amount extraction ──────────────────────────────────────────────────────────


def _extract_amount(text: str) -> float | None:
    """Extract the first numeric amount from text."""
    # Prefixed: $42, £15.50
    prefixed = re.search(r"[$£€]\s*(\d+(?:\.\d+)?)", text)
    if prefixed:
        return float(prefixed.group(1))

    # Standard numeric: 42, 15.50 — avoid matching years (4-digit >= 1900)
    for m in re.finditer(r"\b(\d+(?:\.\d+)?)\b", text):
        val = float(m.group(1))
        int_val = int(val)
        if int_val >= 1900 and int_val <= 2100 and val == int_val:
            continue  # looks like a year
        return val

    return None


# ── Currency extraction ────────────────────────────────────────────────────────


def _extract_currency(text: str) -> str | None:
    """Extract a currency code from text using keyword matching."""
    for code, keywords in _CURRENCY_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return code
    return None


# ── Description / merchant extraction ─────────────────────────────────────────

# Date-like noise words to strip from description / merchant ends
_WEEKDAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_LAST_WEEKDAY_RE = re.compile(r"\blast\s+(" + "|".join(_WEEKDAY_NAMES) + r")\b")
_NAMED_DATE_RE = re.compile(r"\b(" + "|".join(_MONTH_MAP) + r")\s+(\d{1,2})\b", re.IGNORECASE)
_NAMED_DATE_REV_RE = re.compile(r"\b(\d{1,2})\s+(" + "|".join(_MONTH_MAP) + r")\b", re.IGNORECASE)

_NOISE_WORDS = re.compile(
    r"\b(today|yesterday|last\s+\w+|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}(?:/\d{4})?|"
    + "|".join(_MONTH_MAP.keys())
    + r"|\d{1,2})\s*$",
    re.IGNORECASE,
)

# Currency noise to strip from description tail
_CURRENCY_NOISE = re.compile(
    r"\b(" + "|".join(kw for kws in _CURRENCY_KEYWORDS.values() for kw in kws) + r")\b",
    re.IGNORECASE,
)


def _clean_fragment(fragment: str) -> str | None:
    """Strip noise from a parsed fragment and return None if empty."""
    fragment = _NOISE_WORDS.sub("", fragment).strip(" ,")
    fragment = _CURRENCY_NOISE.sub("", fragment).strip(" ,")
    # Strip leading/trailing numeric tokens (lone amounts)
    fragment = re.sub(r"^\d+(?:\.\d+)?\s*", "", fragment).strip()
    fragment = re.sub(r"\s*\d+(?:\.\d+)?$", "", fragment).strip()
    return fragment if fragment else None


def _extract_description_and_merchant(text: str) -> tuple[str | None, str | None]:
    """
    Extract description (after 'on'/'for') and merchant (after 'at').

    Returns:
        A (description, merchant) tuple; either may be None.
    """
    norm = text.lower()

    # Find 'at' position
    at_match = re.search(r"\bat\b", norm)
    at_pos = at_match.start() if at_match else len(norm)

    # Find 'on' or 'for' position (first occurrence before 'at')
    on_match = re.search(r"\b(on|for)\b", norm[:at_pos])
    on_pos = on_match.end() if on_match else -1

    description: str | None = None
    merchant: str | None = None

    if on_pos >= 0:
        raw_desc = text[on_pos:at_pos].strip()
        description = _clean_fragment(raw_desc)

    if at_match:
        raw_merchant = text[at_match.end() :].strip()
        merchant = _clean_fragment(raw_merchant)

    return description, merchant


# ── Category hint ──────────────────────────────────────────────────────────────


def _extract_category_hint(description: str | None, merchant: str | None) -> str | None:
    """Return a category name hint based on description and merchant keywords."""
    combined = " ".join(filter(None, [description, merchant])).lower()
    if not combined:
        return None
    for category, keywords in _CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in combined:
                return category
    return None


# ── Confidence scoring ────────────────────────────────────────────────────────


def _score_confidence(
    amount: float | None,
    currency_code: str | None,
    description: str | None,
    merchant: str | None,
    transaction_date: str | None,
) -> float:
    """Compute a 0.0–1.0 confidence score based on how many fields were found."""
    score = 0.0
    if amount is not None:
        score += 0.35
    if description is not None:
        score += 0.20
    if merchant is not None:
        score += 0.20
    if currency_code is not None:
        score += 0.15
    if transaction_date is not None:
        score += 0.10
    return round(min(score, 1.0), 4)


# ── Public API ────────────────────────────────────────────────────────────────


def parse_transcript(transcript: str) -> VoiceParseResponse:
    """Parse a raw voice transcript into structured transaction fields.

    Args:
        transcript: Raw spoken transcript string from the user.

    Returns:
        A VoiceParseResponse with extracted fields and a confidence score.
    """
    normalized = transcript.lower().strip()

    amount = _extract_amount(normalized)
    currency_code = _extract_currency(normalized)
    transaction_date = _extract_date(normalized)
    description, merchant = _extract_description_and_merchant(transcript)
    category_hint = _extract_category_hint(description, merchant)
    confidence = _score_confidence(amount, currency_code, description, merchant, transaction_date)

    return VoiceParseResponse(
        amount=amount,
        currency_code=currency_code,
        description=description,
        merchant=merchant,
        transaction_date=transaction_date,
        category_hint=category_hint,
        confidence=confidence,
        raw_transcript=transcript,
    )

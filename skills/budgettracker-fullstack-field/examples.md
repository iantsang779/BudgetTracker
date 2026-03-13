# Fullstack Field — Worked Examples

## Example 1: Fixing a 422 on voice transaction save (2026-03-13)

**Symptom:** Voice-parsed transactions returned 422 when saved. The frontend sent `TransactionCreate` without `amount_base`, but the backend schema required it.

**Root cause in `backend/schemas/transaction.py`:**
```python
# BEFORE — Pydantic required this field; frontend never sends it → 422
amount_base: float = Field(gt=0)
```

**Fix:**
```python
# AFTER — safe default; router always overwrites it via CurrencyService
amount_base: float = 0.0  # always overwritten server-side; 0.0 is a placeholder
```

**Why:** `TransactionCreate` is sent by the frontend. `amount_base` is a server-computed USD conversion that the router populates before `repo.create()`. Giving Pydantic `Field(gt=0)` with no default made the field required at deserialization time, before the router body could ever run.

---

## Example 2: Adding `voice_transcript` field to transactions

Touch points used (all 9 steps):

| Step | Change |
|------|--------|
| Model | `voice_transcript: Mapped[str \| None] = mapped_column(default=None)` |
| Schema Create | `voice_transcript: str \| None = None` |
| Schema Update | `voice_transcript: str \| None = None` |
| Schema Read | `voice_transcript: str \| None` |
| Router | No change — `payload.model_dump()` passes it through |
| Tests | `json={"voice_transcript": "spent 10 on lunch"}` in create payload |
| TS Create | `voice_transcript?: string \| null` |
| TS Update | `voice_transcript?: string \| null` |
| TS Read | `voice_transcript: string \| null` |
| Page | Transcript shown as a read-only banner when `source === 'voice'` |

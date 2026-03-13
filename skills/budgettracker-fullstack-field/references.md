# Fullstack Field — Code Templates

## Step 1: Backend Model

```python
# backend/models/transaction.py
class Transaction(Base):
    # existing fields ...
    new_field: Mapped[str | None] = mapped_column(default=None)  # nullable optional
    # OR
    new_field: Mapped[str] = mapped_column(String(255))           # required
```

For monetary fields, always add a pair:
```python
amount_local: Mapped[float]
amount_base: Mapped[float]   # computed server-side, never from client
```

---

## Step 2: Backend Schemas

```python
# DomainCreate — include if client can set it
class DomainCreate(BaseModel):
    new_field: str | None = None   # optional
    # new_field: str               # required
    # Server-computed fields get a default so Pydantic doesn't 422:
    # amount_base: float = 0.0

# DomainUpdate — always optional
class DomainUpdate(BaseModel):
    new_field: str | None = None

# DomainRead — always present; requires from_attributes
class DomainRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    new_field: str | None = None
```

**Never add `amount_base` to `Create` or `Update`** — it's always server-computed via `CurrencyService`.

---

## Step 3: Frontend Types (`frontend/src/types/index.ts`)

Mirror the schema changes exactly:

```typescript
export interface DomainCreate {
  // existing fields ...
  new_field?: string | null   // optional on create
}

export interface DomainUpdate {
  // existing fields ...
  new_field?: string | null
}

export interface DomainRead {
  // existing fields ...
  new_field: string | null    // always present in read
}
```

---

## Step 4: Frontend Form (`frontend/src/pages/{Domain}Page.tsx`)

Add state and input:
```typescript
const [form, setForm] = useState({
  // existing fields ...
  new_field: '',
})

// In JSX:
<input
  type="text"
  value={form.new_field ?? ''}
  onChange={(e) => setForm((prev) => ({ ...prev, new_field: e.target.value }))}
  placeholder="New field"
/>
```

Display in table:
```typescript
<td>{item.new_field ?? '—'}</td>
```

---

## Step 5: Tests — Assert New Field

```python
@pytest.mark.asyncio
async def test_create_with_new_field(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/domains/", json={
        "name": "Test",
        "new_field": "hello",
    })
    assert resp.status_code == 201
    assert resp.json()["new_field"] == "hello"
```

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| `amount_base` in client payload | Remove it — always server-computed |
| `amount_base: Field(gt=0)` with no default | Change to `amount_base: float = 0.0` |
| Forgot `from_attributes=True` on Read | Add `model_config = ConfigDict(from_attributes=True)` |
| TS type uses `any` | Use specific union type; run `npx tsc --noEmit` |
| Field nullable in DB but not in TS Read | Use `string \| null` in Read interface |
| SQLite migration | Dev uses `database.py`'s `create_all` on startup — restart backend to apply model changes |

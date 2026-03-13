---
name: budgettracker-fullstack-field
description: Recipe for adding or modifying a field end-to-end (backend + frontend) in BudgetTracker. Trigger on any change that spans both backend schemas and frontend types, or when debugging 422/type-mismatch errors.
version: 2.0.0
source: local-git-analysis
analyzed_commits: 50
---

# BudgetTracker: Fullstack Field Guide

Use this skill when **adding, modifying, or debugging** a field that spans both backend and frontend — new columns, schema changes, 422 validation errors, type mismatches, or any change where `frontend/src/types/index.ts` and `backend/schemas/` must stay in sync.

## 422 / Type Error Diagnosis

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| 422 on POST/PATCH | Required Pydantic field has no default but frontend never sends it | Give it a safe default (e.g. `= 0.0`, `= None`) |
| `amount_base` 422 | `Field(gt=0)` with no default — frontend never sends it | `amount_base: float = 0.0` (always overwritten server-side) |
| TS type error on `Create` | `amount_base` in TS `Create` interface | Remove it — server-computed only |
| `ValidationError from_attributes` | Read schema missing `model_config = ConfigDict(from_attributes=True)` | Add config to `Read` schema |
| Nullable DB field not nullable in TS | `string` instead of `string \| null` in `Read` interface | Fix union type |
| mypy `--strict` on test fixture | `client` arg missing `AsyncClient` type annotation | Import and annotate |

See [examples.md](./examples.md) for a worked end-to-end fix.

## Touch Points (in order)

| Step | File | What to change |
|------|------|----------------|
| 1 | `backend/models/{domain}.py` | Add `Mapped[T]` column |
| 2 | `backend/schemas/{domain}.py` | Add to `Create`, `Update` (optional), `Read` |
| 3 | `backend/repositories/{domain}_repository.py` | Usually no change needed |
| 4 | `backend/services/{domain}_service.py` | Only if field needs computation |
| 5 | `backend/routers/{domain}.py` | Usually no change if using `payload.model_dump()` |
| 6 | `backend/tests/test_{domain}.py` | Add field to fixture payloads; assert presence |
| 7 | `frontend/src/types/index.ts` | Add to `{Domain}Create`, `{Domain}Update`, `{Domain}Read` |
| 8 | `frontend/src/api/{domain}.ts` | No change if passing whole payload object |
| 9 | `frontend/src/pages/{Domain}Page.tsx` | Add input to form; display in table |

See [references.md](./references.md) for code templates for each step.

## Validation Commands

```bash
# Backend
source /home/iants/BudgetTracker/venv/bin/activate
cd /home/iants/BudgetTracker
python3 -m ruff check --fix backend/ && python3 -m ruff format backend/
python3 -m mypy backend/ --strict
cd backend && pytest tests/ -v --cov=. --cov-fail-under=80

# Frontend
source /home/iants/.nvm/nvm.sh
cd /home/iants/BudgetTracker/frontend
npx tsc --noEmit
```

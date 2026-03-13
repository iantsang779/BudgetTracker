---
name: budgettracker-backend-domain
description: Recipe for adding, modifying, debugging, or fixing backend code (model/schema/repo/service/router/tests) in BudgetTracker. Trigger on any backend Python change.
version: 2.0.0
source: local-git-analysis
analyzed_commits: 50
---

# BudgetTracker: Backend Domain Guide

Use this skill whenever **adding, modifying, debugging, or fixing** any backend code in the FastAPI backend — new domains, schema changes, bug fixes, test failures, or router/service edits.

## Bug Fix / Verification Checklist

| Check | Detail |
|-------|--------|
| `amount_base` never in Create payload | Server-computed via `CurrencyService`; give it `= 0.0` default so Pydantic doesn't reject with 422 |
| `from_attributes=True` on Read schemas | Required for SQLAlchemy model → Pydantic serialization |
| `notify_clients(db)` after writes | Any router creating/updating/deleting transactions or income must call this |
| `from __future__ import annotations` | First line of every `.py` file |
| `X | None` not `Optional[X]` | Project uses Python 3.10+ union syntax |
| `client: AsyncClient` on test fixtures | `mypy --strict` requires explicit type annotation on every async test function |
| Restart backend after model changes | SQLite dev uses `create_all` on startup — new columns only appear after restart |

Run after every backend change:

```bash
source /home/iants/BudgetTracker/venv/bin/activate
cd /home/iants/BudgetTracker
python3 -m ruff check --fix backend/ && python3 -m ruff format backend/
python3 -m mypy backend/ --strict
cd backend && pytest tests/ -v --cov=. --cov-fail-under=80
```

## Adding a New Backend Domain

File creation order:

1. `backend/models/{domain}.py`
2. `backend/schemas/{domain}.py`
3. `backend/repositories/{domain}_repository.py`
4. `backend/services/{domain}_service.py` _(if business logic needed)_
5. `backend/routers/{domain}.py`
6. `backend/tests/test_{domain}.py`
7. Register router in `backend/main.py`

See [references.md](./references.md) for code templates for each step.

## Completion Checklist

- [ ] Model added to `backend/models/__init__.py`
- [ ] `amount_base` computed server-side (if monetary); never a required Create field
- [ ] `notify_clients(db)` called after writes that affect metrics
- [ ] Router registered with `/api/v1` prefix in `main.py`
- [ ] Tests cover: create, list, get 404, update, delete
- [ ] ruff + mypy + pytest all pass (commands above)

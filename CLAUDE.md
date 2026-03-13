# BudgetTracker CLAUDE.md

## Project Overview

Desktop-first personal budget tracker. Users log income/expenses, view live KPI metrics, see interactive charts that update on every entry, apply inflation/currency adjustments, and optionally use voice input. Mobile (iOS/Android) is a first-class future concern.

**GitHub:** https://github.com/iantsang779/BudgetTracker
**Git user:** iantsang779 <iantsang779@gmail.com>

---

## Stack

| Layer | Choice |
|---|---|
| Backend | FastAPI + SQLite + SQLAlchemy (async) |
| Frontend | React + TypeScript (Vite) |
| Charts | Plotly.js (`react-plotly.js`) |
| Desktop | Electron (spawns FastAPI child process) |
| Voice (desktop) | Web Speech API (Electron Chromium) |
| Currency | exchangerate-api.com v6 (free tier, API key required) |
| Inflation | BLS CPI API + embedded fallback JSON |

---

## Build Phases & Status

| Phase | Scope | Status |
|---|---|---|
| 1 | Core backend: all 6 models, base repo, accounts/transactions/categories routers + tests | ✅ Done |
| 2 | Income router, `currency_service.py`, `inflation_service.py`, CPI fallback JSON | ✅ Done |
| 3 | `analytics_service.py` (KPI metrics, cumulative spending/savings, by-category), analytics router, `ConnectionManager`, WebSocket broadcasts | ✅ Done |
| 4 | Frontend core: Vite scaffold, Zustand stores, React Query, API client, AppShell, TransactionsPage, IncomePage | ✅ Done |
| 5 | Charts + live updates: Plotly.js charts, MetricsDashboard WebSocket hook, React Query polling (30s) | ✅ Done |
| 6 | Voice input: `voice_service.py` NLP parser, voice router, `useVoiceInput.ts`, `VoiceInputButton` | ⬜ Next |
| 7 | Electron packaging: `electron/main.ts`, preload, PyInstaller spec, `electron-builder` config | ⬜ |
| 8 | Polish: pre-commit hooks (mypy, ruff, tsc), full test suite, `scripts/dev.sh` | ⬜ |

---

## Project Structure

```
BudgetTracker/
├── pyproject.toml              # pytest, ruff, mypy config
├── backend/
│   ├── main.py                 # FastAPI app, router registration, WS /ws/analytics
│   ├── config.py               # Settings (DB URL, API keys, port) via pydantic-settings
│   ├── database.py             # Async SQLAlchemy engine, session factory, Base, get_db()
│   ├── websocket_manager.py    # ConnectionManager singleton (manager), broadcast()
│   ├── models/                 # SQLAlchemy ORM (Mapped[] / mapped_column())
│   ├── schemas/                # Pydantic v2 request/response models
│   ├── repositories/           # Data access layer — NO business logic here
│   │   ├── base_repository.py  # Generic CRUD: get, list, create, update, soft_delete
│   │   ├── transaction_repository.py  # list_filtered() with date/category/account filters
│   │   └── income_repository.py       # list_active() respects effective_date/end_date
│   ├── services/               # Business logic — NO FastAPI coupling
│   │   ├── analytics_service.py
│   │   ├── currency_service.py
│   │   ├── inflation_service.py
│   │   ├── income_helpers.py   # monthly_base(amount_base, recurrence) shared util
│   │   └── voice_service.py    # TODO Phase 6
│   ├── routers/                # FastAPI APIRouter per domain (prefix in router, not main.py)
│   ├── data/cpi_fallback.json  # Embedded US CPI data 2000–present
│   └── tests/
│       ├── conftest.py         # In-memory SQLite, AsyncClient fixture, dependency override
│       └── test_*.py
├── frontend/src/
│   ├── api/                    # Axios client wrappers per domain
│   ├── types/                  # TS interfaces mirroring Pydantic schemas
│   ├── hooks/                  # useTransactions, useAnalytics (React Query), useWebSocket, useVoiceInput
│   ├── store/                  # Zustand: currency, inflation override, UI state
│   ├── components/             # layout/, transactions/, income/, charts/, metrics/, common/
│   └── pages/                  # DashboardPage, TransactionsPage, IncomePage, AnalyticsPage, SettingsPage
└── electron/                   # TODO Phase 7
```

---

## Database Schema

All monetary amounts stored as `REAL` in USD (`amount_base`) at write time; display conversion at read time. Soft deletes via `deleted_at`.

| Table | Key columns |
|---|---|
| `categories` | id, name, color_hex, icon, is_income, deleted_at |
| `accounts` | id, name, currency_code, balance_initial, deleted_at |
| `transactions` | id, account_id, category_id, amount_local, currency_code, amount_base, description, merchant, transaction_date, source (manual/voice), voice_transcript, deleted_at |
| `income_entries` | id, account_id, amount_local, currency_code, amount_base, recurrence (monthly/yearly/one_off), description, effective_date, end_date, deleted_at |
| `currency_rates` | id, base_code, target_code, rate, fetched_at |
| `cpi_snapshots` | id, country_code, period (YYYY-MM), cpi_value, source |

---

## Implemented API Endpoints (`/api/v1`)

| Router | Routes |
|---|---|
| `/accounts` | GET /, POST /, GET /{id}, PATCH /{id}, DELETE /{id} |
| `/categories` | GET /?is_income=, POST /, GET /{id}, PATCH /{id}, DELETE /{id} |
| `/transactions` | GET /?account_id&category_id&currency_code&source&date_from&date_to, POST /, GET /{id}, PATCH /{id}, DELETE /{id} |
| `/income` | GET /, POST /, GET /summary, GET /{id}, PATCH /{id}, DELETE /{id} |
| `/currency` | GET /rates, POST /rates/refresh, POST /convert |
| `/analytics` | GET /metrics, GET /spending-cumulative?year=, GET /savings-cumulative?year=, GET /spending-by-category?start_date&end_date, GET /spending-over-time |
| `WS /ws/analytics` | Pushes `{"event":"metrics_updated","data":{...MetricsResponse}}` on every write |

---

## Key Implementation Details

### Analytics Service
- `get_metrics()` → `MetricsResponse`: total_spending_base, savings_rate, monthly_income_base
- `get_cumulative_spending(year?)` → monthly totals + running cumulative, filtered to year
- `get_cumulative_savings(year?)` → per-month income/spending/saving/running cumulative; capped at current month
- `get_spending_by_category(start_date?, end_date?)` → groups by category_id (null = "Uncategorized"), with percentage
- Year validation: `Query(None, ge=2000, le=2100)` on cumulative endpoints (422 if out of range)

### WebSocket Live Updates
- `ConnectionManager` singleton `manager` — import from `websocket_manager.py`
- `notify_clients(db)` in `routers/analytics.py` — call after every write in transactions/income routers
- Dead connections pruned silently on broadcast

### Currency Service
- Fetches from exchangerate-api.com v6; 24h TTL cache in `currency_rates` table
- `EXCHANGERATE_API_KEY` in `.env`; returns 1.0 if key missing or API fails

### Inflation Service
- `get_annual_rate()`: user override → trailing 12-month CPI CAGR → 3.5% default
- BLS series CUUR0000SA0; fallback: `data/cpi_fallback.json`

### Patterns Used Everywhere
- `get_db()`: yields `AsyncSession`, commits on exit, rolls back on exception
- `BaseRepository`: `get`, `list`, `create` (flush+refresh), `update`, `soft_delete`
- All schemas: `from_attributes=True` on Read models; `X | None` not `Optional[X]`
- `amount_base` is server-computed — never in TypeScript Create/Update types

---

## Python Rules (project-specific)

> General style, linting, and type hint rules are in `~/.claude/rules/common/coding-style.md`.
> For testing workflow, use `/pytest-tdd` skill.
> For code review, use `/python-review` skill.

- All files: `from __future__ import annotations` (line 1)
- Google-style docstrings on all public functions, classes, modules
- No repeated logic: shared queries → `repositories/`, shared logic → `services/`
- After any code change: run ruff + mypy **automatically without asking**

## TypeScript Rules (Phase 4+)

> General rules are in `~/.claude/rules/common/coding-style.md`.

- `strict: true` in tsconfig.json — no `any` types
- React Query for data fetching; Zustand for global state

## Git Rules

> Full workflow is in `~/.claude/rules/common/git-workflow.md`.

- NEVER `git push` without explicit user permission

---

## Dev Commands

```bash
# Activate venv (always required first)
source /home/iants/BudgetTracker/venv/bin/activate

# Backend tests (see /pytest-tdd skill for TDD workflow)
cd backend && pytest tests/ -v --cov=. --cov-fail-under=80

# Type check + lint
python3 -m mypy backend/ --strict
python3 -m ruff check backend/ && python3 -m ruff format --check backend/
python3 -m ruff check --fix backend/ && python3 -m ruff format backend/
```

### Starting dev servers

**Backend** — run from project root so `backend.*` imports resolve:
```bash
source /home/iants/BudgetTracker/venv/bin/activate
cd /home/iants/BudgetTracker
uvicorn backend.main:app --reload --port 8000
```

**Frontend** — Vite proxies `/api` and `/ws` to `localhost:8000`:
```bash
source /home/iants/.nvm/nvm.sh
cd /home/iants/BudgetTracker/frontend
npm run dev
```

Open http://localhost:5173 — both servers must be running simultaneously.

---

## Phase 6 — Voice Input (Next)

### Files to create

| File | Purpose |
|---|---|
| `backend/services/voice_service.py` | NLP parser: extract amount, category, merchant, date from transcript |
| `backend/routers/voice.py` | `POST /voice/parse` → `VoiceParseResponse` |
| `frontend/src/hooks/useVoiceInput.ts` | Web Speech API hook: start/stop, transcript, parsed result |
| `frontend/src/components/transactions/VoiceInputButton.tsx` | Mic button: triggers hook, shows transcript, auto-fills TransactionForm |

### voice_service.py spec
- Input: raw transcript string
- Output: `VoiceParseResponse` with `amount`, `currency_code`, `description`, `merchant`, `transaction_date`, `category_hint`, `confidence`
- Use regex + keyword matching (no external ML)
- Example: `"spent 42 dollars on coffee at Starbucks"` → `{amount: 42, currency: USD, merchant: "Starbucks", category_hint: "coffee"}`

### useVoiceInput.ts spec
- `window.SpeechRecognition` / `window.webkitSpeechRecognition`
- Returns `{ listening, transcript, start, stop, parseResult }`
- On final transcript: POST to `/api/v1/voice/parse` → auto-populate form fields

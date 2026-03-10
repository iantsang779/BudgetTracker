# BudgetTracker CLAUDE.md

## Project Overview

Desktop-first personal budget tracker. Users log income/expenses, view live KPI metrics with regression-based spending predictions, see interactive charts that update on every entry, apply inflation/currency adjustments, and optionally use voice input. Mobile (iOS/Android) is a first-class future concern.

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
| Regression | scikit-learn `LinearRegression` |
| Voice (desktop) | Web Speech API (Electron Chromium) |
| Currency | exchangerate.host (free, no API key) |
| Inflation | BLS CPI API + embedded fallback JSON |

---

## Build Phases & Status

| Phase | Scope | Status |
|---|---|---|
| 1 | Core backend: all 6 models, base repo, accounts/transactions/categories routers + tests | ✅ Done |
| 2 | Income router, `currency_service.py`, `inflation_service.py`, CPI fallback JSON | ✅ Done |
| 3 | `analytics_service.py` (regression), analytics router, `ConnectionManager`, WebSocket broadcasts | ✅ Done |
| 4 | Frontend core: Vite scaffold, Zustand stores, React Query, API client, AppShell, TransactionsPage, IncomePage | ✅ Done |
| 5 | Charts + live updates: Plotly.js charts, MetricsDashboard WebSocket hook, React Query polling (30s) | ✅ Done |
| 6 | Voice input: `voice_service.py` NLP parser, voice router, `useVoiceInput.ts`, `VoiceInputButton` | ⬜ Next |
| 7 | Electron packaging: `electron/main.ts`, preload, PyInstaller spec, `electron-builder` config | ⬜ |
| 8 | Polish: pre-commit hooks (mypy, ruff, tsc), full test suite, `scripts/dev.sh` | ⬜ |

---

## Project Structure

```
BudgetTracker/
├── CLAUDE.md
├── pyproject.toml              # pytest, ruff, mypy config
├── scripts/
│   ├── dev.sh                  # Start backend + frontend concurrently (TODO Phase 8)
│   └── build.sh                # Build frontend, package Electron (TODO Phase 8)
├── backend/
│   ├── main.py                 # FastAPI app, router registration, WS /ws/analytics
│   ├── config.py               # Settings (DB URL, API keys, port) via pydantic-settings
│   ├── database.py             # Async SQLAlchemy engine, session factory, Base, get_db()
│   ├── websocket_manager.py    # ConnectionManager singleton (manager), broadcast()
│   ├── requirements.txt
│   ├── models/                 # SQLAlchemy ORM (Mapped[] / mapped_column())
│   │   ├── account.py, transaction.py, category.py
│   │   ├── income.py, currency_rate.py, cpi_snapshot.py
│   ├── schemas/                # Pydantic v2 request/response models
│   │   ├── account.py, transaction.py, category.py
│   │   ├── income.py, analytics.py, currency.py
│   ├── repositories/           # Data access layer — NO business logic here
│   │   ├── base_repository.py  # Generic CRUD: get, list, create, update, soft_delete
│   │   ├── account_repository.py, category_repository.py
│   │   ├── transaction_repository.py  # list_filtered() with date/category/account filters
│   │   └── income_repository.py       # list_active() respects effective_date/end_date
│   ├── services/               # Business logic — NO FastAPI coupling
│   │   ├── analytics_service.py   # get_metrics(), get_savings_projection(), by-category, over-time
│   │   ├── currency_service.py    # exchangerate.host, 24h TTL cache in DB
│   │   ├── inflation_service.py   # BLS CPI API, fallback JSON, trailing CAGR
│   │   ├── income_helpers.py      # monthly_base(amount_base, recurrence) shared util
│   │   └── voice_service.py       # TODO Phase 6
│   ├── routers/                # FastAPI APIRouter per domain (prefix in router, not main.py)
│   │   ├── accounts.py, categories.py, transactions.py
│   │   ├── income.py, currency.py, analytics.py
│   │   └── voice.py            # TODO Phase 6
│   ├── data/
│   │   └── cpi_fallback.json   # Embedded US CPI data 2000–present
│   ├── migrations/             # Alembic (TODO: initialise in Phase 8)
│   └── tests/
│       ├── conftest.py         # In-memory SQLite, AsyncClient fixture, dependency override
│       └── test_*.py           # test_accounts, categories, transactions, income, currency, analytics
├── frontend/                   # TODO Phase 4
│   ├── vite.config.ts
│   ├── tsconfig.json           # strict: true
│   └── src/
│       ├── api/                # Axios client wrappers per domain
│       ├── types/              # TS interfaces mirroring Pydantic schemas
│       ├── hooks/
│       │   ├── useTransactions.ts, useAnalytics.ts  (React Query)
│       │   ├── useVoiceInput.ts   (Web Speech API)
│       │   └── useWebSocket.ts    (auto-reconnect with backoff)
│       ├── store/              # Zustand: currency, inflation override, UI state
│       ├── components/
│       │   ├── layout/         # AppShell, Sidebar, TopBar
│       │   ├── transactions/   # TransactionList, TransactionForm, VoiceInputButton
│       │   ├── income/         # IncomeForm, IncomeList, IncomeSummaryCard
│       │   ├── charts/         # SavingsProjectionChart, SpendingByCategoryChart, SpendingTrendChart
│       │   ├── metrics/        # MetricsDashboard (KPI cards, WebSocket-driven)
│       │   └── common/         # CurrencySelector, DateRangePicker, LoadingSpinner
│       └── pages/              # DashboardPage, TransactionsPage, IncomePage, AnalyticsPage, SettingsPage
└── electron/                   # TODO Phase 7
    ├── main.ts                 # Spawn FastAPI, health-check loop, load renderer
    └── preload.ts              # contextBridge IPC (expose port to renderer)
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
| `/analytics` | GET /metrics, GET /savings-projection?months_ahead=6, GET /spending-by-category?start_date&end_date, GET /spending-over-time |
| `WS /ws/analytics` | Pushes `{"event":"metrics_updated","data":{...MetricsResponse}}` on every write |

---

## Key Implementation Details

### Analytics Service (`backend/services/analytics_service.py`)
- `get_metrics()` → `MetricsResponse`: total_spending_base, predicted_monthly_base, savings_rate, inflation_adjusted_spending, monthly_income_base, regression_slope, regression_r2
- `get_savings_projection()` → `SavingsProjectionResponse`: `points` list of `ProjectionPoint` (period, actual|None, predicted, upper_band, lower_band), slope, r2_score, error_std
- `get_spending_by_category()` → `SpendingByCategoryResponse`: groups by category_id (null = "Uncategorized")
- `get_spending_over_time()` → `SpendingOverTimeResponse`: monthly timeseries
- Regression: `LinearRegression` on month-index vs total; fallback to average if <3 months
- Private helpers: `_monthly_spend_totals()`, `_fit_regression()` → `_RegResult` NamedTuple, `_add_months(period, n)`

### WebSocket Live Updates (`backend/websocket_manager.py`)
- `ConnectionManager` singleton `manager` imported everywhere needed
- `notify_clients(db)` in `routers/analytics.py` — call after every write in transactions/income routers
- Dead connections pruned silently on broadcast

### Currency Service (`backend/services/currency_service.py`)
- Fetches from exchangerate.host; 24h TTL cache in `currency_rates` table
- Falls back to rate=1.0 on API failure

### Inflation Service (`backend/services/inflation_service.py`)
- `get_annual_rate()`: user override → trailing 12-month CPI CAGR → 3.5% default
- `ensure_cpi_loaded()`: loads `data/cpi_fallback.json` if DB empty
- `fetch_latest_bls(api_key)`: BLS series CUUR0000SA0

### Income Helpers (`backend/services/income_helpers.py`)
- `monthly_base(amount_base, recurrence)`: converts yearly→/12, one_off→0

### Patterns Used Everywhere
- `get_db()` dependency: yields `AsyncSession`, commits on exit, rolls back on exception
- `BaseRepository`: `get`, `list`, `create` (flush+refresh), `update`, `soft_delete`
- All schemas: `from_attributes=True` on Read models; `X | None` not `Optional[X]`
- `ruff check --fix` auto-fixes I001 (import sort); E402 ignored (future-import pattern)

---

## Python Rules
- All files: `from __future__ import annotations` (line 1)
- Strict type annotations everywhere; `X | None` not `Optional[X]`
- Google-style docstrings on all public functions, classes, modules
- No repeated logic: shared queries → `repositories/`, shared logic → `services/`
- `mypy backend/ --strict` must pass — use `source venv/bin/activate && python3 -m mypy backend/ --strict`
- `ruff check` + `ruff format` — use `python3 -m ruff check backend/ && python3 -m ruff format --check backend/`
- After any code change: run ruff + mypy automatically without asking

## TypeScript Rules (Phase 4+)
- `strict: true` in tsconfig.json
- No `any` types
- All components typed
- React Query for data fetching; Zustand for global state

## Git Rules
- Auto stage + commit after each logical change with conventional commit message
- NEVER `git push` without explicit user permission
- Remote: `origin` → https://github.com/iantsang779/BudgetTracker

## Dev Commands
- Activate venv first: `source /home/iants/BudgetTracker/venv/bin/activate`
- Backend tests: `cd backend && pytest tests/ -v --cov=. --cov-fail-under=80`
- Type check: `python3 -m mypy backend/ --strict`
- Lint check: `python3 -m ruff check backend/ && python3 -m ruff format --check backend/`
- Lint fix: `python3 -m ruff check --fix backend/ && python3 -m ruff format backend/`
- Start dev (Phase 8): `bash scripts/dev.sh` → FastAPI :8000, React :5173

---

## Phase 6 — Voice Input (Next)

Implement voice-based transaction entry using the Web Speech API in Electron's Chromium and a backend NLP parser.

### Files to create

| File | Purpose |
|---|---|
| `backend/services/voice_service.py` | NLP parser: extract amount, category, merchant, date from transcript |
| `backend/routers/voice.py` | `POST /voice/parse` → `VoiceParseResponse` |
| `frontend/src/hooks/useVoiceInput.ts` | Web Speech API hook: start/stop, transcript, parsed result |
| `frontend/src/components/transactions/VoiceInputButton.tsx` | Mic button: triggers hook, shows transcript, auto-fills TransactionForm |

### voice_service.py notes
- Input: raw transcript string
- Output: `VoiceParseResponse` with `amount`, `currency_code`, `description`, `merchant`, `transaction_date`, `category_hint`, `confidence`
- Use regex + keyword matching (no external ML dependency for Phase 6)
- Examples: "spent 42 dollars on coffee at Starbucks" → `{amount: 42, currency: USD, merchant: "Starbucks", category_hint: "coffee"}`

### useVoiceInput.ts notes
- `window.SpeechRecognition` / `window.webkitSpeechRecognition`
- Returns `{ listening, transcript, start, stop, parseResult }`
- On final transcript: POST to `/api/v1/voice/parse` → auto-populate form fields

### Dev commands
```bash
source /home/iants/.nvm/nvm.sh
cd frontend && npm run dev   # frontend :5173
# separate terminal:
source venv/bin/activate && cd backend && uvicorn main:app --reload --port 8000
```

### Verification
- `npx tsc --noEmit` → 0 errors
- `pytest tests/ -v --cov=. --cov-fail-under=80`
- Click mic button → speak → transcript appears → form fields auto-filled

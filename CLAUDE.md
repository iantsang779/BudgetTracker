# BudgetTracker CLAUDE.md

## Python Rules
- All files: `from __future__ import annotations`
- Strict type annotations everywhere; use `X | None` (not `Optional[X]`)
- Google-style docstrings on all public functions, classes, and modules
- No repeated logic: shared queries → repositories/, shared logic → services/
- `mypy backend/ --strict` must pass (zero errors)
- `ruff check` + `ruff format` on all Python

## TypeScript Rules
- `strict: true` in tsconfig.json
- No `any` types
- All components typed

## Git Rules
- Auto stage + commit after each logical change with conventional commit message
- NEVER `git push` without explicit user permission
- GitHub repository: https://github.com/iantsang779/BudgetTracker
- Git user: iantsang779 <iantsang779@gmail.com>

## Dev Commands
- Start dev: `bash scripts/dev.sh`
- Backend tests: `cd backend && pytest tests/ -v --cov=. --cov-fail-under=80`
- Type check: `mypy backend/ --strict`
- Lint: `ruff check backend/ && ruff format --check backend/`

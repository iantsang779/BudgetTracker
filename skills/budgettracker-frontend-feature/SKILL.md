---
name: budgettracker-frontend-feature
description: Recipe for adding, modifying, debugging, or fixing frontend code (types/api/hooks/components/pages) in BudgetTracker. Trigger on any frontend TypeScript/TSX change.
version: 2.0.0
source: local-git-analysis
analyzed_commits: 50
---

# BudgetTracker: Frontend Feature Guide

Use this skill whenever **adding, modifying, debugging, or fixing** any frontend code in BudgetTracker — new features, component edits, bug fixes, type errors, or hook changes.

## Bug Fix / Verification Checklist

| Check | Detail |
|-------|--------|
| `amount_base` never in Create/Update types | Server-computed; omit from `DomainCreate` / `DomainUpdate` interfaces |
| `string \| null` for nullable DB fields | Not `string \| undefined` — mirrors nullable DB columns |
| `useCallback` for callbacks passed as props | Prevents child `useEffect` re-running on every parent render when callback is a dep |
| `strict: true` — no `any` | Run `npx tsc --noEmit` after every change |
| `displayCurrency` from `useAppStore` | Global currency state; use `useCurrencyRate` hook for conversion factor |
| `invalidateQueries` in every mutation | All React Query mutations must invalidate their query key on success |
| Currency dropdown from `CURRENCIES` constant | Use `frontend/src/constants/currencies.ts`, never a hand-rolled list |

Run after every frontend change:

```bash
source /home/iants/.nvm/nvm.sh
cd /home/iants/BudgetTracker/frontend
npx tsc --noEmit
```

## Adding a New Frontend Feature

File creation order:

1. `frontend/src/types/index.ts` — add TS interfaces
2. `frontend/src/api/{domain}.ts` — Axios wrapper
3. `frontend/src/hooks/use{Domain}.ts` — React Query hook
4. `frontend/src/components/{domain}/` — reusable components
5. `frontend/src/pages/{Domain}Page.tsx` — page with form + list

See [references.md](./references.md) for code templates for each step.

## Completion Checklist

- [ ] Types added: `Create`, `Update`, `Read` — no `amount_base` in Create/Update
- [ ] API client wraps all CRUD endpoints
- [ ] React Query hook with `invalidateQueries` on mutations
- [ ] Page renders loading state, form, and list
- [ ] Route added in `App.tsx`; nav link in `Sidebar.tsx`
- [ ] `npx tsc --noEmit` passes with no errors

# Frontend Feature — Code Templates

## Types — `frontend/src/types/index.ts`

Add a section with `Create`, `Update`, `Read` interfaces mirroring Pydantic schemas:

```typescript
// ── Domain ────────────────────────────────────────────────────────────────────

export interface DomainCreate {
  name: string
  amount_local: number
  currency_code: string
  // NOTE: never include amount_base — server-computed
}

export interface DomainUpdate {
  name?: string
  amount_local?: number
  currency_code?: string
}

export interface DomainRead {
  id: number
  name: string
  amount_local: number
  amount_base: number   // present in Read, never in Create/Update
  currency_code: string
  deleted_at: string | null
}
```

Rules:
- `strict: true` — no `any`
- Use `string | null` not `string | undefined` for nullable DB fields
- Never include `amount_base` in Create/Update types

---

## API Client — `frontend/src/api/{domain}.ts`

```typescript
import apiClient from './client'
import type { DomainCreate, DomainRead, DomainUpdate } from '../types'

export async function getDomains(): Promise<DomainRead[]> {
  const { data } = await apiClient.get<DomainRead[]>('/domains/')
  return data
}

export async function createDomain(payload: DomainCreate): Promise<DomainRead> {
  const { data } = await apiClient.post<DomainRead>('/domains/', payload)
  return data
}

export async function updateDomain(id: number, payload: DomainUpdate): Promise<DomainRead> {
  const { data } = await apiClient.patch<DomainRead>(`/domains/${id}`, payload)
  return data
}

export async function deleteDomain(id: number): Promise<void> {
  await apiClient.delete(`/domains/${id}`)
}
```

`apiClient` is the Axios instance at `frontend/src/api/client.ts` with baseURL `/api/v1`.

---

## React Query Hook — `frontend/src/hooks/use{Domain}.ts`

```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createDomain, deleteDomain, getDomains, updateDomain } from '../api/domain'
import type { DomainCreate, DomainUpdate } from '../types'

const QUERY_KEY = ['domains'] as const

export function useDomains() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: getDomains,
    refetchInterval: 30_000,
  })
}

export function useCreateDomain() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: DomainCreate) => createDomain(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useUpdateDomain() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: DomainUpdate }) => updateDomain(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}

export function useDeleteDomain() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteDomain(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  })
}
```

---

## Page — `frontend/src/pages/{Domain}Page.tsx`

Follow the existing pattern (TransactionsPage / IncomePage):

```typescript
import { useState } from 'react'
import { useDomains, useCreateDomain, useDeleteDomain } from '../hooks/useDomain'
import { CURRENCIES } from '../constants/currencies'

const inputStyle: React.CSSProperties = {
  background: '#313244',
  border: '1px solid #45475a',
  borderRadius: 6,
  padding: '6px 10px',
  color: '#cdd6f4',
  fontSize: 13,
}

export default function DomainPage() {
  const { data: domains = [], isLoading } = useDomains()
  const createMutation = useCreateDomain()
  const deleteMutation = useDeleteDomain()
  const [form, setForm] = useState({ name: '', amount_local: 0, currency_code: 'GBP' })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    createMutation.mutate(form)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Domains</h1>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <input
          style={inputStyle}
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
        />
        <input
          style={inputStyle}
          type="number"
          step="0.01"
          placeholder="Amount"
          value={form.amount_local}
          onChange={(e) => setForm((prev) => ({ ...prev, amount_local: Number(e.target.value) }))}
        />
        <select
          style={inputStyle}
          value={form.currency_code}
          onChange={(e) => setForm((prev) => ({ ...prev, currency_code: e.target.value }))}
        >
          {CURRENCIES.map((code) => <option key={code} value={code}>{code}</option>)}
        </select>
        <button type="submit" style={{ ...inputStyle, background: '#a6e3a1', color: '#1e1e2e', fontWeight: 600, cursor: 'pointer', border: 'none' }}>
          Save
        </button>
      </form>

      {isLoading ? (
        <p style={{ color: '#6c7086' }}>Loading…</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #313244', textAlign: 'left', color: '#6c7086' }}>
              <th style={{ padding: '6px 12px' }}>Name</th>
              <th style={{ padding: '6px 12px' }}></th>
            </tr>
          </thead>
          <tbody>
            {domains.map((d) => (
              <tr key={d.id} style={{ borderBottom: '1px solid #313244' }}>
                <td style={{ padding: '8px 12px' }}>{d.name}</td>
                <td style={{ padding: '8px 12px' }}>
                  <button
                    onClick={() => deleteMutation.mutate(d.id)}
                    style={{ background: 'none', border: 'none', color: '#f38ba8', cursor: 'pointer', fontSize: 13 }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
```

Register page in `frontend/src/App.tsx` with a `<Route>` and add nav link in `frontend/src/components/layout/Sidebar.tsx`.

---

## WebSocket Integration (if metrics-affecting)

If writes affect metrics, the WS update is automatic — no frontend changes needed. Any backend write that calls `notify_clients(db)` pushes a `metrics_updated` event, which `useWebSocket.ts` handles by invalidating the `['metrics']` query.

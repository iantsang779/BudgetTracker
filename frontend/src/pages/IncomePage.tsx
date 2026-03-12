import { useState } from 'react'
import { useIncomes, useIncomeSummary, useCreateIncome, useUpdateIncome, useDeleteIncome } from '../hooks/useIncome'
import { useCurrencyRate, fmtCurrency } from '../hooks/useCurrency'
import useAppStore from '../store/useAppStore'
import { CURRENCIES } from '../constants/currencies'
import type { IncomeCreate, IncomeRead, Recurrence } from '../types'

const today = new Date().toISOString().slice(0, 10)

const defaultForm: IncomeCreate = {
  account_id: 1,
  amount_local: 0,
  currency_code: 'GBP',
  amount_base: 0,
  recurrence: 'monthly',
  description: '',
  effective_date: today,
  end_date: null,
}

const inputStyle: React.CSSProperties = {
  background: '#313244',
  border: '1px solid #45475a',
  borderRadius: 6,
  padding: '6px 10px',
  color: '#cdd6f4',
  fontSize: 13,
}

const card: React.CSSProperties = {
  background: '#181825',
  border: '1px solid #313244',
  borderRadius: 10,
  padding: '16px 20px',
  minWidth: 160,
}

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

function groupByMonth(incomes: IncomeRead[]): Map<string, IncomeRead[]> {
  const groups = new Map<string, IncomeRead[]>()
  for (const inc of incomes) {
    const d = new Date(inc.effective_date)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    const existing = groups.get(key)
    if (existing) {
      existing.push(inc)
    } else {
      groups.set(key, [inc])
    }
  }
  return new Map([...groups.entries()].sort((a, b) => b[0].localeCompare(a[0])))
}

function formatMonthKey(key: string): string {
  const [year, month] = key.split('-')
  return `${MONTH_NAMES[Number(month) - 1]} ${year}`
}

export default function IncomePage() {
  const [form, setForm] = useState<IncomeCreate>(defaultForm)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  const displayCurrency = useAppStore((s) => s.displayCurrency)
  const { data: rateData } = useCurrencyRate(displayCurrency)
  const rate = displayCurrency === 'USD' ? 1 : (rateData?.rate ?? 1)

  const { data: incomes, isLoading } = useIncomes()
  const { data: summary } = useIncomeSummary()
  const createMutation = useCreateIncome()
  const updateMutation = useUpdateIncome()
  const deleteMutation = useDeleteIncome()

  function handleEdit(inc: IncomeRead) {
    setForm({
      account_id: inc.account_id,
      amount_local: inc.amount_local,
      currency_code: inc.currency_code,
      amount_base: inc.amount_base,
      recurrence: inc.recurrence as Recurrence,
      description: inc.description ?? '',
      effective_date: inc.effective_date.slice(0, 10),
      end_date: null,
    })
    setEditingId(inc.id)
    setShowForm(true)
  }

  function handleCancel() {
    setForm(defaultForm)
    setEditingId(null)
    setShowForm(false)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (editingId !== null) {
      updateMutation.mutate({ id: editingId, data: form }, { onSuccess: handleCancel })
    } else {
      createMutation.mutate(form, {
        onSuccess: () => {
          setForm(defaultForm)
          setShowForm(false)
        },
      })
    }
  }

  const grouped = incomes ? groupByMonth(incomes) : new Map<string, IncomeRead[]>()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Income</h1>
        <button
          onClick={() => (showForm && editingId === null ? handleCancel() : setShowForm((v) => !v))}
          style={{ ...inputStyle, cursor: 'pointer', background: '#cba6f7', color: '#1e1e2e', fontWeight: 600, border: 'none' }}
        >
          {showForm ? 'Cancel' : '+ New Income'}
        </button>
      </div>

      {/* Summary cards */}
      {summary && (
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <div style={card}>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', color: '#6c7086', marginBottom: 6 }}>Monthly Total</div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{fmtCurrency(summary.monthly_total_base * rate, displayCurrency)}</div>
          </div>
          <div style={card}>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', color: '#6c7086', marginBottom: 6 }}>Yearly Total</div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{fmtCurrency(summary.yearly_total_base * rate, displayCurrency)}</div>
          </div>
          <div style={card}>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', color: '#6c7086', marginBottom: 6 }}>Active Sources</div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{summary.active_sources}</div>
          </div>
        </div>
      )}

      {/* Form */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          style={{ display: 'flex', flexWrap: 'wrap', gap: 10, background: '#181825', padding: 16, borderRadius: 10, border: '1px solid #313244' }}
        >
          <input style={inputStyle} type="number" step="0.01" placeholder="Amount" required
            value={form.amount_local || ''}
            onChange={(e) => {
              const val = Number(e.target.value)
              setForm({ ...form, amount_local: val, amount_base: val })
            }} />
          <select style={inputStyle}
            value={form.currency_code}
            onChange={(e) => setForm({ ...form, currency_code: e.target.value })}>
            {CURRENCIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select style={inputStyle}
            value={form.recurrence}
            onChange={(e) => setForm({ ...form, recurrence: e.target.value as Recurrence })}>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
          </select>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <label style={{ fontSize: 11, color: '#6c7086' }}>Date</label>
            <input style={inputStyle} type="date" required
              value={form.effective_date}
              onChange={(e) => setForm({ ...form, effective_date: e.target.value })} />
          </div>
          <input style={inputStyle} placeholder="Description"
            value={form.description ?? ''}
            onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <button type="submit" style={{ ...inputStyle, background: '#a6e3a1', color: '#1e1e2e', fontWeight: 600, cursor: 'pointer', border: 'none' }}>
            {editingId !== null ? 'Save Changes' : 'Save'}
          </button>
          {editingId !== null && (
            <button type="button" onClick={handleCancel} style={{ ...inputStyle, cursor: 'pointer', border: 'none' }}>
              Cancel
            </button>
          )}
        </form>
      )}

      {/* Grouped list */}
      {isLoading ? (
        <p style={{ color: '#6c7086' }}>Loading…</p>
      ) : !incomes?.length ? (
        <p style={{ color: '#6c7086' }}>No income entries found.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {[...grouped.entries()].map(([monthKey, entries]) => {
            const monthTotal = entries.reduce((sum, inc) => sum + inc.amount_base * rate, 0)
            return (
              <div key={monthKey}>
                {/* Month header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: '#a6e3a1', textTransform: 'uppercase', letterSpacing: 1 }}>
                    {formatMonthKey(monthKey)}
                  </span>
                  <span style={{ fontSize: 12, color: '#6c7086' }}>
                    {fmtCurrency(monthTotal, displayCurrency)} · {entries.length} source{entries.length !== 1 ? 's' : ''}
                  </span>
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid #313244', textAlign: 'left', color: '#6c7086' }}>
                        <th style={{ padding: '6px 12px' }}>Description</th>
                        <th style={{ padding: '6px 12px' }}>Amount ({displayCurrency})</th>
                        <th style={{ padding: '6px 12px' }}>Recurrence</th>
                        <th style={{ padding: '6px 12px' }}>Effective Date</th>
                        <th style={{ padding: '6px 12px' }}>End Date</th>
                        <th style={{ padding: '6px 12px' }}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {entries.map((inc) => (
                        <tr key={inc.id} style={{ borderBottom: '1px solid #313244', background: editingId === inc.id ? '#1e1e2e' : 'transparent' }}>
                          <td style={{ padding: '8px 12px' }}>{inc.description || '—'}</td>
                          <td style={{ padding: '8px 12px' }}>{fmtCurrency(inc.amount_base * rate, displayCurrency)}</td>
                          <td style={{ padding: '8px 12px' }}>
                            <span style={{ fontSize: 11, background: '#313244', color: '#a6e3a1', borderRadius: 4, padding: '2px 6px' }}>
                              {inc.recurrence}
                            </span>
                          </td>
                          <td style={{ padding: '8px 12px' }}>{inc.effective_date.slice(0, 10)}</td>
                          <td style={{ padding: '8px 12px' }}>{inc.end_date ? inc.end_date.slice(0, 10) : '—'}</td>
                          <td style={{ padding: '8px 12px', display: 'flex', gap: 8 }}>
                            <button
                              onClick={() => handleEdit(inc)}
                              style={{ background: 'none', border: 'none', color: '#89b4fa', cursor: 'pointer', fontSize: 13 }}
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => deleteMutation.mutate(inc.id)}
                              style={{ background: 'none', border: 'none', color: '#f38ba8', cursor: 'pointer', fontSize: 13 }}
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

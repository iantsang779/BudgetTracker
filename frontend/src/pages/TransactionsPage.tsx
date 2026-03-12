import { useState } from 'react'
import {
  useTransactions,
  useCreateTransaction,
  useUpdateTransaction,
  useDeleteTransaction,
} from '../hooks/useTransactions'
import { useCategories } from '../hooks/useCategories'
import { useCurrencyRate, fmtCurrency } from '../hooks/useCurrency'
import { CURRENCIES } from '../constants/currencies'
import useAppStore from '../store/useAppStore'
import type { TransactionCreate, TransactionFilters, TransactionRead, TransactionRecurrence } from '../types'

const today = new Date().toISOString().slice(0, 10)

const defaultForm: TransactionCreate = {
  account_id: 1,
  category_id: null,
  amount_local: 0,
  currency_code: 'GBP',
  amount_base: 0,
  description: '',
  merchant: '',
  transaction_date: today,
  source: 'manual',
  recurrence: null,
}

const inputStyle: React.CSSProperties = {
  background: '#313244',
  border: '1px solid #45475a',
  borderRadius: 6,
  padding: '6px 10px',
  color: '#cdd6f4',
  fontSize: 13,
}

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

function groupByMonth(transactions: TransactionRead[]): Map<string, TransactionRead[]> {
  const groups = new Map<string, TransactionRead[]>()
  for (const t of transactions) {
    const d = new Date(t.transaction_date)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    const existing = groups.get(key)
    if (existing) {
      existing.push(t)
    } else {
      groups.set(key, [t])
    }
  }
  // Sort keys descending
  return new Map([...groups.entries()].sort((a, b) => b[0].localeCompare(a[0])))
}

function formatMonthKey(key: string): string {
  const [year, month] = key.split('-')
  return `${MONTH_NAMES[Number(month) - 1]} ${year}`
}

export default function TransactionsPage() {
  const [filters, setFilters] = useState<TransactionFilters>({})
  const [form, setForm] = useState<TransactionCreate>(defaultForm)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [isRecurring, setIsRecurring] = useState(false)

  const displayCurrency = useAppStore((s) => s.displayCurrency)
  const { data: rateData } = useCurrencyRate(displayCurrency)
  const rate = displayCurrency === 'USD' ? 1 : (rateData?.rate ?? 1)

  const { data: transactions, isLoading } = useTransactions(filters)
  const { data: expenseCategories } = useCategories(false)
  const createMutation = useCreateTransaction()
  const updateMutation = useUpdateTransaction()
  const deleteMutation = useDeleteTransaction()

  function handleFilterChange(key: keyof TransactionFilters, value: string) {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }))
  }

  function handleEdit(t: TransactionRead) {
    const recurring = t.recurrence !== null
    setIsRecurring(recurring)
    setForm({
      account_id: t.account_id,
      category_id: t.category_id,
      amount_local: t.amount_local,
      currency_code: t.currency_code,
      amount_base: t.amount_base,
      description: t.description ?? '',
      merchant: t.merchant ?? '',
      transaction_date: t.transaction_date.slice(0, 10),
      source: t.source,
      recurrence: t.recurrence,
    })
    setEditingId(t.id)
    setShowForm(true)
  }

  function handleCancel() {
    setForm(defaultForm)
    setEditingId(null)
    setShowForm(false)
    setIsRecurring(false)
  }

  function handleRecurringToggle(checked: boolean) {
    setIsRecurring(checked)
    setForm((prev) => ({ ...prev, recurrence: checked ? 'monthly' : null }))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload = { ...form, recurrence: isRecurring ? form.recurrence : null }
    if (editingId !== null) {
      updateMutation.mutate({ id: editingId, data: payload }, { onSuccess: handleCancel })
    } else {
      createMutation.mutate(payload, {
        onSuccess: () => {
          setForm(defaultForm)
          setIsRecurring(false)
          setShowForm(false)
        },
      })
    }
  }

  const grouped = transactions ? groupByMonth(transactions) : new Map<string, TransactionRead[]>()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Transactions</h1>
        <button
          onClick={() => (showForm && editingId === null ? handleCancel() : setShowForm((v) => !v))}
          style={{ ...inputStyle, cursor: 'pointer', background: '#cba6f7', color: '#1e1e2e', fontWeight: 600, border: 'none' }}
        >
          {showForm ? 'Cancel' : '+ New Transaction'}
        </button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <input
          style={inputStyle}
          type="date"
          placeholder="From"
          value={filters.date_from ?? ''}
          onChange={(e) => handleFilterChange('date_from', e.target.value)}
        />
        <input
          style={inputStyle}
          type="date"
          placeholder="To"
          value={filters.date_to ?? ''}
          onChange={(e) => handleFilterChange('date_to', e.target.value)}
        />
      </div>

      {/* Form */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          style={{ display: 'flex', flexWrap: 'wrap', gap: 10, background: '#181825', padding: 16, borderRadius: 10, border: '1px solid #313244' }}
        >
          <input style={inputStyle} type="number" step="0.01" placeholder="Amount (local)" required
            value={form.amount_local}
            onChange={(e) => setForm({ ...form, amount_local: Number(e.target.value), amount_base: Number(e.target.value) })} />
          <select style={inputStyle} required
            value={form.currency_code}
            onChange={(e) => setForm({ ...form, currency_code: e.target.value })}>
            {CURRENCIES.map((code) => (
              <option key={code} value={code}>{code}</option>
            ))}
          </select>
          <select
            style={inputStyle}
            value={form.category_id ?? ''}
            onChange={(e) => setForm({ ...form, category_id: e.target.value ? Number(e.target.value) : null })}
          >
            <option value="">— Category —</option>
            {expenseCategories?.map((cat) => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>
          <input style={inputStyle} placeholder="Merchant"
            value={form.merchant ?? ''}
            onChange={(e) => setForm({ ...form, merchant: e.target.value })} />
          <input style={inputStyle} placeholder="Description"
            value={form.description ?? ''}
            onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <input style={inputStyle} type="date" required
            value={form.transaction_date}
            onChange={(e) => setForm({ ...form, transaction_date: e.target.value })} />

          {/* Recurring toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 13, color: '#cdd6f4' }}>
              <input
                type="checkbox"
                checked={isRecurring}
                onChange={(e) => handleRecurringToggle(e.target.checked)}
                style={{ accentColor: '#cba6f7', width: 14, height: 14 }}
              />
              Recurring transaction
            </label>
            {isRecurring && (
              <select
                style={inputStyle}
                value={form.recurrence ?? 'monthly'}
                onChange={(e) => setForm({ ...form, recurrence: e.target.value as TransactionRecurrence })}
              >
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
              </select>
            )}
          </div>

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
      ) : !transactions?.length ? (
        <p style={{ color: '#6c7086' }}>No transactions found.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {[...grouped.entries()].map(([monthKey, txns]) => {
            const monthTotal = txns.reduce((sum, t) => sum + t.amount_base * rate, 0)
            return (
              <div key={monthKey}>
                {/* Month header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: '#cba6f7', textTransform: 'uppercase', letterSpacing: 1 }}>
                    {formatMonthKey(monthKey)}
                  </span>
                  <span style={{ fontSize: 12, color: '#6c7086' }}>
                    {fmtCurrency(monthTotal, displayCurrency)} · {txns.length} transaction{txns.length !== 1 ? 's' : ''}
                  </span>
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid #313244', textAlign: 'left', color: '#6c7086' }}>
                        <th style={{ padding: '6px 12px' }}>Date</th>
                        <th style={{ padding: '6px 12px' }}>Merchant</th>
                        <th style={{ padding: '6px 12px' }}>Description</th>
                        <th style={{ padding: '6px 12px' }}>Amount ({displayCurrency})</th>
                        <th style={{ padding: '6px 12px' }}>Category</th>
                        <th style={{ padding: '6px 12px' }}></th>
                      </tr>
                    </thead>
                    <tbody>
                      {txns.map((t) => (
                        <tr key={t.id} style={{ borderBottom: '1px solid #313244', background: editingId === t.id ? '#1e1e2e' : 'transparent' }}>
                          <td style={{ padding: '8px 12px' }}>{t.transaction_date.slice(0, 10)}</td>
                          <td style={{ padding: '8px 12px' }}>
                            {t.merchant || '—'}
                            {t.recurrence && (
                              <span style={{ marginLeft: 6, fontSize: 10, background: '#313244', color: '#cba6f7', borderRadius: 4, padding: '2px 5px' }}>
                                {t.recurrence}
                              </span>
                            )}
                          </td>
                          <td style={{ padding: '8px 12px' }}>{t.description || '—'}</td>
                          <td style={{ padding: '8px 12px' }}>{fmtCurrency(t.amount_base * rate, displayCurrency)}</td>
                          <td style={{ padding: '8px 12px' }}>
                            {t.category_id
                              ? (expenseCategories?.find((c) => c.id === t.category_id)?.name ?? t.category_id)
                              : '—'}
                          </td>
                          <td style={{ padding: '8px 12px', display: 'flex', gap: 8 }}>
                            <button
                              onClick={() => handleEdit(t)}
                              style={{ background: 'none', border: 'none', color: '#89b4fa', cursor: 'pointer', fontSize: 13 }}
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => deleteMutation.mutate(t.id)}
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

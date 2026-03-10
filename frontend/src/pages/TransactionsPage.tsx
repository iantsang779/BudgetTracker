import { useState } from 'react'
import {
  useTransactions,
  useCreateTransaction,
  useDeleteTransaction,
} from '../hooks/useTransactions'
import type { TransactionCreate, TransactionFilters } from '../types'

const today = new Date().toISOString().slice(0, 10)

const defaultForm: TransactionCreate = {
  account_id: 1,
  category_id: null,
  amount_local: 0,
  currency_code: 'USD',
  amount_base: 0,
  description: '',
  merchant: '',
  transaction_date: today,
  source: 'manual',
}

const inputStyle: React.CSSProperties = {
  background: '#313244',
  border: '1px solid #45475a',
  borderRadius: 6,
  padding: '6px 10px',
  color: '#cdd6f4',
  fontSize: 13,
}

export default function TransactionsPage() {
  const [filters, setFilters] = useState<TransactionFilters>({})
  const [form, setForm] = useState<TransactionCreate>(defaultForm)
  const [showForm, setShowForm] = useState(false)

  const { data: transactions, isLoading } = useTransactions(filters)
  const createMutation = useCreateTransaction()
  const deleteMutation = useDeleteTransaction()

  function handleFilterChange(key: keyof TransactionFilters, value: string) {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    createMutation.mutate(form, {
      onSuccess: () => {
        setForm(defaultForm)
        setShowForm(false)
      },
    })
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Transactions</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
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
        <input
          style={inputStyle}
          placeholder="Currency (e.g. USD)"
          value={filters.currency_code ?? ''}
          onChange={(e) => handleFilterChange('currency_code', e.target.value)}
        />
      </div>

      {/* Form */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          style={{ display: 'flex', flexWrap: 'wrap', gap: 10, background: '#181825', padding: 16, borderRadius: 10, border: '1px solid #313244' }}
        >
          <input style={inputStyle} type="number" placeholder="Account ID" required
            value={form.account_id}
            onChange={(e) => setForm({ ...form, account_id: Number(e.target.value) })} />
          <input style={inputStyle} type="number" step="0.01" placeholder="Amount (local)" required
            value={form.amount_local}
            onChange={(e) => setForm({ ...form, amount_local: Number(e.target.value) })} />
          <input style={inputStyle} placeholder="Currency" required
            value={form.currency_code}
            onChange={(e) => setForm({ ...form, currency_code: e.target.value })} />
          <input style={inputStyle} type="number" step="0.01" placeholder="Amount (USD base)" required
            value={form.amount_base}
            onChange={(e) => setForm({ ...form, amount_base: Number(e.target.value) })} />
          <input style={inputStyle} placeholder="Merchant"
            value={form.merchant ?? ''}
            onChange={(e) => setForm({ ...form, merchant: e.target.value })} />
          <input style={inputStyle} placeholder="Description"
            value={form.description ?? ''}
            onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <input style={inputStyle} type="date" required
            value={form.transaction_date}
            onChange={(e) => setForm({ ...form, transaction_date: e.target.value })} />
          <button type="submit" style={{ ...inputStyle, background: '#a6e3a1', color: '#1e1e2e', fontWeight: 600, cursor: 'pointer', border: 'none' }}>
            Save
          </button>
        </form>
      )}

      {/* Table */}
      {isLoading ? (
        <p style={{ color: '#6c7086' }}>Loading…</p>
      ) : !transactions?.length ? (
        <p style={{ color: '#6c7086' }}>No transactions found.</p>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #313244', textAlign: 'left', color: '#6c7086' }}>
                <th style={{ padding: '8px 12px' }}>Date</th>
                <th style={{ padding: '8px 12px' }}>Merchant</th>
                <th style={{ padding: '8px 12px' }}>Description</th>
                <th style={{ padding: '8px 12px' }}>Amount</th>
                <th style={{ padding: '8px 12px' }}>Currency</th>
                <th style={{ padding: '8px 12px' }}>Category</th>
                <th style={{ padding: '8px 12px' }}></th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((t) => (
                <tr key={t.id} style={{ borderBottom: '1px solid #313244' }}>
                  <td style={{ padding: '8px 12px' }}>{t.transaction_date}</td>
                  <td style={{ padding: '8px 12px' }}>{t.merchant ?? '—'}</td>
                  <td style={{ padding: '8px 12px' }}>{t.description ?? '—'}</td>
                  <td style={{ padding: '8px 12px' }}>{t.amount_local.toLocaleString()}</td>
                  <td style={{ padding: '8px 12px' }}>{t.currency_code}</td>
                  <td style={{ padding: '8px 12px' }}>{t.category_id ?? '—'}</td>
                  <td style={{ padding: '8px 12px' }}>
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
      )}
    </div>
  )
}

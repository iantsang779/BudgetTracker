import { useState } from 'react'
import { useIncomes, useIncomeSummary, useCreateIncome, useDeleteIncome } from '../hooks/useIncome'
import type { IncomeCreate, Recurrence } from '../types'

const today = new Date().toISOString().slice(0, 10)

const defaultForm: IncomeCreate = {
  account_id: 1,
  amount_local: 0,
  currency_code: 'USD',
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

export default function IncomePage() {
  const [form, setForm] = useState<IncomeCreate>(defaultForm)
  const [showForm, setShowForm] = useState(false)

  const { data: incomes, isLoading } = useIncomes()
  const { data: summary } = useIncomeSummary()
  const createMutation = useCreateIncome()
  const deleteMutation = useDeleteIncome()

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
        <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Income</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
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
            <div style={{ fontSize: 22, fontWeight: 700 }}>${summary.monthly_total_base.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          </div>
          <div style={card}>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', color: '#6c7086', marginBottom: 6 }}>Yearly Total</div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>${summary.yearly_total_base.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
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
          <select style={inputStyle}
            value={form.recurrence}
            onChange={(e) => setForm({ ...form, recurrence: e.target.value as Recurrence })}>
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
            <option value="one_off">One-off</option>
          </select>
          <input style={inputStyle} placeholder="Description"
            value={form.description ?? ''}
            onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <label style={{ fontSize: 11, color: '#6c7086' }}>Effective Date</label>
            <input style={inputStyle} type="date" required
              value={form.effective_date}
              onChange={(e) => setForm({ ...form, effective_date: e.target.value })} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <label style={{ fontSize: 11, color: '#6c7086' }}>End Date (optional)</label>
            <input style={inputStyle} type="date"
              value={form.end_date ?? ''}
              onChange={(e) => setForm({ ...form, end_date: e.target.value || null })} />
          </div>
          <button type="submit" style={{ ...inputStyle, background: '#a6e3a1', color: '#1e1e2e', fontWeight: 600, cursor: 'pointer', border: 'none' }}>
            Save
          </button>
        </form>
      )}

      {/* Table */}
      {isLoading ? (
        <p style={{ color: '#6c7086' }}>Loading…</p>
      ) : !incomes?.length ? (
        <p style={{ color: '#6c7086' }}>No income entries found.</p>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #313244', textAlign: 'left', color: '#6c7086' }}>
                <th style={{ padding: '8px 12px' }}>Description</th>
                <th style={{ padding: '8px 12px' }}>Amount</th>
                <th style={{ padding: '8px 12px' }}>Currency</th>
                <th style={{ padding: '8px 12px' }}>Recurrence</th>
                <th style={{ padding: '8px 12px' }}>Effective Date</th>
                <th style={{ padding: '8px 12px' }}>End Date</th>
                <th style={{ padding: '8px 12px' }}></th>
              </tr>
            </thead>
            <tbody>
              {incomes.map((inc) => (
                <tr key={inc.id} style={{ borderBottom: '1px solid #313244' }}>
                  <td style={{ padding: '8px 12px' }}>{inc.description ?? '—'}</td>
                  <td style={{ padding: '8px 12px' }}>{inc.amount_local.toLocaleString()}</td>
                  <td style={{ padding: '8px 12px' }}>{inc.currency_code}</td>
                  <td style={{ padding: '8px 12px' }}>{inc.recurrence}</td>
                  <td style={{ padding: '8px 12px' }}>{inc.effective_date}</td>
                  <td style={{ padding: '8px 12px' }}>{inc.end_date ?? '—'}</td>
                  <td style={{ padding: '8px 12px' }}>
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
      )}
    </div>
  )
}

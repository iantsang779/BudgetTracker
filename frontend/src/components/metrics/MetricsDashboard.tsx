import type { MetricsResponse } from '../../types'
import { fmtCurrency } from '../../hooks/useCurrency'

interface Props {
  metrics: MetricsResponse
  rate: number
  currency: string
}

const card: React.CSSProperties = {
  background: '#181825',
  border: '1px solid #313244',
  borderRadius: 10,
  padding: '16px 20px',
  minWidth: 160,
}

const cardLabel: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 600,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
  color: '#6c7086',
  marginBottom: 6,
}

const cardValue: React.CSSProperties = {
  fontSize: 22,
  fontWeight: 700,
  color: '#cdd6f4',
}

function pct(n: number): string {
  return `${(n * 100).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`
}

export default function MetricsDashboard({ metrics, rate, currency }: Props) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
      <div style={card}>
        <div style={cardLabel}>Total Spending</div>
        <div style={cardValue}>{fmtCurrency(metrics.total_spending_base * rate, currency)}</div>
      </div>
      <div style={card}>
        <div style={cardLabel}>Savings Rate</div>
        <div style={{ ...cardValue, color: metrics.savings_rate >= 0 ? '#a6e3a1' : '#f38ba8' }}>
          {pct(metrics.savings_rate)}
        </div>
      </div>
      <div style={card}>
        <div style={cardLabel}>Monthly Income</div>
        <div style={cardValue}>{fmtCurrency(metrics.monthly_income_base * rate, currency)}</div>
      </div>
    </div>
  )
}

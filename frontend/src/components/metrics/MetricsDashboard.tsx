import type { MetricsResponse } from '../../types'

interface Props {
  metrics: MetricsResponse
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

function fmt(n: number, decimals = 2): string {
  return n.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

function pct(n: number): string {
  return `${fmt(n * 100, 1)}%`
}

export default function MetricsDashboard({ metrics }: Props) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
      <div style={card}>
        <div style={cardLabel}>Total Spending</div>
        <div style={cardValue}>${fmt(metrics.total_spending_base)}</div>
      </div>
      <div style={card}>
        <div style={cardLabel}>Predicted Monthly</div>
        <div style={cardValue}>${fmt(metrics.predicted_monthly_base)}</div>
      </div>
      <div style={card}>
        <div style={cardLabel}>Savings Rate</div>
        <div style={{ ...cardValue, color: metrics.savings_rate >= 0 ? '#a6e3a1' : '#f38ba8' }}>
          {pct(metrics.savings_rate)}
        </div>
      </div>
      <div style={card}>
        <div style={cardLabel}>Inflation-Adjusted</div>
        <div style={cardValue}>${fmt(metrics.inflation_adjusted_spending)}</div>
      </div>
      <div style={card}>
        <div style={cardLabel}>Monthly Income</div>
        <div style={cardValue}>${fmt(metrics.monthly_income_base)}</div>
      </div>
      <div style={card}>
        <div style={cardLabel}>Regression Slope</div>
        <div style={cardValue}>{fmt(metrics.regression_slope)}</div>
      </div>
      <div style={card}>
        <div style={cardLabel}>R²</div>
        <div style={cardValue}>{fmt(metrics.regression_r2, 3)}</div>
      </div>
    </div>
  )
}

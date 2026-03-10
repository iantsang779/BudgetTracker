import { useQueryClient } from '@tanstack/react-query'
import { useWebSocket } from '../hooks/useWebSocket'
import { useMetrics } from '../hooks/useAnalytics'
import { useIncomeSummary } from '../hooks/useIncome'

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

export default function DashboardPage() {
  const queryClient = useQueryClient()
  useWebSocket(queryClient)

  const { data: metrics, isLoading: metricsLoading } = useMetrics()
  const { data: summary, isLoading: summaryLoading } = useIncomeSummary()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: '#cdd6f4' }}>Dashboard</h1>

      {/* KPI cards */}
      <section>
        <h2 style={{ fontSize: 13, fontWeight: 600, color: '#6c7086', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Key Metrics
        </h2>
        {metricsLoading ? (
          <p style={{ color: '#6c7086' }}>Loading metrics…</p>
        ) : metrics ? (
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
        ) : (
          <p style={{ color: '#6c7086' }}>No metrics available.</p>
        )}
      </section>

      {/* Income summary */}
      <section>
        <h2 style={{ fontSize: 13, fontWeight: 600, color: '#6c7086', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Income Summary
        </h2>
        {summaryLoading ? (
          <p style={{ color: '#6c7086' }}>Loading income…</p>
        ) : summary ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
            <div style={card}>
              <div style={cardLabel}>Monthly Total</div>
              <div style={cardValue}>${fmt(summary.monthly_total_base)}</div>
            </div>
            <div style={card}>
              <div style={cardLabel}>Yearly Total</div>
              <div style={cardValue}>${fmt(summary.yearly_total_base)}</div>
            </div>
            <div style={card}>
              <div style={cardLabel}>Active Sources</div>
              <div style={cardValue}>{summary.active_sources}</div>
            </div>
          </div>
        ) : (
          <p style={{ color: '#6c7086' }}>No income data.</p>
        )}
      </section>

      {/* Charts placeholder */}
      <section>
        <h2 style={{ fontSize: 13, fontWeight: 600, color: '#6c7086', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Charts
        </h2>
        <div style={{ background: '#181825', border: '1px dashed #45475a', borderRadius: 10, padding: 40, textAlign: 'center', color: '#6c7086' }}>
          Charts coming in Phase 5 (Plotly.js)
        </div>
      </section>
    </div>
  )
}

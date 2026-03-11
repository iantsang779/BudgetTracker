import { useQueryClient } from '@tanstack/react-query'
import { useWebSocket } from '../hooks/useWebSocket'
import { useMetrics, useCumulativeSpending, useSpendingByCategory, useSpendingOverTime } from '../hooks/useAnalytics'
import { useIncomeSummary } from '../hooks/useIncome'
import MetricsDashboard from '../components/metrics/MetricsDashboard'
import CumulativeSpendingChart from '../components/charts/CumulativeSpendingChart'
import SpendingByCategoryChart from '../components/charts/SpendingByCategoryChart'
import SpendingTrendChart from '../components/charts/SpendingTrendChart'

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

const sectionHeading: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 600,
  color: '#6c7086',
  marginBottom: 12,
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
}

const emptyState: React.CSSProperties = {
  background: '#181825',
  border: '1px dashed #45475a',
  borderRadius: 10,
  padding: 40,
  textAlign: 'center',
  color: '#6c7086',
}

export default function DashboardPage() {
  const queryClient = useQueryClient()
  useWebSocket(queryClient)

  const { data: metrics, isLoading: metricsLoading } = useMetrics()
  const { data: summary, isLoading: summaryLoading } = useIncomeSummary()
  const { data: cumulative, isLoading: cumulativeLoading } = useCumulativeSpending()
  const { data: byCategory, isLoading: byCategoryLoading } = useSpendingByCategory()
  const { data: overTime, isLoading: overTimeLoading } = useSpendingOverTime()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: '#cdd6f4' }}>Dashboard</h1>

      {/* KPI cards */}
      <section>
        <h2 style={sectionHeading}>Key Metrics</h2>
        {metricsLoading ? (
          <p style={{ color: '#6c7086' }}>Loading metrics…</p>
        ) : metrics ? (
          <MetricsDashboard metrics={metrics} />
        ) : (
          <p style={{ color: '#6c7086' }}>No metrics available.</p>
        )}
      </section>

      {/* Income summary */}
      <section>
        <h2 style={sectionHeading}>Income Summary</h2>
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

      {/* Cumulative Spending Chart */}
      <section>
        <h2 style={sectionHeading}>Cumulative Spending</h2>
        {cumulativeLoading ? (
          <p style={{ color: '#6c7086' }}>Loading…</p>
        ) : cumulative && cumulative.points.length > 0 ? (
          <CumulativeSpendingChart data={cumulative} />
        ) : (
          <div style={emptyState}>No spending data yet — add transactions to see cumulative totals.</div>
        )}
      </section>

      {/* Spending by Category Chart */}
      <section>
        <h2 style={sectionHeading}>Spending by Category</h2>
        {byCategoryLoading ? (
          <p style={{ color: '#6c7086' }}>Loading…</p>
        ) : byCategory && byCategory.items.length > 0 ? (
          <SpendingByCategoryChart data={byCategory} />
        ) : (
          <div style={emptyState}>No category data yet — add transactions to see the breakdown.</div>
        )}
      </section>

      {/* Spending Over Time Chart */}
      <section>
        <h2 style={sectionHeading}>Spending Over Time</h2>
        {overTimeLoading ? (
          <p style={{ color: '#6c7086' }}>Loading…</p>
        ) : overTime && overTime.points.length > 0 ? (
          <SpendingTrendChart data={overTime} />
        ) : (
          <div style={emptyState}>No historical data yet — add transactions to see monthly trends.</div>
        )}
      </section>
    </div>
  )
}

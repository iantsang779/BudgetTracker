import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useWebSocket } from '../hooks/useWebSocket'
import { useMetrics, useSavingsProjection, useSpendingByCategory, useSpendingOverTime } from '../hooks/useAnalytics'
import { useIncomeSummary } from '../hooks/useIncome'
import MetricsDashboard from '../components/metrics/MetricsDashboard'
import SavingsProjectionChart from '../components/charts/SavingsProjectionChart'
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

  const [months, setMonths] = useState(6)

  const { data: metrics, isLoading: metricsLoading } = useMetrics()
  const { data: summary, isLoading: summaryLoading } = useIncomeSummary()
  const { data: projection, isLoading: projectionLoading } = useSavingsProjection(months)
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

      {/* Savings Projection Chart */}
      <section>
        <h2 style={sectionHeading}>Savings Projection</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
          <label style={{ color: '#6c7086', fontSize: 12 }}>Months ahead: {months}</label>
          <input
            type="range"
            min={1}
            max={24}
            value={months}
            onChange={e => setMonths(Number(e.target.value))}
            style={{ accentColor: '#cba6f7', width: 160 }}
          />
        </div>
        {projectionLoading ? (
          <p style={{ color: '#6c7086' }}>Loading projection…</p>
        ) : projection && projection.points.length > 0 ? (
          <SavingsProjectionChart data={projection} />
        ) : (
          <div style={emptyState}>No projection data yet — add transactions to generate forecasts.</div>
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

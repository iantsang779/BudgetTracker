import { useState, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useWebSocket } from '../hooks/useWebSocket'
import { useMetrics, useCumulativeSpending, useSpendingByCategory, useSpendingOverTime } from '../hooks/useAnalytics'
import { useIncomeSummary } from '../hooks/useIncome'
import { useCurrencyRate, fmtCurrency } from '../hooks/useCurrency'
import useAppStore from '../store/useAppStore'
import MetricsDashboard from '../components/metrics/MetricsDashboard'
import CumulativeSpendingChart from '../components/charts/CumulativeSpendingChart'
import SpendingByCategoryChart from '../components/charts/SpendingByCategoryChart'
import SavingsChart from '../components/charts/SavingsChart'
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

function currentYearMonth(): string {
  return new Date().toISOString().slice(0, 7)
}

export default function DashboardPage() {
  const queryClient = useQueryClient()
  useWebSocket(queryClient)

  const displayCurrency = useAppStore((s) => s.displayCurrency)
  const { data: rateData } = useCurrencyRate(displayCurrency)
  const rate = displayCurrency === 'USD' ? 1 : (rateData?.rate ?? 1)

  const { data: metrics, isLoading: metricsLoading } = useMetrics()
  const { data: summary, isLoading: summaryLoading } = useIncomeSummary()
  const { data: cumulative, isLoading: cumulativeLoading } = useCumulativeSpending()
  const { data: overTime, isLoading: overTimeLoading } = useSpendingOverTime()

  // Derive available months from spending-over-time, default to current month
  const availableMonths = useMemo(() => {
    const fromData = overTime?.points.map(p => p.period) ?? []
    const cur = currentYearMonth()
    return fromData.includes(cur) ? fromData : [...fromData, cur]
  }, [overTime])

  const [selectedMonth, setSelectedMonth] = useState<string>(() => currentYearMonth())

  const monthStart = `${selectedMonth}-01`
  const monthEnd = useMemo(() => {
    const [y, m] = selectedMonth.split('-').map(Number)
    const last = new Date(y, m, 0).getDate()
    return `${selectedMonth}-${String(last).padStart(2, '0')}`
  }, [selectedMonth])

  const { data: byCategory, isLoading: byCategoryLoading } = useSpendingByCategory(monthStart, monthEnd)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: '#cdd6f4' }}>Dashboard</h1>

      {/* KPI cards */}
      <section>
        <h2 style={sectionHeading}>Key Metrics</h2>
        {metricsLoading ? (
          <p style={{ color: '#6c7086' }}>Loading metrics…</p>
        ) : metrics ? (
          <MetricsDashboard metrics={metrics} rate={rate} currency={displayCurrency} />
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
              <div style={cardValue}>{fmtCurrency(summary.monthly_total_base * rate, displayCurrency)}</div>
            </div>
            <div style={card}>
              <div style={cardLabel}>Yearly Total</div>
              <div style={cardValue}>{fmtCurrency(summary.yearly_total_base * rate, displayCurrency)}</div>
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
          <CumulativeSpendingChart data={cumulative} rate={rate} currency={displayCurrency} />
        ) : (
          <div style={emptyState}>No spending data yet — add transactions to see cumulative totals.</div>
        )}
      </section>

      {/* Spending by Category + Savings side by side */}
      <section>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <h2 style={{ ...sectionHeading, marginBottom: 0 }}>Monthly Breakdown</h2>
          <select
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            style={{
              background: '#313244',
              border: '1px solid #45475a',
              borderRadius: 6,
              padding: '4px 10px',
              color: '#cdd6f4',
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            {availableMonths.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <div>
            <h2 style={sectionHeading}>Spending by Category</h2>
            {byCategoryLoading ? (
              <p style={{ color: '#6c7086' }}>Loading…</p>
            ) : byCategory && byCategory.items.length > 0 ? (
              <SpendingByCategoryChart data={byCategory} rate={rate} currency={displayCurrency} />
            ) : (
              <div style={emptyState}>No spending for {selectedMonth}.</div>
            )}
          </div>
          <div>
            <h2 style={sectionHeading}>Savings Breakdown</h2>
            {metricsLoading ? (
              <p style={{ color: '#6c7086' }}>Loading…</p>
            ) : metrics ? (
              <SavingsChart
                spending={byCategory?.total_base ?? 0}
                income={metrics.monthly_income_base}
                rate={rate}
                currency={displayCurrency}
              />
            ) : (
              <div style={emptyState}>No data yet — add income and transactions to see savings.</div>
            )}
          </div>
        </div>
      </section>

      {/* Spending Over Time Chart */}
      <section>
        <h2 style={sectionHeading}>Spending Over Time</h2>
        {overTimeLoading ? (
          <p style={{ color: '#6c7086' }}>Loading…</p>
        ) : overTime && overTime.points.length > 0 ? (
          <SpendingTrendChart data={overTime} rate={rate} currency={displayCurrency} />
        ) : (
          <div style={emptyState}>No historical data yet — add transactions to see monthly trends.</div>
        )}
      </section>
    </div>
  )
}

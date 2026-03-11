import Plot from 'react-plotly.js'
import type { Layout } from 'plotly.js'
import type { MetricsResponse } from '../../types'

interface Props {
  metrics: MetricsResponse
}

const darkLayout: Partial<Layout> = {
  paper_bgcolor: '#181825',
  plot_bgcolor: '#181825',
  font: { color: '#cdd6f4', family: '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif' },
  margin: { t: 30, r: 20, b: 20, l: 20 },
  legend: { bgcolor: 'transparent' },
}

export default function SavingsChart({ metrics }: Props) {
  const spending = Math.max(0, metrics.total_spending_base)
  const income = Math.max(0, metrics.monthly_income_base)
  const savings = Math.max(0, income - spending)

  const labels = ['Spending', 'Savings']
  const values = [spending, savings]
  const colors = ['#f38ba8', '#a6e3a1']

  const centre = income > 0
    ? `$${income.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
    : '$0'

  const traces: Plotly.Data[] = [
    {
      type: 'pie',
      labels,
      values,
      hole: 0.4,
      marker: { colors },
      textinfo: 'label+percent',
      hovertemplate: '%{label}: $%{value:.2f} (%{percent})<extra></extra>',
    },
  ]

  const layout: Partial<Layout> = {
    ...darkLayout,
    annotations: [
      {
        text: centre,
        x: 0.5,
        y: 0.5,
        xanchor: 'center',
        yanchor: 'middle',
        showarrow: false,
        font: { size: 16, color: '#cdd6f4' },
      },
    ],
  }

  return (
    <Plot
      data={traces}
      layout={layout}
      style={{ width: '100%', height: 320 }}
      useResizeHandler
      config={{ displayModeBar: false }}
    />
  )
}

import Plot from 'react-plotly.js'
import type { Layout } from 'plotly.js'

interface Props {
  spending: number
  income: number
  rate: number
  currency: string
}

const darkLayout: Partial<Layout> = {
  paper_bgcolor: '#181825',
  plot_bgcolor: '#181825',
  font: { color: '#cdd6f4', family: '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif' },
  margin: { t: 30, r: 20, b: 20, l: 20 },
  legend: { bgcolor: 'transparent' },
}

export default function SavingsChart({ spending, income, rate, currency }: Props) {
  const spendingVal = Math.max(0, spending * rate)
  const incomeVal = Math.max(0, income * rate)
  const savings = Math.max(0, incomeVal - spendingVal)

  const centre = incomeVal > 0
    ? `${currency} ${incomeVal.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
    : `${currency} 0`

  const traces: Plotly.Data[] = [
    {
      type: 'pie',
      labels: ['Spending', 'Savings'],
      values: [spendingVal, savings],
      hole: 0.4,
      marker: { colors: ['#f38ba8', '#a6e3a1'] },
      textinfo: 'label+percent',
      hovertemplate: `%{label}: ${currency} %{value:,.2f} (%{percent})<extra></extra>`,
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
        font: { size: 14, color: '#cdd6f4' },
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

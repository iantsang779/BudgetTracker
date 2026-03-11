import Plot from 'react-plotly.js'
import type { Layout } from 'plotly.js'
import type { SpendingByCategoryResponse } from '../../types'

interface Props {
  data: SpendingByCategoryResponse
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

export default function SpendingByCategoryChart({ data, rate, currency }: Props) {
  const total = data.total_base * rate

  const traces: Plotly.Data[] = [
    {
      type: 'pie',
      labels: data.items.map(i => i.category_name),
      values: data.items.map(i => i.total_base * rate),
      hole: 0.4,
      marker: { colors: data.items.map(i => i.color_hex) },
      textinfo: 'label+percent',
      hovertemplate: `%{label}: ${currency} %{value:,.2f} (%{percent})<extra></extra>`,
    },
  ]

  const layout: Partial<Layout> = {
    ...darkLayout,
    annotations: [
      {
        text: `${currency} ${total.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
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

import Plot from 'react-plotly.js'
import type { Layout } from 'plotly.js'
import type { SpendingOverTimeResponse } from '../../types'

interface Props {
  data: SpendingOverTimeResponse
}

const darkLayout: Partial<Layout> = {
  paper_bgcolor: '#181825',
  plot_bgcolor: '#181825',
  font: { color: '#cdd6f4', family: '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif' },
  margin: { t: 30, r: 20, b: 50, l: 60 },
  xaxis: { gridcolor: '#313244', zerolinecolor: '#45475a' },
  yaxis: { gridcolor: '#313244', zerolinecolor: '#45475a' },
  legend: { bgcolor: 'transparent' },
}

export default function SpendingTrendChart({ data }: Props) {
  const traces: Plotly.Data[] = [
    {
      type: 'bar',
      x: data.points.map(p => p.period),
      y: data.points.map(p => p.total_base),
      marker: { color: '#cba6f7' },
      hovertemplate: '%{x}: $%{y:.2f}<extra></extra>',
    },
  ]

  return (
    <Plot
      data={traces}
      layout={darkLayout}
      style={{ width: '100%', height: 320 }}
      useResizeHandler
      config={{ displayModeBar: false }}
    />
  )
}

import Plot from 'react-plotly.js'
import type { Layout } from 'plotly.js'
import type { SavingsProjectionResponse } from '../../types'

interface Props {
  data: SavingsProjectionResponse
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

export default function SavingsProjectionChart({ data }: Props) {
  const periods = data.points.map(p => p.period)
  const actuals = data.points.map(p => p.actual)
  const predicted = data.points.map(p => p.predicted)
  const upper = data.points.map(p => p.upper_band)
  const lower = data.points.map(p => p.lower_band)

  const actualX = periods.filter((_, i) => actuals[i] !== null)
  const actualY = actuals.filter((v): v is number => v !== null)

  const traces: Plotly.Data[] = [
    {
      name: 'Upper band',
      x: periods,
      y: upper,
      mode: 'lines',
      line: { width: 0, color: 'transparent' },
      showlegend: false,
    },
    {
      name: 'Lower band',
      x: periods,
      y: lower,
      mode: 'lines',
      fill: 'tonexty',
      fillcolor: 'rgba(203,166,247,0.15)',
      line: { width: 0, color: 'transparent' },
      showlegend: false,
    },
    {
      name: 'Predicted',
      x: periods,
      y: predicted,
      mode: 'lines',
      line: { color: '#cba6f7', dash: 'dash', width: 2 },
    },
    {
      name: 'Actual',
      x: actualX,
      y: actualY,
      mode: 'lines+markers',
      line: { color: '#89b4fa', width: 2 },
      marker: { color: '#89b4fa', size: 6 },
    },
  ]

  const layout: Partial<Layout> = {
    ...darkLayout,
    annotations: [
      {
        xref: 'paper',
        yref: 'paper',
        x: 1,
        y: 1.05,
        xanchor: 'right',
        yanchor: 'bottom',
        text: `slope: ${data.slope.toFixed(2)} · R²: ${data.r2_score.toFixed(3)}`,
        showarrow: false,
        font: { size: 11, color: '#6c7086' },
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

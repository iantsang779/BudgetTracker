import Plot from 'react-plotly.js'
import type { CumulativeSavingsResponse } from '../../types'

interface Props {
  data: CumulativeSavingsResponse
  rate: number
  currency: string
}

export default function CumulativeSavingsChart({ data, rate, currency }: Props) {
  const periods = data.points.map((p) => p.period)
  const cumulative = data.points.map((p) => p.cumulative_saving * rate)

  const lineColor = cumulative[cumulative.length - 1] >= 0 ? '#a6e3a1' : '#f38ba8'
  const fillColor = cumulative[cumulative.length - 1] >= 0
    ? 'rgba(166,227,161,0.12)'
    : 'rgba(243,139,168,0.12)'

  return (
    <Plot
      data={[
        {
          x: periods,
          y: cumulative,
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Cumulative Savings',
          line: { color: lineColor, width: 2 },
          marker: { color: lineColor, size: 6 },
          fill: 'tozeroy',
          fillcolor: fillColor,
          hovertemplate: `%{x}<br>Cumulative: ${currency} %{y:,.2f}<extra></extra>`,
        },
      ]}
      layout={{
        title: { text: `Cumulative Savings — ${data.year}`, font: { color: '#cdd6f4', size: 14 } },
        paper_bgcolor: '#181825',
        plot_bgcolor: '#181825',
        font: { color: '#cdd6f4' },
        xaxis: { gridcolor: '#313244', tickfont: { color: '#6c7086' } },
        yaxis: {
          gridcolor: '#313244',
          tickfont: { color: '#6c7086' },
          tickprefix: `${currency} `,
          zeroline: true,
          zerolinecolor: '#45475a',
        },
        margin: { t: 40, r: 20, b: 40, l: 60 },
        showlegend: false,
      }}
      style={{ width: '100%', height: 320 }}
      config={{ displayModeBar: false, responsive: true }}
    />
  )
}

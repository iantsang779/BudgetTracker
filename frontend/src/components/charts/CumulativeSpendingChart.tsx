import Plot from 'react-plotly.js'
import type { CumulativeSpendingResponse } from '../../types'

interface Props {
  data: CumulativeSpendingResponse
  rate: number
  currency: string
}

export default function CumulativeSpendingChart({ data, rate, currency }: Props) {
  const periods = data.points.map((p) => p.period)
  const cumulative = data.points.map((p) => p.cumulative_total * rate)
  const monthly = data.points.map((p) => p.monthly_total * rate)

  return (
    <Plot
      data={[
        {
          x: periods,
          y: cumulative,
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Cumulative',
          line: { color: '#cba6f7', width: 2 },
          marker: { color: '#cba6f7', size: 6 },
          fill: 'tozeroy',
          fillcolor: 'rgba(203,166,247,0.12)',
          customdata: monthly,
          hovertemplate: `%{x}<br>Cumulative: ${currency} %{y:,.2f}<br>Monthly: ${currency} %{customdata:,.2f}<extra></extra>`,
        },
      ]}
      layout={{
        title: { text: `Cumulative Spending — ${data.year}`, font: { color: '#cdd6f4', size: 14 } },
        paper_bgcolor: '#181825',
        plot_bgcolor: '#181825',
        font: { color: '#cdd6f4' },
        xaxis: { gridcolor: '#313244', tickfont: { color: '#6c7086' } },
        yaxis: {
          gridcolor: '#313244',
          tickfont: { color: '#6c7086' },
          tickprefix: `${currency} `,
        },
        margin: { t: 40, r: 20, b: 40, l: 60 },
        showlegend: false,
      }}
      style={{ width: '100%', height: 320 }}
      config={{ displayModeBar: false, responsive: true }}
    />
  )
}

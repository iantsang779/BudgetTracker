import Plot from 'react-plotly.js'
import type { CumulativeSavingsResponse } from '../../types'

interface Props {
  data: CumulativeSavingsResponse
  rate: number
  currency: string
}

export default function MonthlySavingsChart({ data, rate, currency }: Props) {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const labels = data.points.map((p) => months[parseInt(p.period.split('-')[1], 10) - 1])
  const savings = data.points.map((p) => p.monthly_saving * rate)
  const colors = savings.map((v) => (v >= 0 ? '#a6e3a1' : '#f38ba8'))

  return (
    <Plot
      data={[
        {
          x: labels,
          y: savings,
          type: 'bar',
          name: 'Monthly Savings',
          marker: { color: colors },
          hovertemplate: `%{x}<br>${currency} %{y:,.2f}<extra></extra>`,
        },
      ]}
      layout={{
        title: { text: `Monthly Savings — ${data.year}`, font: { color: '#cdd6f4', size: 14 } },
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

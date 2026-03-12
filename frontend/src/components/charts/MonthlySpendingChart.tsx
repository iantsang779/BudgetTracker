import Plot from 'react-plotly.js'
import type { CumulativeSpendingResponse } from '../../types'

interface Props {
  data: CumulativeSpendingResponse
  rate: number
  currency: string
}

export default function MonthlySpendingChart({ data, rate, currency }: Props) {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const labels = data.points.map((p) => months[parseInt(p.period.split('-')[1], 10) - 1])
  const monthly = data.points.map((p) => p.monthly_total * rate)

  return (
    <Plot
      data={[
        {
          x: labels,
          y: monthly,
          type: 'bar',
          name: 'Monthly Spending',
          marker: { color: '#89b4fa' },
          hovertemplate: `%{x}<br>${currency} %{y:,.2f}<extra></extra>`,
        },
      ]}
      layout={{
        title: { text: `Monthly Spending — ${data.year}`, font: { color: '#cdd6f4', size: 14 } },
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

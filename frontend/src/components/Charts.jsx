import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts'
import { CHART_COLORS, THEME } from '../theme'

function ChartCard({ title, children }) {
  return (
    <div className="chart-card">
      <h3>{title}</h3>
      <div style={{ width: '100%', height: 280 }}>
        <ResponsiveContainer>{children}</ResponsiveContainer>
      </div>
    </div>
  )
}

export default function Charts({ charts = [] }) {
  if (!charts.length) return null
  return (
    <div className="charts">
      {charts.map((c, idx) => {
        if (c.type === 'pie') {
          return (
            <ChartCard key={idx} title={c.title}>
              <PieChart>
                <Pie data={c.data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                  {c.data.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ChartCard>
          )
        }
        if (c.type === 'bar') {
          return (
            <ChartCard key={idx} title={c.title}>
              <BarChart data={c.data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                <XAxis dataKey={c.xKey} tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey={c.yKey} fill={THEME.darkGreen} />
              </BarChart>
            </ChartCard>
          )
        }
        if (c.type === 'line') {
          return (
            <ChartCard key={idx} title={c.title}>
              <LineChart data={c.data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                <XAxis dataKey={c.xKey} tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey={c.yKey} stroke={THEME.bronze} strokeWidth={2} dot={false} />
              </LineChart>
            </ChartCard>
          )
        }
        return null
      })}
    </div>
  )
}

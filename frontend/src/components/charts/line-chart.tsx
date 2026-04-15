import { ResponsiveContainer, LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'

interface LineConfig {
  dataKey?: string
  key?: string
  color: string
  name?: string
  label?: string
}

interface LineChartProps {
  data: Array<Record<string, unknown>>
  lines: LineConfig[]
  xAxisKey: string
  height?: number
}

export function LineChart({ data, lines, xAxisKey, height = 300 }: LineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsLineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis dataKey={xAxisKey} className="text-xs" />
        <YAxis className="text-xs" />
        <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid hsl(var(--border))' }} />
        <Legend />
        {lines.map((line) => {
          const dk = line.dataKey || line.key || ''
          return (
            <Line
              key={dk}
              type="monotone"
              dataKey={dk}
              stroke={line.color}
              name={line.name || line.label || dk}
              strokeWidth={2}
              dot={false}
            />
          )
        })}
      </RechartsLineChart>
    </ResponsiveContainer>
  )
}

export default LineChart

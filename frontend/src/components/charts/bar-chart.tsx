import { ResponsiveContainer, BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'

interface BarConfig {
  dataKey?: string
  key?: string
  color: string
  name?: string
  label?: string
}

interface BarChartProps {
  data: Array<Record<string, unknown>>
  bars: BarConfig[]
  xAxisKey: string
  height?: number
  stacked?: boolean
}

export function BarChart({ data, bars, xAxisKey, height = 300, stacked }: BarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis dataKey={xAxisKey} className="text-xs" />
        <YAxis className="text-xs" />
        <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid hsl(var(--border))' }} />
        <Legend />
        {bars.map((bar) => {
          const dk = bar.dataKey || bar.key || ''
          return (
            <Bar
              key={dk}
              dataKey={dk}
              fill={bar.color}
              name={bar.name || bar.label || dk}
              stackId={stacked ? 'stack' : undefined}
              radius={[4, 4, 0, 0]}
            />
          )
        })}
      </RechartsBarChart>
    </ResponsiveContainer>
  )
}

export default BarChart

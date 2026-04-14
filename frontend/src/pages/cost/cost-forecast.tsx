import PageHeader from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import MetricCard from '@/components/charts/metric-card'
import { LineChart } from '@/components/charts/line-chart'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useCostForecast } from '@/hooks/use-cost'
import { formatCurrency } from '@/lib/utils'
import { TrendingUp, DollarSign, Calendar, AlertTriangle } from 'lucide-react'

export default function CostForecast() {
  const { data: forecast, isLoading } = useCostForecast()

  if (isLoading) return <LoadingSkeleton />

  return (
    <div className="space-y-6">
      <PageHeader title="Cost Forecast" description="Projected spending based on usage trends" />

      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          title="Current Month Actual"
          value={formatCurrency(forecast?.current_month_actual ?? 0)}
          icon={<DollarSign className="h-4 w-4" />}
        />
        <MetricCard
          title="Projected Month-End"
          value={formatCurrency(forecast?.projected_month_end ?? 0)}
          trend={forecast?.projection_trend}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <MetricCard
          title="Next Month Estimate"
          value={formatCurrency(forecast?.next_month_estimate ?? 0)}
          icon={<Calendar className="h-4 w-4" />}
        />
        <MetricCard
          title="Budget Remaining"
          value={formatCurrency(forecast?.budget_remaining ?? 0)}
          icon={<AlertTriangle className="h-4 w-4" />}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            Projected Spend
            <Badge variant="info">90-day forecast</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LineChart
            data={forecast?.projection_data ?? []}
            lines={[
              { key: 'actual', label: 'Actual Spend', color: '#3b82f6' },
              { key: 'projected', label: 'Projected', color: '#f59e0b' },
              { key: 'upper_bound', label: 'Upper Bound', color: '#ef444466' },
              { key: 'lower_bound', label: 'Lower Bound', color: '#10b98166' },
            ]}
            xAxisKey="date"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-sm">Forecast by Model</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-3">
            {(forecast?.by_model ?? []).map((m: { model: string; current: number; projected: number }) => (
              <div key={m.model} className="flex items-center justify-between rounded-md border p-3">
                <span className="font-medium text-sm">{m.model}</span>
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-muted-foreground">Current: {formatCurrency(m.current)}</span>
                  <span>Projected: <strong>{formatCurrency(m.projected)}</strong></span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

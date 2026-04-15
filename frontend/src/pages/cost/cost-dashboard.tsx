import PageHeader from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import MetricCard from '@/components/charts/metric-card'
import { LineChart } from '@/components/charts/line-chart'
import { BarChart } from '@/components/charts/bar-chart'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useCostAnalytics } from '@/hooks/use-cost'
import { formatCurrency } from '@/lib/utils'
import { DollarSign, TrendingDown, Zap, BarChart3 } from 'lucide-react'

export default function CostDashboard() {
  const { data: analytics, isLoading } = useCostAnalytics()

  if (isLoading) return <LoadingSkeleton />

  return (
    <div className="space-y-6">
      <PageHeader title="Cost Analytics" description="Monitor and optimize LLM spending" />

      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          title="Total Spend (30d)"
          value={formatCurrency(analytics?.total_spend ?? 0)}
          trend={analytics?.spend_trend}
          icon={<DollarSign className="h-4 w-4" />}
        />
        <MetricCard
          title="Avg Cost/Query"
          value={`$${(analytics?.avg_cost_per_query ?? 0).toFixed(4)}`}
          trend={analytics?.cost_per_query_trend}
          icon={<BarChart3 className="h-4 w-4" />}
        />
        <MetricCard
          title="Cache Savings"
          value={formatCurrency(analytics?.cache_savings ?? 0)}
          icon={<Zap className="h-4 w-4" />}
        />
        <MetricCard
          title="Cache Hit Rate"
          value={`${((analytics?.cache_hit_rate ?? 0) * 100).toFixed(1)}%`}
          icon={<TrendingDown className="h-4 w-4" />}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle className="text-sm">Daily Spend Trend</CardTitle></CardHeader>
          <CardContent>
            <LineChart
              data={analytics?.daily_spend ?? []}
              lines={[{ dataKey: 'spend', name: 'Spend ($)', color: '#3b82f6' }]}
              xAxisKey="date"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Cost by Model</CardTitle></CardHeader>
          <CardContent>
            <BarChart
              data={analytics?.cost_by_model ?? []}
              bars={[{ dataKey: 'cost', name: 'Cost ($)', color: '#8b5cf6' }]}
              xAxisKey="model"
            />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">Cost by Application</CardTitle></CardHeader>
        <CardContent>
          <BarChart
            data={analytics?.cost_by_app ?? []}
            bars={[{ dataKey: 'cost', name: 'Cost ($)', color: '#10b981' }]}
            xAxisKey="app_name"
          />
        </CardContent>
      </Card>
    </div>
  )
}

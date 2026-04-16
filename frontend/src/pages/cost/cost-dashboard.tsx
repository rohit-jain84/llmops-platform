import PageHeader from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import MetricCard from '@/components/charts/metric-card'
import { LineChart } from '@/components/charts/line-chart'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useCostAnalytics } from '@/hooks/use-cost'
import { formatCurrency } from '@/lib/utils'
import { DollarSign, TrendingDown, Zap, BarChart3 } from 'lucide-react'

export default function CostDashboard() {
  const { data: analytics, isLoading } = useCostAnalytics()

  if (isLoading) return <LoadingSkeleton />

  const totalCost = Number(analytics?.total_cost_usd ?? 0)
  const totalRequests = analytics?.total_requests ?? 0
  const avgCost = totalRequests > 0 ? totalCost / totalRequests : 0
  const cacheHitRate = analytics?.cache_hit_rate ?? 0

  const dailySpend = (analytics?.breakdown ?? []).map((b: { period: string; cost: number; requests: number }) => ({
    date: b.period.split(' ')[0],
    spend: b.cost,
    requests: b.requests,
  }))

  return (
    <div className="space-y-6">
      <PageHeader title="Cost Analytics" description="Monitor and optimize LLM spending" />

      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          title="Total Spend (30d)"
          value={formatCurrency(totalCost)}
          icon={<DollarSign className="h-4 w-4" />}
        />
        <MetricCard
          title="Avg Cost/Query"
          value={`$${avgCost.toFixed(4)}`}
          icon={<BarChart3 className="h-4 w-4" />}
        />
        <MetricCard
          title="Total Requests"
          value={totalRequests.toLocaleString()}
          icon={<Zap className="h-4 w-4" />}
        />
        <MetricCard
          title="Cache Hit Rate"
          value={`${(cacheHitRate * 100).toFixed(1)}%`}
          icon={<TrendingDown className="h-4 w-4" />}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle className="text-sm">Daily Spend Trend</CardTitle></CardHeader>
          <CardContent>
            <LineChart
              data={dailySpend}
              lines={[{ dataKey: 'spend', name: 'Spend ($)', color: '#3b82f6' }]}
              xAxisKey="date"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Daily Requests</CardTitle></CardHeader>
          <CardContent>
            <LineChart
              data={dailySpend}
              lines={[{ dataKey: 'requests', name: 'Requests', color: '#8b5cf6' }]}
              xAxisKey="date"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

import PageHeader from '@/components/layout/page-header'
import MetricCard from '@/components/charts/metric-card'
import LineChart from '@/components/charts/line-chart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useCostAnalytics } from '@/hooks/use-cost'
import { useExperiments } from '@/hooks/use-experiments'
import { Activity, DollarSign, Zap, FlaskConical } from 'lucide-react'

export default function Dashboard() {
  const { data: costData } = useCostAnalytics()
  const { data: experiments } = useExperiments()

  const activeExperiments = experiments?.filter(e => e.status === 'running').length ?? 0

  return (
    <div>
      <PageHeader title="Dashboard" description="Overview of your LLMOps platform" />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Requests"
          value={costData?.total_requests?.toLocaleString() ?? '0'}
          icon={<Activity className="h-4 w-4" />}
        />
        <MetricCard
          title="Total Cost"
          value={`$${(costData?.total_cost_usd ?? 0).toFixed(2)}`}
          icon={<DollarSign className="h-4 w-4" />}
        />
        <MetricCard
          title="Cache Hit Rate"
          value={`${((costData?.cache_hit_rate ?? 0) * 100).toFixed(1)}%`}
          icon={<Zap className="h-4 w-4" />}
        />
        <MetricCard
          title="Active Experiments"
          value={activeExperiments}
          icon={<FlaskConical className="h-4 w-4" />}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Request Volume & Cost</CardTitle>
          </CardHeader>
          <CardContent>
            <LineChart
              data={costData?.breakdown ?? []}
              lines={[
                { dataKey: 'requests', color: '#3b82f6', name: 'Requests' },
                { dataKey: 'cost', color: '#ef4444', name: 'Cost ($)' },
              ]}
              xAxisKey="period"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Token Usage</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Input Tokens</span>
                <span className="font-medium">{(costData?.total_input_tokens ?? 0).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Output Tokens</span>
                <span className="font-medium">{(costData?.total_output_tokens ?? 0).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Total Tokens</span>
                <span className="font-bold">
                  {((costData?.total_input_tokens ?? 0) + (costData?.total_output_tokens ?? 0)).toLocaleString()}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

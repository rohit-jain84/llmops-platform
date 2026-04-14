import { useState } from 'react'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import MetricCard from '@/components/charts/metric-card'
import { LineChart } from '@/components/charts/line-chart'
import { BarChart } from '@/components/charts/bar-chart'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useCostAnalytics } from '@/hooks/use-cost'
import { formatNumber } from '@/lib/utils'
import { Hash, TrendingUp, ArrowUpDown } from 'lucide-react'

export default function TokenAnalytics() {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d')
  const { data: analytics, isLoading } = useCostAnalytics({ timeRange })

  if (isLoading) return <LoadingSkeleton />

  return (
    <div className="space-y-6">
      <PageHeader title="Token Analytics" description="Deep-dive into token usage by application, model, and time period" />

      <div className="flex gap-2">
        {(['7d', '30d', '90d'] as const).map((r) => (
          <Button key={r} size="sm" variant={timeRange === r ? 'default' : 'outline'} onClick={() => setTimeRange(r)}>{r}</Button>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-4">
        <MetricCard title="Total Tokens" value={formatNumber(analytics?.total_tokens ?? 0)} icon={<Hash className="h-4 w-4" />} />
        <MetricCard title="Input Tokens" value={formatNumber(analytics?.input_tokens ?? 0)} icon={<TrendingUp className="h-4 w-4" />} />
        <MetricCard title="Output Tokens" value={formatNumber(analytics?.output_tokens ?? 0)} icon={<ArrowUpDown className="h-4 w-4" />} />
      </div>

      <Tabs defaultValue="by-time">
        <TabsList>
          <TabsTrigger value="by-time">By Time</TabsTrigger>
          <TabsTrigger value="by-model">By Model</TabsTrigger>
          <TabsTrigger value="by-app">By Application</TabsTrigger>
        </TabsList>

        <TabsContent value="by-time">
          <Card>
            <CardHeader><CardTitle className="text-sm">Token Usage Over Time</CardTitle></CardHeader>
            <CardContent>
              <LineChart
                data={analytics?.token_usage_over_time ?? []}
                lines={[
                  { key: 'input_tokens', label: 'Input', color: '#3b82f6' },
                  { key: 'output_tokens', label: 'Output', color: '#ef4444' },
                ]}
                xAxisKey="date"
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="by-model">
          <Card>
            <CardHeader><CardTitle className="text-sm">Tokens by Model</CardTitle></CardHeader>
            <CardContent>
              <BarChart
                data={analytics?.tokens_by_model ?? []}
                bars={[
                  { key: 'input_tokens', label: 'Input', color: '#3b82f6' },
                  { key: 'output_tokens', label: 'Output', color: '#ef4444' },
                ]}
                xAxisKey="model"
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="by-app">
          <Card>
            <CardHeader><CardTitle className="text-sm">Tokens by Application</CardTitle></CardHeader>
            <CardContent>
              <BarChart
                data={analytics?.tokens_by_app ?? []}
                bars={[{ key: 'total_tokens', label: 'Total Tokens', color: '#10b981' }]}
                xAxisKey="app_name"
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

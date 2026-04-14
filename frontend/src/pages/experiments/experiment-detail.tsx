import { useParams } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import MetricCard from '@/components/charts/metric-card'
import { BarChart } from '@/components/charts/bar-chart'
import { LineChart } from '@/components/charts/line-chart'
import { StatSignificance } from '@/components/charts/stat-significance'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useExperiment, useExperimentResults, useStartExperiment, useStopExperiment, usePromoteWinner } from '@/hooks/use-experiments'
import { formatNumber } from '@/lib/utils'
import { Play, Square, Trophy, Activity, Calendar, Users } from 'lucide-react'

export default function ExperimentDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: experiment, isLoading } = useExperiment(id!)
  const { data: results } = useExperimentResults(id!)
  const startExperiment = useStartExperiment()
  const stopExperiment = useStopExperiment()
  const promoteWinner = usePromoteWinner()

  if (isLoading) return <LoadingSkeleton />

  const isRunning = experiment?.status === 'running'
  const daysRunning = experiment?.started_at
    ? Math.floor((Date.now() - new Date(experiment.started_at).getTime()) / 86400000)
    : 0

  return (
    <div className="space-y-6">
      <PageHeader
        title={experiment?.name ?? 'Experiment'}
        description={`Status: ${experiment?.status ?? 'unknown'}`}
        actions={
          <div className="flex gap-2">
            {experiment?.status === 'draft' && (
              <Button onClick={() => startExperiment.mutate(id!)}><Play className="mr-2 h-4 w-4" />Start</Button>
            )}
            {isRunning && (
              <Button variant="outline" onClick={() => stopExperiment.mutate(id!)}><Square className="mr-2 h-4 w-4" />Stop</Button>
            )}
            {results?.winner && (
              <Button onClick={() => promoteWinner.mutate({ experimentId: id!, variantId: results.winner!.id })}>
                <Trophy className="mr-2 h-4 w-4" />Promote Winner
              </Button>
            )}
          </div>
        }
      />

      <div className="grid grid-cols-4 gap-4">
        <MetricCard title="Total Requests" value={formatNumber(results?.total_requests ?? 0)} icon={<Users className="h-4 w-4" />} />
        <MetricCard title="Winner" value={results?.winner?.name ?? 'TBD'} icon={<Trophy className="h-4 w-4" />} />
        <MetricCard title="Days Running" value={String(daysRunning)} icon={<Calendar className="h-4 w-4" />} />
        <Card className="flex items-center gap-3 p-4">
          <Activity className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">p-value</p>
            <StatSignificance pValue={results?.p_value ?? 1} />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle className="text-sm">Conversion by Variant</CardTitle></CardHeader>
          <CardContent>
            <BarChart
              data={results?.variants ?? []}
              bars={[{ key: 'conversion_rate', label: 'Conversion %', color: '#3b82f6' }]}
              xAxisKey="name"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Latency by Variant</CardTitle></CardHeader>
          <CardContent>
            <BarChart
              data={results?.variants ?? []}
              bars={[{ key: 'avg_latency_ms', label: 'Avg Latency (ms)', color: '#f59e0b' }]}
              xAxisKey="name"
            />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">Convergence Over Time</CardTitle></CardHeader>
        <CardContent>
          <LineChart
            data={results?.convergence ?? []}
            lines={(results?.variants ?? []).map((v: { name: string }, i: number) => ({
              key: v.name,
              label: v.name,
              color: ['#3b82f6', '#ef4444', '#10b981', '#f59e0b'][i % 4],
            }))}
            xAxisKey="date"
          />
        </CardContent>
      </Card>
    </div>
  )
}

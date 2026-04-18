import { useParams } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/ui/data-table'
import MetricCard from '@/components/charts/metric-card'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useEvalRun, useEvalResults } from '@/hooks/use-evaluations'
import { formatNumber } from '@/lib/utils'
import { CheckCircle, XCircle, BarChart3 } from 'lucide-react'

interface EvalResultRow {
  id: string
  input?: string
  expected?: string
  actual?: string
  score?: number
  metrics?: Record<string, number>
  [key: string]: unknown
}

export default function EvalRunDetail() {
  const { runId } = useParams<{ runId: string }>()
  const { data: run, isLoading } = useEvalRun(runId!)
  const { data: results } = useEvalResults(runId!)

  if (isLoading) return <LoadingSkeleton />

  const metricSummary: Record<string, number> = {}
  results?.forEach((r: EvalResultRow) => {
    Object.entries(r.metrics ?? {}).forEach(([k, v]) => {
      metricSummary[k] = (metricSummary[k] ?? 0) + v
    })
  })
  const count = results?.length ?? 1
  Object.keys(metricSummary).forEach((k) => { metricSummary[k] /= count })

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Eval Run ${runId?.slice(0, 8)}`}
        description={`Status: ${run?.status ?? 'unknown'} | ${results?.length ?? 0} samples`}
      />

      <div className="grid grid-cols-4 gap-4">
        <MetricCard title="Overall Score" value={run?.overall_score != null ? `${(run.overall_score * 100).toFixed(1)}%` : '—'} icon={<BarChart3 className="h-4 w-4" />} />
        <MetricCard title="Samples" value={formatNumber(results?.length ?? 0)} icon={<CheckCircle className="h-4 w-4" />} />
        {Object.entries(metricSummary).slice(0, 2).map(([key, val]) => (
          <MetricCard key={key} title={key} value={val.toFixed(3)} icon={<BarChart3 className="h-4 w-4" />} />
        ))}
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">Per-Metric Averages</CardTitle></CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            {Object.entries(metricSummary).map(([key, val]) => (
              <div key={key} className="rounded-md border px-4 py-2">
                <p className="text-xs text-muted-foreground">{key}</p>
                <p className="text-lg font-semibold">{val.toFixed(3)}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <DataTable<EvalResultRow>
        columns={[
          { key: 'input', header: 'Input', render: (r) => <span className="max-w-xs truncate block text-sm">{r.input}</span> },
          { key: 'expected', header: 'Expected', render: (r) => <span className="max-w-xs truncate block text-sm">{r.expected}</span> },
          { key: 'actual', header: 'Actual', render: (r) => <span className="max-w-xs truncate block text-sm">{r.actual}</span> },
          {
            key: 'score', header: 'Score', render: (r) => (
              <div className="flex items-center gap-1">
                {(r.score ?? 0) >= 0.8 ? <CheckCircle className="h-3 w-3 text-green-500" /> : <XCircle className="h-3 w-3 text-red-500" />}
                <span>{((r.score ?? 0) * 100).toFixed(0)}%</span>
              </div>
            ),
          },
        ]}
        data={(results ?? []) as EvalResultRow[]}
      />
    </div>
  )
}

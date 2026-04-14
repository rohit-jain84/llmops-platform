import { useNavigate } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/ui/data-table'
import MetricCard from '@/components/charts/metric-card'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useEvalDatasets, useTriggerEvalRun } from '@/hooks/use-evaluations'
import { formatDate } from '@/lib/utils'
import { Play, ClipboardCheck, BarChart3, Database } from 'lucide-react'

interface EvalRunRow {
  id: string
  dataset_name: string
  status: string
  overall_score?: number
  created_at: string
  [key: string]: unknown
}

export default function EvalDashboard() {
  const navigate = useNavigate()
  const { data: datasets, isLoading } = useEvalDatasets()
  const triggerRun = useTriggerEvalRun()

  if (isLoading) return <LoadingSkeleton />

  const recentRuns: EvalRunRow[] = datasets?.flatMap((d: { name: string; recent_runs?: EvalRunRow[] }) =>
    (d.recent_runs ?? []).map((r: EvalRunRow) => ({ ...r, dataset_name: d.name }))
  ) ?? []

  const avgScore = recentRuns.length
    ? (recentRuns.reduce((s, r) => s + (r.overall_score ?? 0), 0) / recentRuns.length).toFixed(2)
    : '—'

  return (
    <div className="space-y-6">
      <PageHeader
        title="Evaluations"
        description="Automated evaluation runs and scoring"
        actions={<Button onClick={() => navigate('/evaluations/datasets')}><Database className="mr-2 h-4 w-4" />Manage Datasets</Button>}
      />

      <div className="grid grid-cols-3 gap-4">
        <MetricCard title="Datasets" value={String(datasets?.length ?? 0)} icon={<Database className="h-4 w-4" />} />
        <MetricCard title="Recent Runs" value={String(recentRuns.length)} icon={<BarChart3 className="h-4 w-4" />} />
        <MetricCard title="Avg Score" value={avgScore} icon={<ClipboardCheck className="h-4 w-4" />} />
      </div>

      <DataTable<EvalRunRow>
        columns={[
          { key: 'dataset_name', header: 'Dataset', render: (r) => <span className="font-medium">{r.dataset_name}</span> },
          { key: 'status', header: 'Status', render: (r) => <Badge variant={r.status === 'completed' ? 'success' : r.status === 'running' ? 'warning' : 'info'}>{r.status}</Badge> },
          { key: 'overall_score', header: 'Score', render: (r) => r.overall_score != null ? `${(r.overall_score * 100).toFixed(1)}%` : '—' },
          { key: 'created_at', header: 'Run Date', render: (r) => formatDate(r.created_at) },
          {
            key: 'actions', header: '', render: (r) => (
              <div className="flex gap-1">
                <Button size="sm" variant="ghost" onClick={() => navigate(`/evaluations/runs/${r.id}`)}>View</Button>
                <Button size="sm" variant="ghost" onClick={() => triggerRun.mutate({ dataset_id: r.id })}>
                  <Play className="h-3 w-3" />
                </Button>
              </div>
            ),
          },
        ]}
        data={recentRuns}
      />
    </div>
  )
}

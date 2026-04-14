import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/ui/data-table'
import EmptyState from '@/components/common/empty-state'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useExperiments } from '@/hooks/use-experiments'
import { formatDate } from '@/lib/utils'
import { Plus, FlaskConical } from 'lucide-react'

interface ExperimentRow {
  id: string
  name: string
  status: string
  app_id: string
  variants_count?: number
  created_at: string
  [key: string]: unknown
}

const statusVariant: Record<string, string> = {
  running: 'success',
  draft: 'secondary',
  stopped: 'warning',
  completed: 'info',
}

export default function ExperimentsList() {
  const [statusFilter, setStatusFilter] = useState<string>('')
  const { data: experiments, isLoading } = useExperiments()
  const navigate = useNavigate()

  const filtered = statusFilter ? experiments?.filter((e: ExperimentRow) => e.status === statusFilter) : experiments

  if (isLoading) return <LoadingSkeleton lines={5} />

  return (
    <div className="space-y-6">
      <PageHeader
        title="Experiments"
        description="A/B tests and traffic splitting experiments"
        actions={<Button onClick={() => navigate('/experiments/new')}><Plus className="mr-2 h-4 w-4" />New Experiment</Button>}
      />

      <div className="flex gap-2">
        {['', 'draft', 'running', 'stopped', 'completed'].map((s) => (
          <Button key={s} size="sm" variant={statusFilter === s ? 'default' : 'outline'} onClick={() => setStatusFilter(s)}>
            {s || 'All'}
          </Button>
        ))}
      </div>

      {!filtered?.length ? (
        <EmptyState title="No experiments" description="Create your first A/B test experiment" icon={<FlaskConical className="h-10 w-10" />} />
      ) : (
        <DataTable<ExperimentRow>
          columns={[
            { key: 'name', header: 'Name', render: (e) => <span className="font-medium">{e.name}</span> },
            { key: 'status', header: 'Status', render: (e) => <Badge variant={statusVariant[e.status] as 'success' | 'warning' | 'info'}>{e.status}</Badge> },
            { key: 'variants_count', header: 'Variants', render: (e) => e.variants_count ?? '—' },
            { key: 'created_at', header: 'Created', render: (e) => formatDate(e.created_at) },
          ]}
          data={(filtered ?? []) as ExperimentRow[]}
          onRowClick={(e) => navigate(`/experiments/${e.id}`)}
        />
      )}
    </div>
  )
}

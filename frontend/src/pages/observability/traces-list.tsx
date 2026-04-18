import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/ui/data-table'
import EmptyState from '@/components/common/empty-state'
import { formatDate, formatDuration } from '@/lib/utils'
import { Search, Activity } from 'lucide-react'

interface TraceRow {
  id: string
  trace_id: string
  operation: string
  status: string
  duration_ms: number
  model?: string
  app_id: string
  created_at: string
  [key: string]: unknown
}

// Placeholder — replace with real hook
const MOCK_TRACES: TraceRow[] = []

export default function TracesList() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const traces = MOCK_TRACES

  const filtered = traces.filter((t) => {
    if (search && !t.trace_id.includes(search) && !t.operation.includes(search)) return false
    if (statusFilter && t.status !== statusFilter) return false
    return true
  })

  return (
    <div className="space-y-6">
      <PageHeader title="Traces" description="Search and explore distributed traces" />

      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            className="w-full rounded-md border pl-9 pr-3 py-2 text-sm"
            placeholder="Search by trace ID or operation..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          {['', 'ok', 'error', 'timeout'].map((s) => (
            <Button key={s} size="sm" variant={statusFilter === s ? 'default' : 'outline'} onClick={() => setStatusFilter(s)}>
              {s || 'All'}
            </Button>
          ))}
        </div>
      </div>

      {!filtered.length ? (
        <EmptyState title="No traces found" description="Adjust filters or wait for new requests" icon={<Activity className="h-10 w-10" />} />
      ) : (
        <DataTable<TraceRow>
          columns={[
            { key: 'trace_id', header: 'Trace ID', render: (t) => <span className="font-mono text-xs">{t.trace_id.slice(0, 12)}...</span> },
            { key: 'operation', header: 'Operation', render: (t) => <span className="font-medium">{t.operation}</span> },
            { key: 'status', header: 'Status', render: (t) => <Badge variant={t.status === 'ok' ? 'success' : t.status === 'error' ? 'warning' : 'info'}>{t.status}</Badge> },
            { key: 'duration_ms', header: 'Duration', render: (t) => formatDuration(t.duration_ms) },
            { key: 'model', header: 'Model', render: (t) => t.model ?? '—' },
            { key: 'created_at', header: 'Time', render: (t) => formatDate(t.created_at) },
          ]}
          data={filtered}
          onRowClick={(t) => navigate(`/observability/traces/${t.trace_id}`)}
        />
      )}
    </div>
  )
}

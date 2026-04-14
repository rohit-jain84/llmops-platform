import { useParams } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { formatDate, formatDuration } from '@/lib/utils'
import { Clock, Server, Cpu, Hash } from 'lucide-react'

interface Span {
  span_id: string
  operation: string
  service: string
  duration_ms: number
  status: string
  attributes: Record<string, string>
  children?: Span[]
}

// Placeholder — replace with real hook when observability backend is wired
const useMockTrace = (_id: string) => ({
  data: null as { trace_id: string; root_span: Span; total_duration_ms: number; created_at: string } | null,
  isLoading: false,
})

function SpanRow({ span, depth = 0 }: { span: Span; depth?: number }) {
  return (
    <>
      <div className="flex items-center border-b py-2 hover:bg-muted/50" style={{ paddingLeft: `${depth * 24 + 12}px` }}>
        <div className="flex-1">
          <span className="font-medium text-sm">{span.operation}</span>
          <span className="ml-2 text-xs text-muted-foreground">{span.service}</span>
        </div>
        <Badge variant={span.status === 'ok' ? 'success' : 'warning'} className="mr-3">{span.status}</Badge>
        <span className="text-sm font-mono w-20 text-right">{formatDuration(span.duration_ms)}</span>
      </div>
      {span.children?.map((child) => (
        <SpanRow key={child.span_id} span={child} depth={depth + 1} />
      ))}
    </>
  )
}

export default function TraceViewer() {
  const { id } = useParams<{ id: string }>()
  const { data: trace, isLoading } = useMockTrace(id!)

  if (isLoading) return <LoadingSkeleton />

  if (!trace) {
    return (
      <div className="space-y-6">
        <PageHeader title={`Trace ${id?.slice(0, 8)}...`} description="Request trace detail" />

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader><CardTitle className="text-lg">Trace Info</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Trace ID</span>
                <code className="font-mono text-xs">{id}</code>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Status</span>
                <Badge variant="success">OK</Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                Connect to the observability backend to view full span waterfall. External links available below.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-lg">External Links</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <a href="http://localhost:3001" target="_blank" rel="noopener noreferrer"
                className="block text-sm text-blue-600 hover:underline">
                View in LangFuse
              </a>
              <a href={`http://localhost:3002/explore?left=["now-1h","now","Tempo",{"query":"${id}"}]`}
                target="_blank" rel="noopener noreferrer"
                className="block text-sm text-blue-600 hover:underline">
                View in Grafana Tempo
              </a>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader title={`Trace ${trace.trace_id.slice(0, 12)}...`} description={`Captured at ${formatDate(trace.created_at)}`} />

      <div className="grid grid-cols-4 gap-4">
        <Card className="p-4 flex items-center gap-3">
          <Hash className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">Trace ID</p>
            <p className="font-mono text-xs">{trace.trace_id}</p>
          </div>
        </Card>
        <Card className="p-4 flex items-center gap-3">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">Total Duration</p>
            <p className="font-semibold">{formatDuration(trace.total_duration_ms)}</p>
          </div>
        </Card>
        <Card className="p-4 flex items-center gap-3">
          <Server className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">Root Operation</p>
            <p className="text-sm">{trace.root_span.operation}</p>
          </div>
        </Card>
        <Card className="p-4 flex items-center gap-3">
          <Cpu className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">Service</p>
            <p className="text-sm">{trace.root_span.service}</p>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">Span Waterfall</CardTitle></CardHeader>
        <CardContent className="p-0">
          <SpanRow span={trace.root_span} />
        </CardContent>
      </Card>
    </div>
  )
}

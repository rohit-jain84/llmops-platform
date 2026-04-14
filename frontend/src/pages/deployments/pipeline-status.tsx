import { useNavigate } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/ui/data-table'
import EmptyState from '@/components/common/empty-state'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useDeployments } from '@/hooks/use-deployments'
import { formatDate } from '@/lib/utils'
import type { Deployment } from '@/api/types'
import { Rocket, ArrowRight } from 'lucide-react'

const statusBadge = (status: string) => {
  const variants: Record<string, 'default' | 'success' | 'warning' | 'destructive' | 'info'> = {
    pending_eval: 'info',
    eval_passed: 'success',
    eval_failed: 'destructive',
    canary: 'warning',
    rolled_out: 'success',
    rolled_back: 'destructive',
  }
  return <Badge variant={variants[status] || 'default'}>{status.replace('_', ' ')}</Badge>
}

const envOrder = ['staging', 'canary', 'production'] as const

export default function PipelineStatus() {
  const { data: deployments, isLoading } = useDeployments()
  const navigate = useNavigate()

  if (isLoading) return <LoadingSkeleton lines={5} />

  if (!deployments?.length) {
    return (
      <div>
        <PageHeader title="Deployments" description="Deployment pipeline status" />
        <EmptyState title="No deployments yet" description="Deploy a prompt version to get started" />
      </div>
    )
  }

  // Group deployments by environment for pipeline view
  const byEnv = envOrder.map((env) => ({
    env,
    items: (deployments as Array<Deployment & { environment?: string }>).filter((d) =>
      d.status === env || (env === 'staging' && d.status === 'pending_eval') ||
      (env === 'canary' && d.status === 'canary') ||
      (env === 'production' && d.status === 'rolled_out')
    ),
  }))

  return (
    <div className="space-y-6">
      <PageHeader title="Deployment Pipeline" description="Active deployments across environments" />

      <div className="flex items-start gap-4 overflow-x-auto pb-4">
        {byEnv.map((group, i) => (
          <div key={group.env} className="flex items-start gap-4">
            <Card className="min-w-[280px]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm capitalize">
                  <Rocket className="h-4 w-4" />
                  {group.env}
                  <Badge variant="info">{group.items.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {group.items.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No active deployments</p>
                ) : (
                  group.items.map((d) => (
                    <div
                      key={d.id}
                      className="cursor-pointer rounded-md border p-3 hover:bg-muted/50 transition-colors"
                      onClick={() => navigate(`/deployments/${d.id}`)}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <code className="font-mono text-xs">{d.id.slice(0, 8)}...</code>
                        {statusBadge(d.status)}
                      </div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Canary: {d.canary_pct}%</span>
                        <span>{formatDate(d.created_at)}</span>
                      </div>
                      <div className="mt-2 h-2 w-full rounded-full bg-muted">
                        <div className="h-2 rounded-full bg-blue-500 transition-all" style={{ width: `${d.canary_pct}%` }} />
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
            {i < byEnv.length - 1 && <ArrowRight className="mt-12 h-5 w-5 text-muted-foreground flex-shrink-0" />}
          </div>
        ))}
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">All Deployments</CardTitle></CardHeader>
        <CardContent className="p-0">
          <DataTable<Deployment & Record<string, unknown>>
            columns={[
              { key: 'status', header: 'Status', render: (d) => statusBadge(d.status) },
              { key: 'canary_pct', header: 'Canary %', render: (d) => (
                <div className="flex items-center gap-2">
                  <div className="h-2 w-24 rounded-full bg-muted">
                    <div className="h-2 rounded-full bg-blue-500" style={{ width: `${d.canary_pct}%` }} />
                  </div>
                  <span className="text-sm">{d.canary_pct}%</span>
                </div>
              )},
              { key: 'created_at', header: 'Created', render: (d) => formatDate(d.created_at) },
              { key: 'updated_at', header: 'Updated', render: (d) => formatDate(d.updated_at) },
            ]}
            data={(deployments ?? []) as Array<Deployment & Record<string, unknown>>}
            onRowClick={(d) => navigate(`/deployments/${d.id}`)}
          />
        </CardContent>
      </Card>
    </div>
  )
}

import { useParams } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useDeployment, usePromoteDeployment, useRollbackDeployment } from '@/hooks/use-deployments'
import { formatDate } from '@/lib/utils'
import { ArrowUpCircle, ArrowDownCircle, Clock } from 'lucide-react'

interface AuditEntry {
  timestamp: string
  action: string
  actor: string
  details: string
}

export default function DeploymentHistory() {
  const { id } = useParams<{ id: string }>()
  const { data: deployment, isLoading } = useDeployment(id!)
  const promote = usePromoteDeployment()
  const rollback = useRollbackDeployment()

  if (isLoading) return <LoadingSkeleton />
  if (!deployment) return null

  const canPromote = ['canary', 'eval_passed'].includes(deployment.status)
  const canRollback = ['canary', 'rolled_out'].includes(deployment.status)

  // Build audit trail from deployment data
  const auditTrail: AuditEntry[] = [
    { timestamp: deployment.created_at, action: 'Created', actor: 'system', details: `Deployment initiated for version ${deployment.prompt_version_id.slice(0, 8)}` },
    ...(deployment.updated_at !== deployment.created_at
      ? [{ timestamp: deployment.updated_at, action: 'Updated', actor: 'system', details: `Status changed to ${deployment.status}, canary at ${deployment.canary_pct}%` }]
      : []),
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Deployment ${id?.slice(0, 8)}...`}
        description="Deployment details and audit trail"
        actions={
          <div className="flex gap-2">
            {canRollback && (
              <Button variant="destructive" onClick={() => rollback.mutate(id!)} disabled={rollback.isPending}>
                <ArrowDownCircle className="mr-2 h-4 w-4" />Rollback
              </Button>
            )}
            {canPromote && (
              <Button onClick={() => promote.mutate(id!)} disabled={promote.isPending}>
                <ArrowUpCircle className="mr-2 h-4 w-4" />Promote ({deployment.canary_pct}% -> next)
              </Button>
            )}
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="text-lg">Status</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Status</span>
              <Badge>{deployment.status.replace('_', ' ')}</Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Canary %</span>
              <span className="font-medium">{deployment.canary_pct}%</span>
            </div>
            <div className="h-3 w-full rounded-full bg-muted">
              <div className="h-3 rounded-full bg-blue-500 transition-all" style={{ width: `${deployment.canary_pct}%` }} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">Details</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Prompt Version</span>
              <code className="font-mono text-xs">{deployment.prompt_version_id.slice(0, 8)}...</code>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Previous Version</span>
              <code className="font-mono text-xs">{deployment.previous_version_id?.slice(0, 8) || '---'}...</code>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Created</span>
              <span>{formatDate(deployment.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Last Updated</span>
              <span>{formatDate(deployment.updated_at)}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Canary Progression</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            {[10, 25, 50, 100].map((stage) => (
              <div key={stage} className="flex items-center gap-2">
                <div className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold ${
                  deployment.canary_pct >= stage ? 'bg-blue-500 text-white' : 'bg-muted text-muted-foreground'
                }`}>
                  {stage}%
                </div>
                {stage < 100 && <div className="h-0.5 w-8 bg-muted" />}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-lg">Audit Trail</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-4">
            {auditTrail.map((entry, i) => (
              <div key={i} className="flex items-start gap-3">
                <Clock className="mt-0.5 h-4 w-4 text-muted-foreground flex-shrink-0" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{entry.action}</span>
                    <span className="text-xs text-muted-foreground">{formatDate(entry.timestamp)}</span>
                    <Badge variant="secondary" className="text-xs">{entry.actor}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{entry.details}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

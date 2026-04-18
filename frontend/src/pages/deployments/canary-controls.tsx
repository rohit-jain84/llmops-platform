import { useParams } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import MetricCard from '@/components/charts/metric-card'
import { LineChart } from '@/components/charts/line-chart'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useDeployment, usePromoteDeployment, useRollbackDeployment } from '@/hooks/use-deployments'
import { formatDate } from '@/lib/utils'
import { Shield, ArrowUp, ArrowDown, Activity, CheckCircle } from 'lucide-react'

const CANARY_STAGES = [10, 25, 50, 100]

export default function CanaryControls() {
  const { id } = useParams<{ id: string }>()
  const { data: deployment, isLoading } = useDeployment(id!)
  const promote = usePromoteDeployment()
  const rollback = useRollbackDeployment()

  if (isLoading) return <LoadingSkeleton />
  if (!deployment) return null

  const nextStage = CANARY_STAGES.find((s) => s > deployment.canary_pct)
  const canPromote = ['canary', 'eval_passed'].includes(deployment.status) && nextStage !== undefined
  const canRollback = ['canary', 'rolled_out'].includes(deployment.status)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Canary Controls"
        description={`Managing canary deployment for ${id?.slice(0, 8)}...`}
      />

      <div className="grid grid-cols-4 gap-4">
        <MetricCard title="Current Traffic" value={`${deployment.canary_pct}%`} icon={<Shield className="h-4 w-4" />} />
        <MetricCard title="Status" value={deployment.status.replace('_', ' ')} icon={<Activity className="h-4 w-4" />} />
        <MetricCard title="Next Stage" value={nextStage ? `${nextStage}%` : 'Fully rolled out'} icon={<ArrowUp className="h-4 w-4" />} />
        <MetricCard title="Version" value={deployment.prompt_version_id.slice(0, 8)} icon={<CheckCircle className="h-4 w-4" />} />
      </div>

      {/* Canary progression */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Canary Progression</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            {CANARY_STAGES.map((stage, i) => (
              <div key={stage} className="flex items-center gap-2">
                <div className={`h-10 w-10 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                  deployment.canary_pct >= stage
                    ? 'bg-blue-500 text-white'
                    : deployment.canary_pct > (CANARY_STAGES[i - 1] ?? 0) && deployment.canary_pct < stage
                      ? 'bg-blue-200 text-blue-800 ring-2 ring-blue-400'
                      : 'bg-muted text-muted-foreground'
                }`}>
                  {stage}%
                </div>
                {i < CANARY_STAGES.length - 1 && (
                  <div className={`h-0.5 w-12 ${deployment.canary_pct >= CANARY_STAGES[i + 1] ? 'bg-blue-500' : 'bg-muted'}`} />
                )}
              </div>
            ))}
          </div>
          <div className="mt-4 h-3 w-full rounded-full bg-muted">
            <div className="h-3 rounded-full bg-blue-500 transition-all" style={{ width: `${deployment.canary_pct}%` }} />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            {deployment.canary_pct}% of traffic is routed to the new version. Last updated: {formatDate(deployment.updated_at)}
          </p>
        </CardContent>
      </Card>

      {/* Health metrics placeholder */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Canary Health Metrics</CardTitle></CardHeader>
        <CardContent>
          <LineChart
            data={[]}
            lines={[
              { key: 'canary_error_rate', label: 'Canary Error Rate', color: '#ef4444' },
              { key: 'baseline_error_rate', label: 'Baseline Error Rate', color: '#3b82f6' },
            ]}
            xAxisKey="time"
          />
          <p className="mt-2 text-xs text-muted-foreground">Health metrics will populate once the canary receives traffic.</p>
        </CardContent>
      </Card>

      {/* Promote / Rollback actions */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ArrowUp className="h-5 w-5 text-green-600" /> Promote
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              {canPromote
                ? `Increase canary traffic from ${deployment.canary_pct}% to ${nextStage}%. Quality metrics will be monitored automatically.`
                : 'Deployment is fully rolled out or cannot be promoted in current state.'}
            </p>
            <Button
              className="w-full"
              onClick={() => promote.mutate(id!)}
              disabled={promote.isPending || !canPromote}
            >
              {promote.isPending ? 'Promoting...' : canPromote ? `Promote to ${nextStage}%` : 'Fully Rolled Out'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <ArrowDown className="h-5 w-5 text-red-600" /> Rollback
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Immediately rollback to the previous version ({deployment.previous_version_id?.slice(0, 8) || 'N/A'}). All canary traffic will be redirected.
            </p>
            <Button
              variant="destructive"
              className="w-full"
              onClick={() => rollback.mutate(id!)}
              disabled={rollback.isPending || !canRollback}
            >
              {rollback.isPending ? 'Rolling back...' : 'Rollback Now'}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

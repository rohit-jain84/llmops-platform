import { useParams } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import MetricCard from '@/components/charts/metric-card'
import { BarChart } from '@/components/charts/bar-chart'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useHumanEvalCampaign } from '@/hooks/use-evaluations'
import { formatNumber } from '@/lib/utils'
import { Users, CheckCircle, BarChart3, Clock } from 'lucide-react'

export default function CampaignDetail() {
  const { campaignId } = useParams<{ campaignId: string }>()
  const { data: campaign, isLoading } = useHumanEvalCampaign(campaignId)

  if (isLoading) return <LoadingSkeleton />

  const progressPct = campaign?.total_items
    ? ((campaign.completed_items / campaign.total_items) * 100).toFixed(0)
    : '0'

  return (
    <div className="space-y-6">
      <PageHeader
        title={campaign?.name ?? 'Campaign'}
        description={campaign?.description}
      />

      <div className="grid grid-cols-4 gap-4">
        <MetricCard title="Progress" value={`${progressPct}%`} icon={<CheckCircle className="h-4 w-4" />} />
        <MetricCard title="Completed" value={`${formatNumber(campaign?.completed_items ?? 0)}/${formatNumber(campaign?.total_items ?? 0)}`} icon={<BarChart3 className="h-4 w-4" />} />
        <MetricCard title="Reviewers" value={String(campaign?.reviewers_count ?? 0)} icon={<Users className="h-4 w-4" />} />
        <MetricCard title="Status" value={campaign?.status ?? '—'} icon={<Clock className="h-4 w-4" />} />
      </div>

      <div className="w-full rounded-full bg-muted h-3">
        <div className="h-3 rounded-full bg-primary transition-all" style={{ width: `${progressPct}%` }} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle className="text-sm">Score Distribution</CardTitle></CardHeader>
          <CardContent>
            <BarChart
              data={campaign?.score_distribution ?? []}
              bars={[{ key: 'count', label: 'Count', color: '#3b82f6' }]}
              xAxisKey="score"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Reviewer Progress</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {(campaign?.reviewers ?? []).map((r: { email: string; completed: number; total: number }) => (
                <div key={r.email} className="flex items-center justify-between">
                  <span className="text-sm">{r.email}</span>
                  <Badge variant={r.completed === r.total ? 'success' : 'info'}>{r.completed}/{r.total}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

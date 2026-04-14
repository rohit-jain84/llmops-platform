import { useNavigate } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/ui/data-table'
import EmptyState from '@/components/common/empty-state'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useHumanEvalCampaign } from '@/hooks/use-evaluations'
import { formatDate } from '@/lib/utils'
import { Plus, Users } from 'lucide-react'

interface CampaignRow {
  id: string
  name: string
  status: string
  total_items: number
  completed_items: number
  reviewers_count: number
  created_at: string
  [key: string]: unknown
}

const statusVariant: Record<string, string> = { active: 'success', draft: 'secondary', completed: 'info', paused: 'warning' }

export default function CampaignsList() {
  const navigate = useNavigate()
  const { data: campaigns, isLoading } = useHumanEvalCampaign()

  if (isLoading) return <LoadingSkeleton lines={5} />

  return (
    <div className="space-y-6">
      <PageHeader
        title="Human Evaluation Campaigns"
        description="Manage human review campaigns for quality assessment"
        actions={<Button onClick={() => navigate('/evaluations/human-eval/new')}><Plus className="mr-2 h-4 w-4" />New Campaign</Button>}
      />

      {!campaigns?.length ? (
        <EmptyState title="No campaigns" description="Create a human evaluation campaign" icon={<Users className="h-10 w-10" />} />
      ) : (
        <DataTable<CampaignRow>
          columns={[
            { key: 'name', header: 'Campaign', render: (c) => <span className="font-medium">{c.name}</span> },
            { key: 'status', header: 'Status', render: (c) => <Badge variant={statusVariant[c.status] as 'success' | 'warning' | 'info'}>{c.status}</Badge> },
            { key: 'progress', header: 'Progress', render: (c) => `${c.completed_items}/${c.total_items}` },
            { key: 'reviewers_count', header: 'Reviewers', render: (c) => c.reviewers_count },
            { key: 'created_at', header: 'Created', render: (c) => formatDate(c.created_at) },
          ]}
          data={(campaigns ?? []) as CampaignRow[]}
          onRowClick={(c) => navigate(`/evaluations/human-eval/${c.id}`)}
        />
      )}
    </div>
  )
}

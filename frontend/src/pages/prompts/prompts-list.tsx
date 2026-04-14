import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/ui/data-table'
import EmptyState from '@/components/common/empty-state'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { usePrompts } from '@/hooks/use-prompts'
import { formatDate } from '@/lib/utils'
import type { PromptTemplate } from '@/api/types'
import { Plus } from 'lucide-react'

export default function PromptsList() {
  const [selectedApp] = useState<string>('')
  const { data: prompts, isLoading } = usePrompts(selectedApp)
  const navigate = useNavigate()

  if (isLoading) return <LoadingSkeleton lines={5} />

  return (
    <div>
      <PageHeader
        title="Prompts"
        description="Manage prompt templates and versions"
        actions={<Button onClick={() => {}}><Plus className="mr-2 h-4 w-4" />New Prompt</Button>}
      />

      {!prompts?.length ? (
        <EmptyState
          title="No prompts yet"
          description="Create your first prompt template to get started"
          action={<Button><Plus className="mr-2 h-4 w-4" />Create Prompt</Button>}
        />
      ) : (
        <DataTable<PromptTemplate & Record<string, unknown>>
          columns={[
            { key: 'name', header: 'Name', render: (item) => <span className="font-medium">{item.name}</span> },
            { key: 'description', header: 'Description', render: (item) => <span className="text-muted-foreground">{item.description || '—'}</span> },
            { key: 'created_at', header: 'Created', render: (item) => formatDate(item.created_at) },
          ]}
          data={(prompts ?? []) as Array<PromptTemplate & Record<string, unknown>>}
          onRowClick={(item) => navigate(`/prompts/${item.id}`)}
        />
      )}
    </div>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/ui/data-table'
import EmptyState from '@/components/common/empty-state'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { usePrompts } from '@/hooks/use-prompts'
import { formatDate } from '@/lib/utils'
import { promptsApi } from '@/api/prompts'
import type { PromptTemplate } from '@/api/types'
import { Plus } from 'lucide-react'

export default function PromptsList() {
  const [selectedApp] = useState<string>('')
  const { data: prompts, isLoading, refetch } = usePrompts(selectedApp)
  const navigate = useNavigate()
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [appId, setAppId] = useState('')
  const [creating, setCreating] = useState(false)

  const handleCreate = async () => {
    if (!name || !appId) return
    setCreating(true)
    try {
      const created = await promptsApi.create(appId, { name, description })
      setShowCreate(false)
      setName('')
      setDescription('')
      setAppId('')
      refetch()
      navigate(`/prompts/${created.id}`)
    } catch {
      // stay on dialog so user can retry
    } finally {
      setCreating(false)
    }
  }

  if (isLoading) return <LoadingSkeleton lines={5} />

  return (
    <div>
      <PageHeader
        title="Prompts"
        description="Manage prompt templates and versions"
        actions={<Button onClick={() => setShowCreate(true)}><Plus className="mr-2 h-4 w-4" />New Prompt</Button>}
      />

      {showCreate && (
        <Card className="mb-6">
          <CardHeader><CardTitle className="text-sm">Create Prompt Template</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="text-sm font-medium">Application ID</label>
              <input className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={appId} onChange={(e) => setAppId(e.target.value)} placeholder="app-xxx" />
            </div>
            <div>
              <label className="text-sm font-medium">Name</label>
              <input className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g., Customer Support Prompt" />
            </div>
            <div>
              <label className="text-sm font-medium">Description</label>
              <input className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description" />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={!name || !appId || creating}>{creating ? 'Creating...' : 'Create'}</Button>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {!prompts?.length ? (
        <EmptyState
          title="No prompts yet"
          description="Create your first prompt template to get started"
          action={<Button onClick={() => setShowCreate(true)}><Plus className="mr-2 h-4 w-4" />Create Prompt</Button>}
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

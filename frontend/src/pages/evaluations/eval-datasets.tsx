import { useState } from 'react'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable } from '@/components/ui/data-table'
import EmptyState from '@/components/common/empty-state'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useEvalDatasets, useCreateEvalDataset } from '@/hooks/use-evaluations'
import { formatDate, formatNumber } from '@/lib/utils'
import { Plus, Database, Upload } from 'lucide-react'

interface DatasetRow {
  id: string
  name: string
  description?: string
  item_count: number
  created_at: string
  [key: string]: unknown
}

export default function EvalDatasets() {
  const { data: datasets, isLoading } = useEvalDatasets()
  const createDataset = useCreateEvalDataset()
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  if (isLoading) return <LoadingSkeleton />

  const handleCreate = async () => {
    await createDataset.mutateAsync({ name, description })
    setName('')
    setDescription('')
    setShowCreate(false)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Evaluation Datasets"
        description="Manage test datasets for evaluations"
        actions={<Button onClick={() => setShowCreate(true)}><Plus className="mr-2 h-4 w-4" />New Dataset</Button>}
      />

      {showCreate && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Create Dataset</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="text-sm font-medium">Name</label>
              <input className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium">Description</label>
              <input className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={!name || createDataset.isPending}>
                {createDataset.isPending ? 'Creating...' : 'Create'}
              </Button>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {!datasets?.length ? (
        <EmptyState title="No datasets" description="Create a dataset to start evaluating" icon={<Database className="h-10 w-10" />} />
      ) : (
        <DataTable<DatasetRow>
          columns={[
            { key: 'name', header: 'Name', render: (d) => <span className="font-medium">{d.name}</span> },
            { key: 'description', header: 'Description', render: (d) => <span className="text-muted-foreground">{d.description || '—'}</span> },
            { key: 'item_count', header: 'Items', render: (d) => formatNumber(d.item_count) },
            { key: 'created_at', header: 'Created', render: (d) => formatDate(d.created_at) },
            {
              key: 'actions', header: '', render: () => (
                <Button size="sm" variant="ghost"><Upload className="mr-1 h-3 w-3" />Upload</Button>
              ),
            },
          ]}
          data={(datasets ?? []) as DatasetRow[]}
        />
      )}
    </div>
  )
}

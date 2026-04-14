import { useState } from 'react'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/ui/data-table'
import EmptyState from '@/components/common/empty-state'
import { formatDate } from '@/lib/utils'
import { Plus, Route, Trash2 } from 'lucide-react'

interface RoutingRule {
  id: string
  name: string
  condition: string
  target_model: string
  priority: number
  enabled: boolean
  created_at: string
  [key: string]: unknown
}

// Placeholder data — replace with actual hook when available
const MOCK_RULES: RoutingRule[] = []

export default function RoutingRules() {
  const [rules] = useState<RoutingRule[]>(MOCK_RULES)
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [condition, setCondition] = useState('')
  const [targetModel, setTargetModel] = useState('gpt-4o-mini')
  const [priority, setPriority] = useState(10)

  const handleCreate = () => {
    // Wire to actual mutation hook
    setShowCreate(false)
    setName('')
    setCondition('')
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Routing Rules"
        description="Configure intelligent model routing to optimize cost and quality"
        actions={<Button onClick={() => setShowCreate(true)}><Plus className="mr-2 h-4 w-4" />New Rule</Button>}
      />

      {showCreate && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Create Routing Rule</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm font-medium">Rule Name</label>
                <input className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g., Simple queries to mini" />
              </div>
              <div>
                <label className="text-sm font-medium">Target Model</label>
                <select className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={targetModel} onChange={(e) => setTargetModel(e.target.value)}>
                  <option value="gpt-4o">gpt-4o</option>
                  <option value="gpt-4o-mini">gpt-4o-mini</option>
                  <option value="claude-3.5-sonnet">claude-3.5-sonnet</option>
                  <option value="claude-3-haiku">claude-3-haiku</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Condition (expression)</label>
              <input className="mt-1 w-full rounded-md border px-3 py-2 text-sm font-mono" value={condition} onChange={(e) => setCondition(e.target.value)} placeholder='token_count < 200 AND complexity == "low"' />
            </div>
            <div className="w-32">
              <label className="text-sm font-medium">Priority</label>
              <input type="number" className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={priority} onChange={(e) => setPriority(Number(e.target.value))} />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={!name || !condition}>Create Rule</Button>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {!rules.length ? (
        <EmptyState title="No routing rules" description="Create routing rules to optimize model selection based on query characteristics" icon={<Route className="h-10 w-10" />} />
      ) : (
        <DataTable<RoutingRule>
          columns={[
            { key: 'name', header: 'Name', render: (r) => <span className="font-medium">{r.name}</span> },
            { key: 'condition', header: 'Condition', render: (r) => <code className="text-xs bg-muted px-2 py-1 rounded">{r.condition}</code> },
            { key: 'target_model', header: 'Target Model', render: (r) => <Badge variant="info">{r.target_model}</Badge> },
            { key: 'priority', header: 'Priority', render: (r) => r.priority },
            { key: 'enabled', header: 'Status', render: (r) => <Badge variant={r.enabled ? 'success' : 'secondary'}>{r.enabled ? 'Active' : 'Disabled'}</Badge> },
            { key: 'created_at', header: 'Created', render: (r) => formatDate(r.created_at) },
            { key: 'actions', header: '', render: () => <Button size="sm" variant="ghost"><Trash2 className="h-3 w-3 text-destructive" /></Button> },
          ]}
          data={rules}
        />
      )}
    </div>
  )
}

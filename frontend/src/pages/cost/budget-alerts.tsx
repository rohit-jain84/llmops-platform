import { useState } from 'react'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/ui/data-table'
import EmptyState from '@/components/common/empty-state'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useBudgetAlerts, useCreateBudgetAlert } from '@/hooks/use-cost'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Plus, Bell, AlertTriangle } from 'lucide-react'

interface AlertRow {
  id: string
  name: string
  threshold: number
  period: string
  current_spend: number
  status: string
  notification_channels: string[]
  created_at: string
  [key: string]: unknown
}

export default function BudgetAlerts() {
  const { data: alerts, isLoading } = useBudgetAlerts()
  const createAlert = useCreateBudgetAlert()
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [threshold, setThreshold] = useState(100)
  const [period, setPeriod] = useState('monthly')

  if (isLoading) return <LoadingSkeleton />

  const handleCreate = async () => {
    await createAlert.mutateAsync({ name, threshold, period })
    setShowCreate(false)
    setName('')
    setThreshold(100)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Budget Alerts"
        description="Set spending thresholds and get notified before exceeding budget"
        actions={<Button onClick={() => setShowCreate(true)}><Plus className="mr-2 h-4 w-4" />New Alert</Button>}
      />

      {showCreate && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Create Budget Alert</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="text-sm font-medium">Alert Name</label>
              <input className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g., Monthly team budget" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm font-medium">Threshold ($)</label>
                <input type="number" className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} />
              </div>
              <div>
                <label className="text-sm font-medium">Period</label>
                <select className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={period} onChange={(e) => setPeriod(e.target.value)}>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={!name || createAlert.isPending}>{createAlert.isPending ? 'Creating...' : 'Create'}</Button>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {!alerts?.length ? (
        <EmptyState title="No budget alerts" description="Create alerts to monitor spending thresholds" icon={<Bell className="h-10 w-10" />} />
      ) : (
        <DataTable<AlertRow>
          columns={[
            { key: 'name', header: 'Alert', render: (a) => <span className="font-medium">{a.name}</span> },
            { key: 'threshold', header: 'Threshold', render: (a) => formatCurrency(a.threshold) },
            { key: 'current_spend', header: 'Current Spend', render: (a) => formatCurrency(a.current_spend) },
            { key: 'period', header: 'Period', render: (a) => <Badge variant="info">{a.period}</Badge> },
            {
              key: 'status', header: 'Status', render: (a) => (
                <Badge variant={a.status === 'triggered' ? 'warning' : 'success'}>
                  {a.status === 'triggered' && <AlertTriangle className="mr-1 h-3 w-3" />}
                  {a.status}
                </Badge>
              ),
            },
            { key: 'created_at', header: 'Created', render: (a) => formatDate(a.created_at) },
          ]}
          data={(alerts ?? []) as AlertRow[]}
        />
      )}
    </div>
  )
}

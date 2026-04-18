import { useState } from 'react'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/ui/data-table'
import { Plus, Trash2 } from 'lucide-react'

interface AlertRule {
  id: string
  name: string
  metric: string
  condition: string
  threshold: number
  severity: string
  enabled: boolean
  notification_channel: string
  [key: string]: unknown
}

const DEFAULT_RULES: AlertRule[] = [
  { id: '1', name: 'High Error Rate', metric: 'error_rate', condition: 'Error rate > 5% for 5 minutes', threshold: 5, severity: 'critical', enabled: true, notification_channel: 'slack' },
  { id: '2', name: 'High Latency', metric: 'latency_p99', condition: 'p99 latency > 10s for 5 minutes', threshold: 10000, severity: 'warning', enabled: true, notification_channel: 'pagerduty' },
  { id: '3', name: 'Eval Score Regression', metric: 'eval_score', condition: 'Avg eval score drops below threshold', threshold: 0.7, severity: 'critical', enabled: true, notification_channel: 'slack' },
  { id: '4', name: 'Budget Exceeded', metric: 'budget', condition: 'Spend exceeds 80% or 100% of budget', threshold: 80, severity: 'warning', enabled: true, notification_channel: 'email' },
  { id: '5', name: 'Low Cache Hit Ratio', metric: 'cache_hit', condition: 'Cache hit ratio < 20%', threshold: 20, severity: 'info', enabled: false, notification_channel: 'slack' },
]

export default function AlertConfig() {
  const [alerts, setAlerts] = useState<AlertRule[]>(DEFAULT_RULES)
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [metric, setMetric] = useState('latency_p99')
  const [condition, setCondition] = useState('greater_than')
  const [threshold, setThreshold] = useState(1000)
  const [severity, setSeverity] = useState('warning')

  const handleCreate = () => {
    setAlerts((prev) => [...prev, {
      id: String(prev.length + 1), name, metric, condition: `${metric} ${condition} ${threshold}`,
      threshold, severity, enabled: true, notification_channel: 'slack',
    }])
    setShowCreate(false)
    setName('')
  }

  const toggleAlert = (id: string) => {
    setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, enabled: !a.enabled } : a))
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Alert Configuration"
        description="Alerting rules for quality degradation and system issues"
        actions={<Button onClick={() => setShowCreate(true)}><Plus className="mr-2 h-4 w-4" />New Alert</Button>}
      />

      {showCreate && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Create Alert Rule</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="text-sm font-medium">Name</label>
              <input className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g., High latency alert" />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-sm font-medium">Metric</label>
                <select className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={metric} onChange={(e) => setMetric(e.target.value)}>
                  <option value="latency_p99">Latency P99</option>
                  <option value="latency_p95">Latency P95</option>
                  <option value="error_rate">Error Rate</option>
                  <option value="throughput">Throughput</option>
                  <option value="token_usage">Token Usage</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Condition</label>
                <select className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={condition} onChange={(e) => setCondition(e.target.value)}>
                  <option value="greater_than">Greater Than</option>
                  <option value="less_than">Less Than</option>
                  <option value="equals">Equals</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Threshold</label>
                <input type="number" className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Severity</label>
              <select className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={severity} onChange={(e) => setSeverity(e.target.value)}>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreate} disabled={!name}>Create</Button>
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <DataTable<AlertRule>
        columns={[
          { key: 'name', header: 'Alert Rule', render: (a) => <span className="font-medium">{a.name}</span> },
          { key: 'condition', header: 'Condition', render: (a) => <span className="text-sm text-muted-foreground">{a.condition}</span> },
          { key: 'severity', header: 'Severity', render: (a) => <Badge variant={a.severity === 'critical' ? 'warning' : a.severity === 'warning' ? 'info' : 'secondary'}>{a.severity}</Badge> },
          { key: 'enabled', header: 'Status', render: (a) => (
            <button onClick={() => toggleAlert(a.id)}>
              <Badge variant={a.enabled ? 'success' : 'secondary'}>{a.enabled ? 'Active' : 'Disabled'}</Badge>
            </button>
          )},
          { key: 'notification_channel', header: 'Channel', render: (a) => a.notification_channel },
          { key: 'actions', header: '', render: () => <Button size="sm" variant="ghost"><Trash2 className="h-3 w-3 text-destructive" /></Button> },
        ]}
        data={alerts}
      />
    </div>
  )
}

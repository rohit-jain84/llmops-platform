import PageHeader from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import MetricCard from '@/components/charts/metric-card'
import { LineChart } from '@/components/charts/line-chart'
import { Activity, Clock, AlertTriangle, Gauge, ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'

const GRAFANA_DASHBOARDS = [
  { name: 'Request Latency', url: '/grafana/d/latency', description: 'P50/P95/P99 latency distributions' },
  { name: 'Error Rates', url: '/grafana/d/errors', description: 'Error rate by endpoint and model' },
  { name: 'Throughput', url: '/grafana/d/throughput', description: 'Requests per second by application' },
  { name: 'Model Performance', url: '/grafana/d/models', description: 'Token throughput and queue depth' },
]

export default function ObservabilityDashboard() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Observability"
        description="System health, performance metrics, and monitoring"
        actions={<Link to="/observability/alerts"><Button variant="outline"><AlertTriangle className="mr-2 h-4 w-4" />Alert Config</Button></Link>}
      />

      <div className="grid grid-cols-4 gap-4">
        <MetricCard title="Avg Latency (P50)" value="245ms" trend={-5.2} icon={<Clock className="h-4 w-4" />} />
        <MetricCard title="Error Rate" value="0.12%" trend={0.03} icon={<AlertTriangle className="h-4 w-4" />} />
        <MetricCard title="Throughput" value="1.2K req/s" icon={<Gauge className="h-4 w-4" />} />
        <MetricCard title="Active Traces" value="3,847" icon={<Activity className="h-4 w-4" />} />
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">Request Latency (24h)</CardTitle></CardHeader>
        <CardContent>
          <LineChart
            data={[]}
            lines={[
              { dataKey: 'p50', name: 'P50', color: '#3b82f6' },
              { dataKey: 'p95', name: 'P95', color: '#f59e0b' },
              { dataKey: 'p99', name: 'P99', color: '#ef4444' },
            ]}
            xAxisKey="time"
          />
        </CardContent>
      </Card>

      <div>
        <h2 className="mb-3 text-sm font-semibold">Grafana Dashboards</h2>
        <div className="grid grid-cols-2 gap-4">
          {GRAFANA_DASHBOARDS.map((d) => (
            <Card key={d.name} className="cursor-pointer hover:bg-muted/50 transition-colors">
              <CardContent className="flex items-center justify-between p-4">
                <div>
                  <p className="font-medium text-sm">{d.name}</p>
                  <p className="text-xs text-muted-foreground">{d.description}</p>
                </div>
                <a href={d.url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4 text-muted-foreground" />
                </a>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <div className="flex gap-2">
        <Link to="/observability/traces"><Button variant="outline">View Traces</Button></Link>
        <Link to="/observability/alerts"><Button variant="outline">Manage Alerts</Button></Link>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { useParams } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import PromptEditor from '@/components/editor/prompt-editor'
import MetricCard from '@/components/charts/metric-card'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { usePrompt, usePromptVersions, useRenderPrompt } from '@/hooks/use-prompts'
import { usePlaygroundStore } from '@/stores'
import { Play, Clock, Coins, Hash } from 'lucide-react'

export default function PromptPlayground() {
  const { id } = useParams<{ id: string }>()
  const { data: template, isLoading } = usePrompt(id!)
  const { data: versions } = usePromptVersions(id!)
  const renderPrompt = useRenderPrompt()
  const { model, temperature, setModel, setTemperature } = usePlaygroundStore()
  const [variables, setVariables] = useState<Record<string, string>>({})
  const [output, setOutput] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<{ latency: number; tokens: number; cost: number } | null>(null)

  const latestVersion = versions?.[0]

  if (isLoading) return <LoadingSkeleton />

  const handleRun = async () => {
    if (!id || !latestVersion) return
    const start = Date.now()
    const result = await renderPrompt.mutateAsync({
      templateId: id,
      versionNum: latestVersion.version_number,
      variables,
      model,
      temperature,
    })
    setOutput(result.output)
    setMetrics({ latency: Date.now() - start, tokens: result.tokens ?? 0, cost: result.cost ?? 0 })
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Playground — ${template?.name ?? 'Prompt'}`}
        description="Test prompt with variable inputs and model settings"
      />

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 space-y-4">
          <Card>
            <CardHeader><CardTitle className="text-sm">Template Preview</CardTitle></CardHeader>
            <CardContent>
              <PromptEditor value={latestVersion?.content ?? ''} onChange={() => {}} />
            </CardContent>
          </Card>

          {latestVersion?.variables && Object.keys(latestVersion.variables).length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-sm">Variables</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {Object.keys(latestVersion.variables).map((key) => (
                  <div key={key}>
                    <label className="text-sm font-medium">{`{{${key}}}`}</label>
                    <input
                      className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
                      value={variables[key] ?? ''}
                      onChange={(e) => setVariables((v) => ({ ...v, [key]: e.target.value }))}
                    />
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {output && (
            <Card>
              <CardHeader><CardTitle className="text-sm">Output</CardTitle></CardHeader>
              <CardContent>
                <pre className="whitespace-pre-wrap rounded-md bg-muted p-4 text-sm">{output}</pre>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle className="text-sm">Settings</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="text-sm font-medium">Model</label>
                <select className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={model} onChange={(e) => setModel(e.target.value)}>
                  <option value="gpt-4o">gpt-4o</option>
                  <option value="gpt-4o-mini">gpt-4o-mini</option>
                  <option value="claude-3.5-sonnet">claude-3.5-sonnet</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Temperature: {temperature}</label>
                <input type="range" min={0} max={2} step={0.1} value={temperature} onChange={(e) => setTemperature(Number(e.target.value))} className="mt-1 w-full" />
              </div>
              <Button className="w-full" onClick={handleRun} disabled={renderPrompt.isPending}>
                <Play className="mr-2 h-4 w-4" />{renderPrompt.isPending ? 'Running...' : 'Run'}
              </Button>
            </CardContent>
          </Card>

          {metrics && (
            <div className="space-y-3">
              <MetricCard title="Latency" value={`${metrics.latency}ms`} icon={<Clock className="h-4 w-4" />} />
              <MetricCard title="Tokens" value={String(metrics.tokens)} icon={<Hash className="h-4 w-4" />} />
              <MetricCard title="Cost" value={`$${metrics.cost.toFixed(4)}`} icon={<Coins className="h-4 w-4" />} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

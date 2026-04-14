import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useCreateExperiment } from '@/hooks/use-experiments'
import { Plus, Trash2 } from 'lucide-react'

interface Variant {
  name: string
  prompt_version_id: string
  traffic_percentage: number
}

export default function ExperimentCreate() {
  const navigate = useNavigate()
  const createExperiment = useCreateExperiment()
  const [name, setName] = useState('')
  const [appId, setAppId] = useState('')
  const [variants, setVariants] = useState<Variant[]>([
    { name: 'Control', prompt_version_id: '', traffic_percentage: 50 },
    { name: 'Variant B', prompt_version_id: '', traffic_percentage: 50 },
  ])

  const updateVariant = (idx: number, patch: Partial<Variant>) => {
    setVariants((vs) => vs.map((v, i) => (i === idx ? { ...v, ...patch } : v)))
  }

  const addVariant = () => {
    const remaining = 100 - variants.reduce((s, v) => s + v.traffic_percentage, 0)
    setVariants((vs) => [...vs, { name: `Variant ${String.fromCharCode(65 + vs.length)}`, prompt_version_id: '', traffic_percentage: Math.max(0, remaining) }])
  }

  const removeVariant = (idx: number) => setVariants((vs) => vs.filter((_, i) => i !== idx))

  const totalTraffic = variants.reduce((s, v) => s + v.traffic_percentage, 0)

  const handleSubmit = async () => {
    const result = await createExperiment.mutateAsync({ name, app_id: appId, variants })
    navigate(`/experiments/${result.id}`)
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Create Experiment" description="Set up a new A/B test experiment" />

      <div className="max-w-2xl space-y-4">
        <Card>
          <CardHeader><CardTitle className="text-sm">Basic Info</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="text-sm font-medium">Experiment Name</label>
              <input className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g., Improved system prompt test" />
            </div>
            <div>
              <label className="text-sm font-medium">Application ID</label>
              <input className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={appId} onChange={(e) => setAppId(e.target.value)} placeholder="app-xxx" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm">Variants</CardTitle>
            <Button size="sm" variant="outline" onClick={addVariant}><Plus className="mr-1 h-3 w-3" />Add</Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {variants.map((v, i) => (
              <div key={i} className="flex items-end gap-3 rounded-md border p-3">
                <div className="flex-1">
                  <label className="text-xs font-medium">Name</label>
                  <input className="mt-1 w-full rounded-md border px-2 py-1.5 text-sm" value={v.name} onChange={(e) => updateVariant(i, { name: e.target.value })} />
                </div>
                <div className="flex-1">
                  <label className="text-xs font-medium">Prompt Version ID</label>
                  <input className="mt-1 w-full rounded-md border px-2 py-1.5 text-sm" value={v.prompt_version_id} onChange={(e) => updateVariant(i, { prompt_version_id: e.target.value })} />
                </div>
                <div className="w-24">
                  <label className="text-xs font-medium">Traffic %</label>
                  <input type="number" min={0} max={100} className="mt-1 w-full rounded-md border px-2 py-1.5 text-sm" value={v.traffic_percentage} onChange={(e) => updateVariant(i, { traffic_percentage: Number(e.target.value) })} />
                </div>
                {variants.length > 2 && (
                  <Button size="sm" variant="ghost" onClick={() => removeVariant(i)}><Trash2 className="h-4 w-4 text-destructive" /></Button>
                )}
              </div>
            ))}
            {totalTraffic !== 100 && <p className="text-sm text-destructive">Traffic must sum to 100% (currently {totalTraffic}%)</p>}
          </CardContent>
        </Card>

        <Button onClick={handleSubmit} disabled={!name || !appId || totalTraffic !== 100 || createExperiment.isPending}>
          {createExperiment.isPending ? 'Creating...' : 'Create Experiment'}
        </Button>
      </div>
    </div>
  )
}

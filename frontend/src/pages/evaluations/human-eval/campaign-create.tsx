import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useCreateCampaign, useEvalDatasets } from '@/hooks/use-evaluations'

export default function CampaignCreate() {
  const navigate = useNavigate()
  const createCampaign = useCreateCampaign()
  const { data: datasets } = useEvalDatasets()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [datasetId, setDatasetId] = useState('')
  const [reviewerEmails, setReviewerEmails] = useState('')
  const [blindMode, setBlindMode] = useState(true)

  const handleSubmit = async () => {
    const result = await createCampaign.mutateAsync({
      name,
      description,
      dataset_id: datasetId,
      reviewer_emails: reviewerEmails.split(',').map((e) => e.trim()).filter(Boolean),
      blind_mode: blindMode,
    })
    navigate(`/evaluations/human-eval/${result.id}`)
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Create Human Eval Campaign" description="Set up a new human evaluation campaign" />

      <div className="max-w-2xl space-y-4">
        <Card>
          <CardHeader><CardTitle className="text-sm">Campaign Details</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="text-sm font-medium">Campaign Name</label>
              <input className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={name} onChange={(e) => setName(e.target.value)} placeholder="Q1 Quality Review" />
            </div>
            <div>
              <label className="text-sm font-medium">Description</label>
              <textarea className="mt-1 w-full rounded-md border px-3 py-2 text-sm" rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium">Evaluation Dataset</label>
              <select className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
                <option value="">Select dataset...</option>
                {datasets?.map((d: { id: string; name: string }) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium">Reviewer Emails (comma-separated)</label>
              <input className="mt-1 w-full rounded-md border px-3 py-2 text-sm" value={reviewerEmails} onChange={(e) => setReviewerEmails(e.target.value)} placeholder="alice@co.com, bob@co.com" />
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="blind" checked={blindMode} onChange={(e) => setBlindMode(e.target.checked)} />
              <label htmlFor="blind" className="text-sm font-medium">Blind evaluation (hide model/version info)</label>
            </div>
          </CardContent>
        </Card>

        <Button onClick={handleSubmit} disabled={!name || !datasetId || createCampaign.isPending}>
          {createCampaign.isPending ? 'Creating...' : 'Create Campaign'}
        </Button>
      </div>
    </div>
  )
}

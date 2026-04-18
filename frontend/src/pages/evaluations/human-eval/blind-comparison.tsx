import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useHumanEvalCampaign, useSubmitRating } from '@/hooks/use-evaluations'
import { ThumbsUp, Send } from 'lucide-react'

export default function BlindComparison() {
  const { campaignId, itemId } = useParams<{ campaignId: string; itemId: string }>()
  const { data: campaign, isLoading } = useHumanEvalCampaign(campaignId)
  const submitRating = useSubmitRating()
  const [selected, setSelected] = useState<'A' | 'B' | 'tie' | null>(null)
  const [comment, setComment] = useState('')

  if (isLoading) return <LoadingSkeleton />

  const currentItem = campaign?.items?.find((i) => i.id === itemId)
  const progressPct = campaign?.total_items ? (((campaign.completed_items ?? 0) / campaign.total_items) * 100).toFixed(0) : '0'

  const handleSubmit = async () => {
    if (!selected) return
    await submitRating.mutateAsync({ campaignId: campaignId!, itemId: itemId!, ratings: { preference: selected }, comment })
    setSelected(null)
    setComment('')
  }

  return (
    <div className="mx-auto max-w-4xl py-8 px-4">
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Blind Comparison</h1>
        <div className="mt-2 flex items-center gap-3">
          <div className="flex-1 rounded-full bg-muted h-2">
            <div className="h-2 rounded-full bg-primary transition-all" style={{ width: `${progressPct}%` }} />
          </div>
          <span className="text-sm text-muted-foreground">{progressPct}%</span>
        </div>
      </div>

      <Card className="mb-6">
        <CardHeader><CardTitle className="text-sm">Prompt</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm bg-muted rounded-md p-3">{currentItem?.input ?? 'Loading...'}</p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <Card className={`cursor-pointer transition-all ${selected === 'A' ? 'ring-2 ring-primary' : ''}`} onClick={() => setSelected('A')}>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm">Response A</CardTitle>
            {selected === 'A' && <ThumbsUp className="h-4 w-4 text-primary" />}
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm">{currentItem?.output_a ?? 'Loading...'}</p>
          </CardContent>
        </Card>

        <Card className={`cursor-pointer transition-all ${selected === 'B' ? 'ring-2 ring-primary' : ''}`} onClick={() => setSelected('B')}>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm">Response B</CardTitle>
            {selected === 'B' && <ThumbsUp className="h-4 w-4 text-primary" />}
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap text-sm">{currentItem?.output_b ?? 'Loading...'}</p>
          </CardContent>
        </Card>
      </div>

      <div className="mb-6 flex items-center justify-center">
        <Button variant={selected === 'tie' ? 'default' : 'outline'} onClick={() => setSelected('tie')}>It's a tie</Button>
      </div>

      <div className="mb-4">
        <label className="text-sm font-medium">Comment (optional)</label>
        <textarea className="mt-1 w-full rounded-md border px-3 py-2 text-sm" rows={2} value={comment} onChange={(e) => setComment(e.target.value)} />
      </div>

      <div className="flex justify-end">
        <Button onClick={handleSubmit} disabled={!selected || submitRating.isPending}>
          <Send className="mr-2 h-4 w-4" />{submitRating.isPending ? 'Submitting...' : 'Submit & Next'}
        </Button>
      </div>
    </div>
  )
}

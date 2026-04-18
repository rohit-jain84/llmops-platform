import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import LoadingSkeleton from '@/components/common/loading-skeleton'
import { useHumanEvalCampaign, useSubmitRating } from '@/hooks/use-evaluations'
import { Send, ChevronRight } from 'lucide-react'

const RATING_CRITERIA = [
  { key: 'relevance', label: 'Relevance', description: 'How relevant is the response?' },
  { key: 'coherence', label: 'Coherence', description: 'Is the response well-structured?' },
  { key: 'accuracy', label: 'Accuracy', description: 'Is the information correct?' },
  { key: 'helpfulness', label: 'Helpfulness', description: 'Does it address the query?' },
]

export default function RatingInterface() {
  const { campaignId, itemId } = useParams<{ campaignId: string; itemId: string }>()
  const { data: campaign, isLoading } = useHumanEvalCampaign(campaignId)
  const submitRating = useSubmitRating()
  const [ratings, setRatings] = useState<Record<string, number>>({})
  const [comment, setComment] = useState('')

  if (isLoading) return <LoadingSkeleton />

  const currentItem = campaign?.items?.find((i) => i.id === itemId)
  const progressPct = campaign?.total_items ? (((campaign.completed_items ?? 0) / campaign.total_items) * 100).toFixed(0) : '0'

  const handleSubmit = async () => {
    await submitRating.mutateAsync({ campaignId: campaignId!, itemId: itemId!, ratings, comment })
    setRatings({})
    setComment('')
  }

  return (
    <div className="mx-auto max-w-3xl py-8 px-4">
      <div className="mb-6">
        <h1 className="text-xl font-semibold">{campaign?.name ?? 'Human Evaluation'}</h1>
        <div className="mt-2 flex items-center gap-3">
          <div className="flex-1 rounded-full bg-muted h-2">
            <div className="h-2 rounded-full bg-primary transition-all" style={{ width: `${progressPct}%` }} />
          </div>
          <span className="text-sm text-muted-foreground">{progressPct}% complete</span>
        </div>
      </div>

      <Card className="mb-6">
        <CardHeader><CardTitle className="text-sm">Prompt</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm bg-muted rounded-md p-3">{currentItem?.input ?? 'Loading...'}</p>
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader><CardTitle className="text-sm">Response</CardTitle></CardHeader>
        <CardContent>
          <p className="whitespace-pre-wrap text-sm">{currentItem?.output ?? 'Loading...'}</p>
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader><CardTitle className="text-sm">Rate this response</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {RATING_CRITERIA.map((c) => (
            <div key={c.key}>
              <div className="flex items-center justify-between mb-1">
                <label className="text-sm font-medium">{c.label}</label>
                <span className="text-xs text-muted-foreground">{c.description}</span>
              </div>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    className={`h-10 w-10 rounded-md border text-sm font-medium transition-colors ${ratings[c.key] === n ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}`}
                    onClick={() => setRatings((r) => ({ ...r, [c.key]: n }))}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
          ))}
          <div>
            <label className="text-sm font-medium">Comment (optional)</label>
            <textarea className="mt-1 w-full rounded-md border px-3 py-2 text-sm" rows={2} value={comment} onChange={(e) => setComment(e.target.value)} />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button onClick={handleSubmit} disabled={Object.keys(ratings).length < RATING_CRITERIA.length || submitRating.isPending}>
          <Send className="mr-2 h-4 w-4" />{submitRating.isPending ? 'Submitting...' : 'Submit & Next'}
          <ChevronRight className="ml-1 h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

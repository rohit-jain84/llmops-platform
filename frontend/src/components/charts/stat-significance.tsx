import { cn } from '@/lib/utils'

interface StatSignificanceProps {
  pValue: number | null
  threshold?: number
}

export default function StatSignificance({ pValue, threshold = 0.05 }: StatSignificanceProps) {
  if (pValue === null) {
    return <span className="text-sm text-muted-foreground">Not enough data</span>
  }

  const isSignificant = pValue < threshold

  return (
    <div className="flex items-center gap-2">
      <div className={cn(
        'h-2 w-2 rounded-full',
        isSignificant ? 'bg-green-500' : 'bg-yellow-500'
      )} />
      <span className="text-sm font-medium">
        p = {pValue.toFixed(4)}
      </span>
      <span className={cn(
        'text-xs',
        isSignificant ? 'text-green-600' : 'text-yellow-600'
      )}>
        {isSignificant ? 'Statistically significant' : 'Not yet significant'}
      </span>
    </div>
  )
}

import { Inbox } from 'lucide-react'

interface EmptyStateProps {
  title: string
  description?: string
  action?: React.ReactNode
  icon?: React.ReactNode
}

export default function EmptyState({ title, description, action, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      {icon ? <div className="text-muted-foreground/50">{icon}</div> : <Inbox className="h-12 w-12 text-muted-foreground/50" />}
      <h3 className="mt-4 text-lg font-semibold">{title}</h3>
      {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

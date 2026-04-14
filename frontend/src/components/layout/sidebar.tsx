import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useUIStore } from '@/stores/ui-store'
import {
  LayoutDashboard,
  MessageSquare,
  FlaskConical,
  ClipboardCheck,
  DollarSign,
  Activity,
  Rocket,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/prompts', label: 'Prompts', icon: MessageSquare },
  { path: '/experiments', label: 'Experiments', icon: FlaskConical },
  { path: '/evaluations', label: 'Evaluations', icon: ClipboardCheck },
  { path: '/cost', label: 'Cost & Usage', icon: DollarSign },
  { path: '/observability', label: 'Observability', icon: Activity },
  { path: '/deployments', label: 'Deployments', icon: Rocket },
]

export default function Sidebar() {
  const location = useLocation()
  const { sidebarCollapsed, toggleSidebar } = useUIStore()

  return (
    <aside className={cn(
      'flex flex-col border-r bg-card transition-all duration-300',
      sidebarCollapsed ? 'w-16' : 'w-64'
    )}>
      <div className="flex h-16 items-center justify-between border-b px-4">
        {!sidebarCollapsed && (
          <h1 className="text-lg font-bold text-primary">LLMOps</h1>
        )}
        <button onClick={toggleSidebar} className="rounded-md p-1.5 hover:bg-muted">
          {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>
      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path ||
            (item.path !== '/' && location.pathname.startsWith(item.path))
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {!sidebarCollapsed && <span>{item.label}</span>}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}

import { useCurrentUser, useLogout } from '@/hooks/use-auth'
import { useTheme } from '@/context/ThemeContext'
import { Button } from '@/components/ui/button'
import { LogOut, User, Sun, Moon } from 'lucide-react'

export default function Header() {
  const { data: user } = useCurrentUser()
  const logout = useLogout()
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      <div />
      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <User className="h-4 w-4" />
            <span>{user.email}</span>
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs">{user.role}</span>
          </div>
        )}
        <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
        <Button variant="ghost" size="sm" onClick={logout}>
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}

import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Sidebar from '@/components/layout/sidebar'
import { useUIStore } from '@/stores/ui-store'

function renderSidebar(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Sidebar />
    </MemoryRouter>
  )
}

describe('Sidebar', () => {
  beforeEach(() => {
    // Reset sidebar to expanded
    if (useUIStore.getState().sidebarCollapsed) {
      useUIStore.getState().toggleSidebar()
    }
  })

  it('renders all nav items when expanded', () => {
    renderSidebar()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Prompts')).toBeInTheDocument()
    expect(screen.getByText('Experiments')).toBeInTheDocument()
    expect(screen.getByText('Evaluations')).toBeInTheDocument()
    expect(screen.getByText('Cost & Usage')).toBeInTheDocument()
    expect(screen.getByText('Observability')).toBeInTheDocument()
    expect(screen.getByText('Deployments')).toBeInTheDocument()
  })

  it('shows LLMOps title when expanded', () => {
    renderSidebar()
    expect(screen.getByText('LLMOps')).toBeInTheDocument()
  })

  it('hides labels when collapsed', () => {
    useUIStore.getState().toggleSidebar()
    renderSidebar()
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument()
    expect(screen.queryByText('Prompts')).not.toBeInTheDocument()
    expect(screen.queryByText('LLMOps')).not.toBeInTheDocument()
  })

  it('highlights active route', () => {
    renderSidebar('/prompts')
    const promptsLink = screen.getByText('Prompts').closest('a')
    expect(promptsLink?.className).toContain('bg-primary')
  })

  it('highlights nested routes', () => {
    renderSidebar('/cost/analytics')
    const costLink = screen.getByText('Cost & Usage').closest('a')
    expect(costLink?.className).toContain('bg-primary')
  })

  it('does not highlight non-matching routes', () => {
    renderSidebar('/prompts')
    const dashboardLink = screen.getByText('Dashboard').closest('a')
    expect(dashboardLink?.className).not.toContain('bg-primary')
  })

  it('toggles collapse on button click', () => {
    renderSidebar()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()

    const toggleBtn = screen.getByRole('button')
    fireEvent.click(toggleBtn)

    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument()
  })
})

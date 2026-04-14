import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DataTable } from '@/components/ui/data-table'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

describe('DataTable', () => {
  const columns = [
    { key: 'name', header: 'Name' },
    { key: 'status', header: 'Status' },
  ]

  const data = [
    { name: 'Item 1', status: 'active' },
    { name: 'Item 2', status: 'inactive' },
    { name: 'Item 3', status: 'active' },
  ]

  it('renders column headers', () => {
    render(<DataTable columns={columns} data={data} />)
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
  })

  it('renders all rows', () => {
    render(<DataTable columns={columns} data={data} />)
    expect(screen.getByText('Item 1')).toBeInTheDocument()
    expect(screen.getByText('Item 2')).toBeInTheDocument()
    expect(screen.getByText('Item 3')).toBeInTheDocument()
  })

  it('shows empty message when data is empty', () => {
    render(<DataTable columns={columns} data={[]} emptyMessage="Nothing here" />)
    expect(screen.getByText('Nothing here')).toBeInTheDocument()
  })

  it('shows default empty message', () => {
    render(<DataTable columns={columns} data={[]} />)
    expect(screen.getByText('No data available')).toBeInTheDocument()
  })

  it('calls onRowClick when clicking a row', () => {
    const onClick = vi.fn()
    render(<DataTable columns={columns} data={data} onRowClick={onClick} />)
    fireEvent.click(screen.getByText('Item 2'))
    expect(onClick).toHaveBeenCalledWith(data[1])
  })

  it('renders custom cell content via render function', () => {
    const columnsWithRender = [
      { key: 'name', header: 'Name' },
      {
        key: 'status',
        header: 'Status',
        render: (item: { name: string; status: string }) => (
          <span data-testid="custom">{item.status.toUpperCase()}</span>
        ),
      },
    ]
    render(<DataTable columns={columnsWithRender} data={data} />)
    const customCells = screen.getAllByTestId('custom')
    expect(customCells[0]).toHaveTextContent('ACTIVE')
    expect(customCells[1]).toHaveTextContent('INACTIVE')
  })
})

describe('Badge', () => {
  it('renders with default variant', () => {
    render(<Badge>Default</Badge>)
    expect(screen.getByText('Default')).toBeInTheDocument()
  })

  it('renders with success variant', () => {
    render(<Badge variant="success">Passed</Badge>)
    const badge = screen.getByText('Passed')
    expect(badge).toBeInTheDocument()
    expect(badge.className).toContain('bg-green')
  })

  it('renders with destructive variant', () => {
    render(<Badge variant="destructive">Failed</Badge>)
    const badge = screen.getByText('Failed')
    expect(badge.className).toContain('bg-destructive')
  })

  it('renders with info variant', () => {
    render(<Badge variant="info">v1</Badge>)
    const badge = screen.getByText('v1')
    expect(badge.className).toContain('bg-blue')
  })
})

describe('Card', () => {
  it('renders card with header and content', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Test Title</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Card body text</p>
        </CardContent>
      </Card>
    )
    expect(screen.getByText('Test Title')).toBeInTheDocument()
    expect(screen.getByText('Card body text')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<Card data-testid="card" className="border-red-500">Content</Card>)
    const card = screen.getByTestId('card')
    expect(card.className).toContain('border-red-500')
    expect(card.className).toContain('rounded-lg')
  })
})

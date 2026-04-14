import { describe, it, expect } from 'vitest'
import { cn, formatCurrency, formatNumber, formatDuration } from '@/lib/utils'

describe('cn (class merge)', () => {
  it('merges simple classes', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('handles conditional classes', () => {
    expect(cn('base', false && 'hidden', 'extra')).toBe('base extra')
  })

  it('resolves tailwind conflicts', () => {
    const result = cn('px-4', 'px-6')
    expect(result).toBe('px-6')
  })

  it('handles undefined and null', () => {
    expect(cn('a', undefined, null, 'b')).toBe('a b')
  })
})

describe('formatCurrency', () => {
  it('formats positive amounts', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56')
  })

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00')
  })

  it('formats small amounts', () => {
    const result = formatCurrency(0.01)
    expect(result).toBe('$0.01')
  })
})

describe('formatNumber', () => {
  it('formats with commas', () => {
    expect(formatNumber(1000000)).toBe('1,000,000')
  })

  it('handles zero', () => {
    expect(formatNumber(0)).toBe('0')
  })
})

describe('formatDuration', () => {
  it('formats milliseconds under 1s', () => {
    expect(formatDuration(500)).toBe('500ms')
  })

  it('formats seconds', () => {
    expect(formatDuration(2500)).toBe('2.50s')
  })

  it('formats exactly 1 second', () => {
    expect(formatDuration(1000)).toBe('1.00s')
  })
})

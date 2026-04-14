import { describe, it, expect, beforeEach } from 'vitest'
import { usePlaygroundStore } from '@/stores/playground-store'
import { useUIStore } from '@/stores/ui-store'

describe('PlaygroundStore', () => {
  beforeEach(() => {
    usePlaygroundStore.getState().reset()
  })

  it('has correct initial state', () => {
    const state = usePlaygroundStore.getState()
    expect(state.model).toBe('gpt-4o-mini')
    expect(state.temperature).toBe(0.7)
    expect(state.maxTokens).toBe(1024)
    expect(state.variables).toEqual({})
  })

  it('updates model', () => {
    usePlaygroundStore.getState().setModel('gpt-4o')
    expect(usePlaygroundStore.getState().model).toBe('gpt-4o')
  })

  it('updates temperature', () => {
    usePlaygroundStore.getState().setTemperature(0.3)
    expect(usePlaygroundStore.getState().temperature).toBe(0.3)
  })

  it('updates maxTokens', () => {
    usePlaygroundStore.getState().setMaxTokens(2048)
    expect(usePlaygroundStore.getState().maxTokens).toBe(2048)
  })

  it('sets individual variable', () => {
    usePlaygroundStore.getState().setVariable('name', 'Alice')
    usePlaygroundStore.getState().setVariable('role', 'Engineer')
    const vars = usePlaygroundStore.getState().variables
    expect(vars).toEqual({ name: 'Alice', role: 'Engineer' })
  })

  it('replaces all variables', () => {
    usePlaygroundStore.getState().setVariable('old', 'value')
    usePlaygroundStore.getState().setVariables({ new: 'vars' })
    expect(usePlaygroundStore.getState().variables).toEqual({ new: 'vars' })
  })

  it('resets to defaults', () => {
    usePlaygroundStore.getState().setModel('gpt-4o')
    usePlaygroundStore.getState().setTemperature(0.1)
    usePlaygroundStore.getState().setMaxTokens(4096)
    usePlaygroundStore.getState().setVariable('x', 'y')
    usePlaygroundStore.getState().reset()

    const state = usePlaygroundStore.getState()
    expect(state.model).toBe('gpt-4o-mini')
    expect(state.temperature).toBe(0.7)
    expect(state.maxTokens).toBe(1024)
    expect(state.variables).toEqual({})
  })
})

describe('UIStore', () => {
  it('starts with sidebar expanded', () => {
    expect(useUIStore.getState().sidebarCollapsed).toBe(false)
  })

  it('toggles sidebar', () => {
    useUIStore.getState().toggleSidebar()
    expect(useUIStore.getState().sidebarCollapsed).toBe(true)
    useUIStore.getState().toggleSidebar()
    expect(useUIStore.getState().sidebarCollapsed).toBe(false)
  })
})

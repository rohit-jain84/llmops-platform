import { create } from 'zustand'

interface PlaygroundState {
  model: string
  temperature: number
  maxTokens: number
  variables: Record<string, string>
  setModel: (model: string) => void
  setTemperature: (temp: number) => void
  setMaxTokens: (tokens: number) => void
  setVariable: (key: string, value: string) => void
  setVariables: (vars: Record<string, string>) => void
  reset: () => void
}

export const usePlaygroundStore = create<PlaygroundState>((set) => ({
  model: 'gpt-4o-mini',
  temperature: 0.7,
  maxTokens: 1024,
  variables: {},
  setModel: (model) => set({ model }),
  setTemperature: (temperature) => set({ temperature }),
  setMaxTokens: (maxTokens) => set({ maxTokens }),
  setVariable: (key, value) => set((s) => ({ variables: { ...s.variables, [key]: value } })),
  setVariables: (variables) => set({ variables }),
  reset: () => set({ model: 'gpt-4o-mini', temperature: 0.7, maxTokens: 1024, variables: {} }),
}))

import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'

// Mock axios before importing client
vi.mock('axios', () => {
  const interceptors = {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  }
  const instance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors,
    defaults: { headers: { common: {} } },
  }
  return {
    default: {
      create: vi.fn(() => instance),
    },
  }
})

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('creates axios instance with correct base URL', async () => {
    // Re-import to trigger module execution
    vi.resetModules()
    await import('@/api/client')

    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        baseURL: '/api/v1',
        headers: { 'Content-Type': 'application/json' },
      })
    )
  })

  it('registers request and response interceptors', async () => {
    vi.resetModules()
    await import('@/api/client')

    const instance = (axios.create as ReturnType<typeof vi.fn>).mock.results[0]?.value
    expect(instance.interceptors.request.use).toHaveBeenCalled()
    expect(instance.interceptors.response.use).toHaveBeenCalled()
  })
})

describe('Prompts API', () => {
  it('exports expected methods', async () => {
    const { promptsApi } = await import('@/api/prompts')
    expect(promptsApi.list).toBeDefined()
    expect(promptsApi.get).toBeDefined()
    expect(promptsApi.create).toBeDefined()
    expect(promptsApi.listVersions).toBeDefined()
    expect(promptsApi.createVersion).toBeDefined()
    expect(promptsApi.tagVersion).toBeDefined()
    expect(promptsApi.rollback).toBeDefined()
    expect(promptsApi.diff).toBeDefined()
    expect(promptsApi.diffDetailed).toBeDefined()
    expect(promptsApi.render).toBeDefined()
  })
})

describe('Evaluations API', () => {
  it('exports expected methods including regression check', async () => {
    const { evaluationsApi } = await import('@/api/evaluations')
    expect(evaluationsApi.listDatasets).toBeDefined()
    expect(evaluationsApi.createDataset).toBeDefined()
    expect(evaluationsApi.addItems).toBeDefined()
    expect(evaluationsApi.triggerRun).toBeDefined()
    expect(evaluationsApi.getRun).toBeDefined()
    expect(evaluationsApi.getRunResults).toBeDefined()
    expect(evaluationsApi.checkRegression).toBeDefined()
  })
})

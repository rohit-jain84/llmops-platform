import apiClient from './client'
import type { Experiment, ExperimentResultSummary } from './types'

type VariantCreate = {
  prompt_version_id: string
  traffic_pct?: number
  label?: string
  name?: string
  traffic_percentage?: number
}

export const experimentsApi = {
  list: (applicationId?: string) =>
    apiClient.get<Experiment[]>('/experiments', { params: applicationId ? { application_id: applicationId } : {} }).then(r => r.data),
  create: (data: { application_id?: string; app_id?: string; name: string; variants: VariantCreate[] }) =>
    apiClient.post<Experiment>('/experiments', data).then(r => r.data),
  get: (id: string) =>
    apiClient.get<Experiment>(`/experiments/${id}`).then(r => r.data),
  start: (id: string) =>
    apiClient.post<Experiment>(`/experiments/${id}/start`).then(r => r.data),
  stop: (id: string) =>
    apiClient.post<Experiment>(`/experiments/${id}/stop`).then(r => r.data),
  getResults: (id: string) =>
    apiClient.get<ExperimentResultSummary>(`/experiments/${id}/results`).then(r => r.data),
  promoteWinner: (id: string, variantId?: string) =>
    apiClient.post<Experiment>(`/experiments/${id}/promote-winner`, variantId ? { variant_id: variantId } : undefined).then(r => r.data),
}

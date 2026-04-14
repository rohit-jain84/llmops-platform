import apiClient from './client'
import type { Deployment } from './types'

export const deploymentsApi = {
  list: (applicationId?: string) =>
    apiClient.get<Deployment[]>('/deployments', { params: applicationId ? { application_id: applicationId } : {} }).then(r => r.data),
  create: (data: { prompt_version_id: string; canary_pct?: number }) =>
    apiClient.post<Deployment>('/deployments', data).then(r => r.data),
  get: (id: string) =>
    apiClient.get<Deployment>(`/deployments/${id}`).then(r => r.data),
  promote: (id: string) =>
    apiClient.post<Deployment>(`/deployments/${id}/promote`).then(r => r.data),
  rollback: (id: string) =>
    apiClient.post<Deployment>(`/deployments/${id}/rollback`).then(r => r.data),
}

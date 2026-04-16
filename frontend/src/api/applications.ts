import apiClient from './client'
import type { Application } from './types'

export const applicationsApi = {
  list: () =>
    apiClient.get<Application[]>('/applications').then(r => r.data),
  get: (id: string) =>
    apiClient.get<Application>(`/applications/${id}`).then(r => r.data),
  create: (data: { name: string; description?: string }) =>
    apiClient.post<Application>('/applications', data).then(r => r.data),
}

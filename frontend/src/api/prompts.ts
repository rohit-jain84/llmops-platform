import apiClient from './client'
import type { PromptTemplate, PromptVersion, PromptDiffDetailed } from './types'

export const promptsApi = {
  list: (applicationId: string) =>
    apiClient.get<PromptTemplate[]>(`/applications/${applicationId}/prompts`).then(r => r.data),
  get: (templateId: string) =>
    apiClient.get<PromptTemplate>(`/prompts/${templateId}`).then(r => r.data),
  create: (applicationId: string, data: { name: string; description?: string }) =>
    apiClient.post<PromptTemplate>(`/applications/${applicationId}/prompts`, data).then(r => r.data),
  listVersions: (templateId: string) =>
    apiClient.get<PromptVersion[]>(`/prompts/${templateId}/versions`).then(r => r.data),
  createVersion: (templateId: string, data: { content: string; variables?: Record<string, string>; model_config_data?: Record<string, unknown>; tag?: string; commit_message?: string }) =>
    apiClient.post<PromptVersion>(`/prompts/${templateId}/versions`, data).then(r => r.data),
  getVersion: (templateId: string, num: number) =>
    apiClient.get<PromptVersion>(`/prompts/${templateId}/versions/${num}`).then(r => r.data),
  tagVersion: (templateId: string, num: number, tag: string) =>
    apiClient.post<PromptVersion>(`/prompts/${templateId}/versions/${num}/tag`, { tag }).then(r => r.data),
  rollback: (templateId: string, num: number) =>
    apiClient.post<PromptVersion>(`/prompts/${templateId}/versions/${num}/rollback`).then(r => r.data),
  diff: (templateId: string, v1: number, v2: number) =>
    apiClient.get<{ v1: number; v2: number; v1_content: string; v2_content: string }>(`/prompts/${templateId}/diff`, { params: { v1, v2 } }).then(r => r.data),
  diffDetailed: (templateId: string, v1: number, v2: number) =>
    apiClient.get<PromptDiffDetailed>(`/prompts/${templateId}/diff/detailed`, { params: { v1, v2 } }).then(r => r.data),
  render: (templateId: string, variables: Record<string, string>, versionNumber?: number) =>
    apiClient.post<{ rendered: string; version_number: number }>(`/prompts/${templateId}/render`, { variables, version_number: versionNumber }).then(r => r.data),
}

import apiClient from './client'
import type { EvalDataset, EvalRun, EvalResult, HumanEvalCampaign, RegressionCheck } from './types'

export const evaluationsApi = {
  listDatasets: (applicationId?: string) =>
    apiClient.get<EvalDataset[]>('/eval/datasets', { params: applicationId ? { application_id: applicationId } : {} }).then(r => r.data),
  createDataset: (data: { application_id: string; name: string; dataset_type: string; description?: string }) =>
    apiClient.post<EvalDataset>('/eval/datasets', data).then(r => r.data),
  addItems: (datasetId: string, items: Array<{ input_vars: Record<string, string>; expected_output?: string; metadata?: Record<string, unknown> }>) =>
    apiClient.post(`/eval/datasets/${datasetId}/items`, { items }).then(r => r.data),
  triggerRun: (data: { prompt_version_id: string; dataset_id: string; trigger?: string }) =>
    apiClient.post<EvalRun>('/eval/runs', data).then(r => r.data),
  getRun: (runId: string) =>
    apiClient.get<EvalRun>(`/eval/runs/${runId}`).then(r => r.data),
  getRunResults: (runId: string) =>
    apiClient.get<EvalResult[]>(`/eval/runs/${runId}/results`).then(r => r.data),
  createCampaign: (data: { eval_run_id: string; name: string; dimensions: Array<Record<string, unknown>>; evaluator_ids: string[] }) =>
    apiClient.post<HumanEvalCampaign>('/eval/campaigns', data).then(r => r.data),
  getCampaign: (id: string) =>
    apiClient.get<HumanEvalCampaign>(`/eval/campaigns/${id}`).then(r => r.data),
  getAssignments: (campaignId: string, evaluatorId?: string) =>
    apiClient.get(`/eval/campaigns/${campaignId}/assignments`, { params: evaluatorId ? { evaluator_id: evaluatorId } : {} }).then(r => r.data),
  submitRating: (assignmentId: string, data: { ratings: Record<string, number>; notes?: string }) =>
    apiClient.post(`/eval/assignments/${assignmentId}/rate`, data).then(r => r.data),
  checkRegression: (templateId: string, v1?: number, v2?: number, thresholdPct?: number) =>
    apiClient.get<RegressionCheck>(`/eval/regression/${templateId}`, {
      params: { ...(v1 != null && { v1 }), ...(v2 != null && { v2 }), ...(thresholdPct != null && { threshold_pct: thresholdPct }) },
    }).then(r => r.data),
}

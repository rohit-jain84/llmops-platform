import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { evaluationsApi } from '@/api/evaluations'

export function useRegressionCheck(templateId: string, v1?: number, v2?: number) {
  return useQuery({
    queryKey: ['regression', templateId, v1, v2],
    queryFn: () => evaluationsApi.checkRegression(templateId, v1, v2),
    enabled: !!templateId,
    retry: false,
  })
}

export function useEvalDatasets(applicationId?: string) {
  return useQuery({
    queryKey: ['eval-datasets', { applicationId }],
    queryFn: () => evaluationsApi.listDatasets(applicationId),
  })
}

export function useCreateEvalDataset() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: evaluationsApi.createDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['eval-datasets'] })
    },
  })
}

export function useEvalRun(runId: string) {
  return useQuery({
    queryKey: ['eval-runs', runId],
    queryFn: () => evaluationsApi.getRun(runId),
    enabled: !!runId,
    refetchInterval: (query) => {
      const data = query.state.data
      return data?.status === 'running' || data?.status === 'pending' ? 5000 : false
    },
  })
}

export function useEvalResults(runId: string) {
  return useQuery({
    queryKey: ['eval-runs', runId, 'results'],
    queryFn: () => evaluationsApi.getRunResults(runId),
    enabled: !!runId,
  })
}

export function useTriggerEvalRun() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: evaluationsApi.triggerRun,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['eval-runs'] })
    },
  })
}

export function useHumanEvalCampaign(id?: string) {
  return useQuery({
    queryKey: ['eval-campaigns', id],
    queryFn: () => evaluationsApi.getCampaign(id!),
    enabled: !!id,
  })
}

export function useHumanEvalCampaigns(applicationId?: string) {
  return useQuery({
    queryKey: ['eval-campaigns', 'list', { applicationId }],
    queryFn: () => evaluationsApi.listCampaigns(applicationId),
  })
}

export function useCreateCampaign() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: evaluationsApi.createCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['eval-campaigns'] })
    },
  })
}

export function useSubmitRating() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (vars: {
      assignmentId?: string
      campaignId?: string
      itemId?: string
      ratings: Record<string, number | string>
      notes?: string
      comment?: string
    }) => {
      const { assignmentId, campaignId, itemId, ...data } = vars
      const id = assignmentId ?? `${campaignId ?? ''}:${itemId ?? ''}`
      return evaluationsApi.submitRating(id, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['eval-campaigns'] })
    },
  })
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { promptsApi } from '@/api/prompts'

export function usePrompts(applicationId: string) {
  return useQuery({
    queryKey: ['prompts', { applicationId }],
    queryFn: () => promptsApi.list(applicationId),
    enabled: !!applicationId,
  })
}

export function usePrompt(templateId: string) {
  return useQuery({
    queryKey: ['prompts', templateId],
    queryFn: () => promptsApi.get(templateId),
    enabled: !!templateId,
  })
}

export function usePromptVersions(templateId: string) {
  return useQuery({
    queryKey: ['prompts', templateId, 'versions'],
    queryFn: () => promptsApi.listVersions(templateId),
    enabled: !!templateId,
  })
}

export function useCreatePromptVersion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ templateId, ...data }: { templateId: string; content: string; commit_message?: string; tag?: string }) =>
      promptsApi.createVersion(templateId, data),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['prompts', vars.templateId] })
    },
  })
}

export function useTagVersion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ templateId, num, tag }: { templateId: string; num: number; tag: string }) =>
      promptsApi.tagVersion(templateId, num, tag),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['prompts', vars.templateId] })
    },
  })
}

export function useRenderPrompt() {
  return useMutation({
    mutationFn: ({ templateId, variables, versionNumber, versionNum }: { templateId: string; variables: Record<string, string>; versionNumber?: number; versionNum?: number; model?: string; temperature?: number }) =>
      promptsApi.render(templateId, variables, versionNumber ?? versionNum),
  })
}

export function usePromptDiff(templateId: string, v1: number, v2: number) {
  return useQuery({
    queryKey: ['prompts', templateId, 'diff', v1, v2],
    queryFn: () => promptsApi.diff(templateId, v1, v2),
    enabled: !!templateId && v1 > 0 && v2 > 0,
  })
}

export function usePromptDiffDetailed(templateId: string, v1: number, v2: number) {
  return useQuery({
    queryKey: ['prompts', templateId, 'diff-detailed', v1, v2],
    queryFn: () => promptsApi.diffDetailed(templateId, v1, v2),
    enabled: !!templateId && v1 > 0 && v2 > 0,
  })
}

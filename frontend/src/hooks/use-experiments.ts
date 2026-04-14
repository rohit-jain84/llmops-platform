import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { experimentsApi } from '@/api/experiments'

export function useExperiments(applicationId?: string) {
  return useQuery({
    queryKey: ['experiments', { applicationId }],
    queryFn: () => experimentsApi.list(applicationId),
  })
}

export function useExperiment(id: string) {
  return useQuery({
    queryKey: ['experiments', id],
    queryFn: () => experimentsApi.get(id),
    enabled: !!id,
  })
}

export function useExperimentResults(experimentId: string) {
  return useQuery({
    queryKey: ['experiments', experimentId, 'results'],
    queryFn: () => experimentsApi.getResults(experimentId),
    refetchInterval: 5000,
    enabled: !!experimentId,
  })
}

export function useCreateExperiment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: experimentsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiments'] })
    },
  })
}

export function useStartExperiment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => experimentsApi.start(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['experiments', id] })
    },
  })
}

export function useStopExperiment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => experimentsApi.stop(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['experiments', id] })
    },
  })
}

export function usePromoteWinner() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => experimentsApi.promoteWinner(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['experiments', id] })
    },
  })
}

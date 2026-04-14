import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { deploymentsApi } from '@/api/deployments'

export function useDeployments(applicationId?: string) {
  return useQuery({
    queryKey: ['deployments', { applicationId }],
    queryFn: () => deploymentsApi.list(applicationId),
    refetchInterval: 10000,
  })
}

export function useDeployment(id: string) {
  return useQuery({
    queryKey: ['deployments', id],
    queryFn: () => deploymentsApi.get(id),
    enabled: !!id,
    refetchInterval: 10000,
  })
}

export function useCreateDeployment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deploymentsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
  })
}

export function usePromoteDeployment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deploymentsApi.promote(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['deployments', id] })
    },
  })
}

export function useRollbackDeployment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deploymentsApi.rollback(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['deployments', id] })
    },
  })
}

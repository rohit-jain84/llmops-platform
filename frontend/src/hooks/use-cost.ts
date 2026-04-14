import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { costApi } from '@/api/cost'

export function useCostAnalytics(params?: { application_id?: string; date_from?: string; date_to?: string; group_by?: string }) {
  return useQuery({
    queryKey: ['cost', 'analytics', params],
    queryFn: () => costApi.getAnalytics(params),
    refetchInterval: 30000,
  })
}

export function useCostForecast(appId: string) {
  return useQuery({
    queryKey: ['cost', 'forecast', appId],
    queryFn: () => costApi.getForecast(appId),
    enabled: !!appId,
  })
}

export function useBudgetAlerts(applicationId?: string) {
  return useQuery({
    queryKey: ['cost', 'budget-alerts', { applicationId }],
    queryFn: () => costApi.listBudgetAlerts(applicationId),
  })
}

export function useCreateBudgetAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: costApi.createBudgetAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cost', 'budget-alerts'] })
    },
  })
}

import { useQuery } from '@tanstack/react-query'
import { applicationsApi } from '@/api/applications'

export function useApplications() {
  return useQuery({
    queryKey: ['applications'],
    queryFn: () => applicationsApi.list(),
  })
}

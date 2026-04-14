import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/api/client'
import type { User, TokenResponse } from '@/api/types'

export function useCurrentUser() {
  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: () => apiClient.get<User>('/auth/me').then(r => r.data),
    retry: false,
    enabled: !!localStorage.getItem('access_token'),
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      apiClient.post<TokenResponse>('/auth/login', data).then(r => r.data),
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      queryClient.invalidateQueries({ queryKey: ['auth'] })
    },
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: (data: { email: string; password: string; role?: string }) =>
      apiClient.post<User>('/auth/register', data).then(r => r.data),
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    queryClient.clear()
    window.location.href = '/login'
  }
}

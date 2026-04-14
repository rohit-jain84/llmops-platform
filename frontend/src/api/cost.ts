import apiClient from './client'
import type { CostAnalytics, BudgetAlert } from './types'

export const costApi = {
  getAnalytics: (params?: { application_id?: string; date_from?: string; date_to?: string; group_by?: string }) =>
    apiClient.get<CostAnalytics>('/cost/analytics', { params }).then(r => r.data),
  getForecast: (appId: string) =>
    apiClient.get(`/cost/forecast/${appId}`).then(r => r.data),
  createBudgetAlert: (data: { application_id: string; budget_usd: number; period: string; alert_pct: number[] }) =>
    apiClient.post<BudgetAlert>('/cost/budget-alerts', data).then(r => r.data),
  listBudgetAlerts: (applicationId?: string) =>
    apiClient.get<BudgetAlert[]>('/cost/budget-alerts', { params: applicationId ? { application_id: applicationId } : {} }).then(r => r.data),
}

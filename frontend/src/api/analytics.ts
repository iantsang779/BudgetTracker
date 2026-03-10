import client from './client'
import type {
  MetricsResponse,
  SavingsProjectionResponse,
  SpendingByCategoryResponse,
  SpendingOverTimeResponse,
} from '../types'

export async function getMetrics(): Promise<MetricsResponse> {
  const res = await client.get<MetricsResponse>('/analytics/metrics')
  return res.data
}

export async function getSavingsProjection(
  months_ahead?: number,
): Promise<SavingsProjectionResponse> {
  const res = await client.get<SavingsProjectionResponse>('/analytics/savings-projection', {
    params: months_ahead !== undefined ? { months_ahead } : undefined,
  })
  return res.data
}

export async function getSpendingByCategory(
  start_date?: string,
  end_date?: string,
): Promise<SpendingByCategoryResponse> {
  const res = await client.get<SpendingByCategoryResponse>('/analytics/spending-by-category', {
    params: { start_date, end_date },
  })
  return res.data
}

export async function getSpendingOverTime(): Promise<SpendingOverTimeResponse> {
  const res = await client.get<SpendingOverTimeResponse>('/analytics/spending-over-time')
  return res.data
}

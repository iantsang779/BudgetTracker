import client from './client'
import type {
  CumulativeSavingsResponse,
  CumulativeSpendingResponse,
  MetricsResponse,
  SpendingByCategoryResponse,
  SpendingOverTimeResponse,
} from '../types'

export async function getMetrics(): Promise<MetricsResponse> {
  const res = await client.get<MetricsResponse>('/analytics/metrics')
  return res.data
}

export async function getCumulativeSpending(year?: number): Promise<CumulativeSpendingResponse> {
  const res = await client.get<CumulativeSpendingResponse>('/analytics/spending-cumulative', {
    params: year !== undefined ? { year } : undefined,
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

export async function getCumulativeSavings(year?: number): Promise<CumulativeSavingsResponse> {
  const res = await client.get<CumulativeSavingsResponse>('/analytics/savings-cumulative', {
    params: year !== undefined ? { year } : undefined,
  })
  return res.data
}

import { useQuery } from '@tanstack/react-query'
import {
  getMetrics,
  getSavingsProjection,
  getSpendingByCategory,
  getSpendingOverTime,
} from '../api/analytics'

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: getMetrics,
    refetchInterval: 30_000,
  })
}

export function useSavingsProjection(months?: number) {
  return useQuery({
    queryKey: ['savings-projection', months],
    queryFn: () => getSavingsProjection(months),
  })
}

export function useSpendingByCategory(start?: string, end?: string) {
  return useQuery({
    queryKey: ['spending-by-category', start, end],
    queryFn: () => getSpendingByCategory(start, end),
  })
}

export function useSpendingOverTime() {
  return useQuery({
    queryKey: ['spending-over-time'],
    queryFn: getSpendingOverTime,
  })
}

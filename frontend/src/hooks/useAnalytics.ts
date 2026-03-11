import { useQuery } from '@tanstack/react-query'
import {
  getCumulativeSpending,
  getMetrics,
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

export function useCumulativeSpending(year?: number) {
  return useQuery({
    queryKey: ['spending-cumulative', year],
    queryFn: () => getCumulativeSpending(year),
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

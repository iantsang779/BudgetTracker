import { useQuery } from '@tanstack/react-query'
import { convertCurrency } from '../api/currency'

export function useCurrencyRate(targetCurrency: string) {
  return useQuery({
    queryKey: ['currency-rate', targetCurrency],
    queryFn: () => convertCurrency({ amount: 1, from_code: 'USD', to_code: targetCurrency }),
    staleTime: 60 * 60 * 1000, // 1 hour
    enabled: targetCurrency !== 'USD',
  })
}

export function fmtCurrency(amount: number, currency: string): string {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

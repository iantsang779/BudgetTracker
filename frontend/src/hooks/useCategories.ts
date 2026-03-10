import { useQuery } from '@tanstack/react-query'
import { getCategories } from '../api/categories'
import type { CategoryRead } from '../types'

export function useCategories(is_income?: boolean): { data: CategoryRead[] | undefined; isLoading: boolean } {
  return useQuery({
    queryKey: ['categories', is_income],
    queryFn: () => getCategories(is_income),
    staleTime: 5 * 60 * 1000,
  })
}

import { useQuery } from '@tanstack/react-query'
import { getCategories } from '../api/categories'
import type { CategoryRead } from '../types'

export function useCategories(is_income?: boolean): { data: CategoryRead[] | undefined; isLoading: boolean } {
  const query = useQuery({
    queryKey: ['categories', is_income],
    queryFn: () => getCategories(is_income),
    staleTime: 5 * 60 * 1000,
  })

  const data = query.data
    ? [...query.data].sort((a, b) => {
        if (a.name === 'Other') return 1
        if (b.name === 'Other') return -1
        return 0
      })
    : undefined

  return { data, isLoading: query.isLoading }
}

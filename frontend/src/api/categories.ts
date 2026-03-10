import client from './client'
import type { CategoryRead } from '../types'

export async function getCategories(is_income?: boolean): Promise<CategoryRead[]> {
  const res = await client.get<CategoryRead[]>('/categories/', {
    params: is_income !== undefined ? { is_income } : undefined,
  })
  return res.data
}

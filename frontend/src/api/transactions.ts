import client from './client'
import type {
  TransactionCreate,
  TransactionUpdate,
  TransactionRead,
  TransactionFilters,
} from '../types'

export async function getTransactions(filters?: TransactionFilters): Promise<TransactionRead[]> {
  const res = await client.get<TransactionRead[]>('/transactions/', { params: filters })
  return res.data
}

export async function createTransaction(data: TransactionCreate): Promise<TransactionRead> {
  const res = await client.post<TransactionRead>('/transactions/', data)
  return res.data
}

export async function updateTransaction(
  id: number,
  data: TransactionUpdate,
): Promise<TransactionRead> {
  const res = await client.patch<TransactionRead>(`/transactions/${id}`, data)
  return res.data
}

export async function deleteTransaction(id: number): Promise<void> {
  await client.delete(`/transactions/${id}`)
}

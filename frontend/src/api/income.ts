import client from './client'
import type { IncomeCreate, IncomeUpdate, IncomeRead, IncomeSummary } from '../types'

export async function getIncomes(): Promise<IncomeRead[]> {
  const res = await client.get<IncomeRead[]>('/income/')
  return res.data
}

export async function getIncomeSummary(): Promise<IncomeSummary> {
  const res = await client.get<IncomeSummary>('/income/summary')
  return res.data
}

export async function createIncome(data: IncomeCreate): Promise<IncomeRead> {
  const res = await client.post<IncomeRead>('/income/', data)
  return res.data
}

export async function updateIncome(id: number, data: IncomeUpdate): Promise<IncomeRead> {
  const res = await client.patch<IncomeRead>(`/income/${id}`, data)
  return res.data
}

export async function deleteIncome(id: number): Promise<void> {
  await client.delete(`/income/${id}`)
}

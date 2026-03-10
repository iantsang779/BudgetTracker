import client from './client'
import type { AccountCreate, AccountUpdate, AccountRead } from '../types'

export async function getAccounts(): Promise<AccountRead[]> {
  const res = await client.get<AccountRead[]>('/accounts/')
  return res.data
}

export async function createAccount(data: AccountCreate): Promise<AccountRead> {
  const res = await client.post<AccountRead>('/accounts/', data)
  return res.data
}

export async function updateAccount(id: number, data: AccountUpdate): Promise<AccountRead> {
  const res = await client.patch<AccountRead>(`/accounts/${id}`, data)
  return res.data
}

export async function deleteAccount(id: number): Promise<void> {
  await client.delete(`/accounts/${id}`)
}

import client from './client'
import type { CurrencyRateRead, ConvertRequest, ConvertResponse } from '../types'

export async function getRates(): Promise<CurrencyRateRead[]> {
  const res = await client.get<CurrencyRateRead[]>('/currency/rates')
  return res.data
}


export async function refreshRates(): Promise<{ refreshed: number }> {
  const res = await client.post<{ refreshed: number }>('/currency/rates/refresh')
  return res.data
}

export async function convertCurrency(data: ConvertRequest): Promise<ConvertResponse> {
  const res = await client.post<ConvertResponse>('/currency/convert', data)
  return res.data
}

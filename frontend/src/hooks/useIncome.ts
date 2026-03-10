import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getIncomes,
  getIncomeSummary,
  createIncome,
  updateIncome,
  deleteIncome,
} from '../api/income'
import type { IncomeCreate, IncomeUpdate } from '../types'

export function useIncomes() {
  return useQuery({
    queryKey: ['incomes'],
    queryFn: getIncomes,
  })
}

export function useIncomeSummary() {
  return useQuery({
    queryKey: ['income-summary'],
    queryFn: getIncomeSummary,
  })
}

export function useCreateIncome() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: IncomeCreate) => createIncome(data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['incomes'] }),
  })
}

export function useUpdateIncome() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: IncomeUpdate }) => updateIncome(id, data),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['incomes'] }),
  })
}

export function useDeleteIncome() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteIncome(id),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['incomes'] }),
  })
}

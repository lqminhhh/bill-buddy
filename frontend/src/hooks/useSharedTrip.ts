import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/api/client"
import type { CreateExpenseInput, UpdateExpenseInput } from "@/api/types"

const sharedKeys = {
  trip: (token: string) => ["share", token, "trip"] as const,
  expenses: (token: string, filters?: object) =>
    ["share", token, "expenses", filters ?? {}] as const,
  balances: (token: string) => ["share", token, "balances"] as const,
  settlements: (token: string) => ["share", token, "settlements"] as const,
  summary: (token: string) => ["share", token, "summary"] as const,
}

export function useSharedTrip(token: string | undefined) {
  return useQuery({
    queryKey: token ? sharedKeys.trip(token) : ["share", "missing"],
    queryFn: () => api.share.getTrip(token as string),
    enabled: !!token,
  })
}

export function useSharedExpenses(
  token: string | undefined,
  filters?: { payer_id?: number; from?: string; to?: string }
) {
  return useQuery({
    queryKey: token ? sharedKeys.expenses(token, filters) : ["share", "missing-exp"],
    queryFn: () => api.share.listExpenses(token as string, filters),
    enabled: !!token,
  })
}

export function useSharedBalances(token: string | undefined) {
  return useQuery({
    queryKey: token ? sharedKeys.balances(token) : ["share", "missing-bal"],
    queryFn: () => api.share.getBalances(token as string),
    enabled: !!token,
  })
}

export function useSharedSettlements(token: string | undefined) {
  return useQuery({
    queryKey: token ? sharedKeys.settlements(token) : ["share", "missing-set"],
    queryFn: () => api.share.getSettlements(token as string),
    enabled: !!token,
  })
}

function invalidateShare(qc: ReturnType<typeof useQueryClient>, token: string) {
  qc.invalidateQueries({ queryKey: ["share", token] })
}

export function useCreateSharedExpense(token: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateExpenseInput) =>
      api.share.createExpense(token, input),
    onSuccess: () => invalidateShare(qc, token),
  })
}

export function useUpdateSharedExpense(token: string, expenseId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: UpdateExpenseInput) =>
      api.share.updateExpense(token, expenseId, input),
    onSuccess: () => invalidateShare(qc, token),
  })
}

export function useDeleteSharedExpense(token: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (expenseId: number) => api.share.deleteExpense(token, expenseId),
    onSuccess: () => invalidateShare(qc, token),
  })
}

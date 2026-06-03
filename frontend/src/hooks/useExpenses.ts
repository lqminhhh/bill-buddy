import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/api/client"
import { qk } from "@/api/queryKeys"
import type { CreateExpenseInput, UpdateExpenseInput } from "@/api/types"

interface ExpenseFilters {
  payer_id?: number
  from?: string
  to?: string
}

export function useExpenses(tripId: number | undefined, filters?: ExpenseFilters) {
  return useQuery({
    queryKey: [...(tripId ? qk.expenses(tripId) : ["expenses", "missing"]), filters],
    queryFn: () => api.listExpenses(tripId as number, filters),
    enabled: typeof tripId === "number",
  })
}

export function useExpense(expenseId: number | undefined) {
  return useQuery({
    queryKey: expenseId ? qk.expense(expenseId) : ["expense", "missing"],
    queryFn: () => api.getExpense(expenseId as number),
    enabled: typeof expenseId === "number",
  })
}

function invalidateTrip(qc: ReturnType<typeof useQueryClient>, tripId: number) {
  qc.invalidateQueries({ queryKey: qk.expenses(tripId) })
  qc.invalidateQueries({ queryKey: qk.balances(tripId) })
  qc.invalidateQueries({ queryKey: qk.settlements(tripId) })
  qc.invalidateQueries({ queryKey: qk.summary(tripId) })
  qc.invalidateQueries({ queryKey: qk.trip(tripId) })
}

export function useCreateExpense(tripId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateExpenseInput) => api.createExpense(tripId, input),
    onSuccess: () => invalidateTrip(qc, tripId),
  })
}

export function useUpdateExpense(tripId: number, expenseId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: UpdateExpenseInput) => api.updateExpense(expenseId, input),
    onSuccess: () => {
      invalidateTrip(qc, tripId)
      qc.invalidateQueries({ queryKey: qk.expense(expenseId) })
    },
  })
}

export function useDeleteExpense(tripId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (expenseId: number) => api.deleteExpense(expenseId),
    onSuccess: () => invalidateTrip(qc, tripId),
  })
}

import { useNavigate, useParams } from "react-router-dom"
import { toast } from "sonner"

import { ExpenseForm } from "@/components/ExpenseForm"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { extractApiErrorMessage } from "@/hooks/useMembers"
import {
  useSharedExpenses,
  useSharedTrip,
  useUpdateSharedExpense,
} from "@/hooks/useSharedTrip"

export function ShareEditExpensePage() {
  const { token, expenseId } = useParams<{
    token: string
    expenseId: string
  }>()
  const expenseIdNum = expenseId ? Number.parseInt(expenseId, 10) : undefined
  const navigate = useNavigate()
  const { data: trip, isLoading: tripLoading } = useSharedTrip(token)
  const { data: expenses, isLoading: expensesLoading } = useSharedExpenses(token)
  const updateExpense = useUpdateSharedExpense(token ?? "", expenseIdNum ?? -1)

  if (tripLoading || expensesLoading)
    return <Skeleton className="h-72 rounded-2xl" />

  const expense = expenses?.find((e) => e.id === expenseIdNum)
  if (!trip || !expense || !token || expenseIdNum === undefined) {
    return (
      <Card>
        <CardContent className="py-10 text-sm text-muted-foreground">
          Expense not found.
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-primary">
          {trip.name} · shared
        </p>
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          Edit expense
        </h1>
      </div>
      <ExpenseForm
        members={trip.members}
        initial={{
          description: expense.description,
          amountText: (expense.amount_cents / 100).toFixed(2),
          expense_date: expense.expense_date,
          paid_by_member_id: expense.paid_by_member_id,
          participant_ids: expense.participants.map((p) => p.id),
          notes: expense.notes,
        }}
        submitLabel="Save changes"
        pendingLabel="Saving…"
        isPending={updateExpense.isPending}
        onCancel={() => navigate(`/share/${token}`)}
        onSubmit={(values) =>
          updateExpense.mutate(values, {
            onSuccess: () => {
              toast.success("Expense updated")
              navigate(`/share/${token}`)
            },
            onError: (error) =>
              toast.error(
                extractApiErrorMessage(error, "Couldn't update expense")
              ),
          })
        }
      />
    </div>
  )
}

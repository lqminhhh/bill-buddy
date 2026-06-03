import { useNavigate, useParams } from "react-router-dom"
import { toast } from "sonner"

import { ExpenseForm } from "@/components/ExpenseForm"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useExpense, useUpdateExpense } from "@/hooks/useExpenses"
import { extractApiErrorMessage } from "@/hooks/useMembers"
import { useTrip } from "@/hooks/useTrips"

export function EditExpensePage() {
  const { tripId, expenseId } = useParams<{
    tripId: string
    expenseId: string
  }>()
  const tripIdNum = tripId ? Number.parseInt(tripId, 10) : undefined
  const expenseIdNum = expenseId ? Number.parseInt(expenseId, 10) : undefined
  const navigate = useNavigate()

  const { data: trip, isLoading: tripLoading } = useTrip(tripIdNum)
  const { data: expense, isLoading: expenseLoading } = useExpense(expenseIdNum)
  const updateExpense = useUpdateExpense(tripIdNum ?? -1, expenseIdNum ?? -1)

  if (tripLoading || expenseLoading) {
    return <Skeleton className="h-72 rounded-2xl" />
  }
  if (!trip || !expense || tripIdNum === undefined || expenseIdNum === undefined) {
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
          {trip.name}
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
        onCancel={() => navigate(`/trips/${tripIdNum}`)}
        onSubmit={(values) =>
          updateExpense.mutate(values, {
            onSuccess: () => {
              toast.success("Expense updated")
              navigate(`/trips/${tripIdNum}`)
            },
            onError: (error) => {
              toast.error(
                extractApiErrorMessage(error, "Couldn't update expense")
              )
            },
          })
        }
      />
    </div>
  )
}

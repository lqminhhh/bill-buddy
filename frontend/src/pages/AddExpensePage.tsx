import { useNavigate, useParams } from "react-router-dom"
import { toast } from "sonner"

import { ExpenseForm } from "@/components/ExpenseForm"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"
import { useCreateExpense } from "@/hooks/useExpenses"
import { extractApiErrorMessage } from "@/hooks/useMembers"
import { useTrip } from "@/hooks/useTrips"

export function AddExpensePage() {
  const { tripId } = useParams<{ tripId: string }>()
  const tripIdNum = tripId ? Number.parseInt(tripId, 10) : undefined
  const navigate = useNavigate()
  const { data: trip, isLoading } = useTrip(tripIdNum)
  const createExpense = useCreateExpense(tripIdNum ?? -1)

  if (isLoading) {
    return <Skeleton className="h-72 rounded-2xl" />
  }
  if (!trip || tripIdNum === undefined) {
    return (
      <Card>
        <CardContent className="py-10 text-sm text-muted-foreground">
          Trip not found.
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
          Add an expense
        </h1>
      </div>
      <ExpenseForm
        members={trip.members}
        submitLabel="Save expense"
        pendingLabel="Saving…"
        isPending={createExpense.isPending}
        onCancel={() => navigate(`/trips/${tripIdNum}`)}
        onSubmit={(values) =>
          createExpense.mutate(values, {
            onSuccess: () => {
              toast.success("Expense added")
              navigate(`/trips/${tripIdNum}`)
            },
            onError: (error) => {
              toast.error(
                extractApiErrorMessage(error, "Couldn't save expense")
              )
            },
          })
        }
      />
    </div>
  )
}

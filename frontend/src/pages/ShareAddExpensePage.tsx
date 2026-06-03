import { useNavigate, useParams } from "react-router-dom"
import { toast } from "sonner"

import { ExpenseForm } from "@/components/ExpenseForm"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { extractApiErrorMessage } from "@/hooks/useMembers"
import { useCreateSharedExpense, useSharedTrip } from "@/hooks/useSharedTrip"

export function ShareAddExpensePage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const { data: trip, isLoading } = useSharedTrip(token)
  const createExpense = useCreateSharedExpense(token ?? "")

  if (isLoading) return <Skeleton className="h-72 rounded-2xl" />
  if (!trip || !token) {
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
          {trip.name} · shared
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
        onCancel={() => navigate(`/share/${token}`)}
        onSubmit={(values) =>
          createExpense.mutate(values, {
            onSuccess: () => {
              toast.success("Expense added")
              navigate(`/share/${token}`)
            },
            onError: (error) =>
              toast.error(extractApiErrorMessage(error, "Couldn't save expense")),
          })
        }
      />
    </div>
  )
}

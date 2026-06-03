import { useMemo, useState } from "react"
import { Link, useNavigate, useParams } from "react-router-dom"
import {
  BarChart3,
  Download,
  Pencil,
  Plus,
  Receipt,
  Share2,
  Trash2,
} from "lucide-react"
import { toast } from "sonner"

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ShareTripDialog } from "@/components/ShareTripDialog"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { api } from "@/api/client"
import type { Expense } from "@/api/types"
import { useDeleteExpense, useExpenses } from "@/hooks/useExpenses"
import { extractApiErrorMessage } from "@/hooks/useMembers"
import {
  useBalances,
  useSettlements,
} from "@/hooks/useTripDerived"
import { useDeleteTrip, useTrip } from "@/hooks/useTrips"
import { formatCents } from "@/lib/format"

const ALL_PAYERS = "all"

function balanceClassName(net: number): string {
  if (net > 0) return "text-emerald-600 dark:text-emerald-400"
  if (net < 0) return "text-destructive"
  return "text-muted-foreground"
}

export function TripDetailPage() {
  const { id } = useParams<{ id: string }>()
  const tripId = id ? Number.parseInt(id, 10) : undefined
  const navigate = useNavigate()

  const [payerFilter, setPayerFilter] = useState<string>(ALL_PAYERS)
  const [expenseToDelete, setExpenseToDelete] = useState<Expense | null>(null)
  const [confirmTripDelete, setConfirmTripDelete] = useState(false)
  const [shareOpen, setShareOpen] = useState(false)

  const { data: trip, isLoading: tripLoading, isError } = useTrip(tripId)
  const expenseFilters = useMemo(
    () =>
      payerFilter === ALL_PAYERS
        ? undefined
        : { payer_id: Number.parseInt(payerFilter, 10) },
    [payerFilter]
  )
  const { data: expenses } = useExpenses(tripId, expenseFilters)
  const { data: balances } = useBalances(tripId)
  const { data: settlements } = useSettlements(tripId)
  const deleteExpense = useDeleteExpense(tripId ?? -1)
  const deleteTrip = useDeleteTrip()

  if (tripLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 rounded-2xl" />
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    )
  }

  if (isError || !trip) {
    return (
      <Card>
        <CardContent className="py-10 text-sm text-muted-foreground">
          Trip not found.{" "}
          <Link to="/" className="text-primary hover:underline">
            Back to trips
          </Link>
          .
        </CardContent>
      </Card>
    )
  }

  const handleConfirmDeleteExpense = () => {
    if (!expenseToDelete) return
    deleteExpense.mutate(expenseToDelete.id, {
      onSuccess: () => {
        toast.success("Expense deleted")
        setExpenseToDelete(null)
      },
      onError: (error) => {
        toast.error(extractApiErrorMessage(error, "Couldn't delete expense"))
      },
    })
  }

  const handleConfirmDeleteTrip = () => {
    if (!tripId) return
    const tripName = trip.name
    deleteTrip.mutate(tripId, {
      onSuccess: () => {
        toast.success(`Deleted "${tripName}"`)
        navigate("/")
      },
      onError: (error) => {
        toast.error(extractApiErrorMessage(error, "Couldn't delete trip"))
      },
    })
  }

  const exportUrl = api.exportExpensesCsvUrl(
    tripId as number,
    payerFilter === ALL_PAYERS
      ? undefined
      : { payer_id: Number.parseInt(payerFilter, 10) }
  )

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-primary">
            Trip
          </p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            {trip.name}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {trip.currency} · {trip.members.length} member
            {trip.members.length === 1 ? "" : "s"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild>
            <Link to={`/trips/${tripId}/expenses/new`}>
              <Plus />
              Add expense
            </Link>
          </Button>
          <Button asChild variant="secondary">
            <Link to={`/trips/${tripId}/summary`}>
              <BarChart3 />
              Summary
            </Link>
          </Button>
          <Button variant="secondary" onClick={() => setShareOpen(true)}>
            <Share2 />
            Share
          </Button>
          <Button
            variant="ghost"
            onClick={() => setConfirmTripDelete(true)}
            className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
          >
            <Trash2 />
            Delete trip
          </Button>
        </div>
      </div>

      {/* Balances */}
      <Card>
        <CardHeader>
          <CardTitle>Balances</CardTitle>
          <CardDescription>
            Net = paid − share. Positive means others owe them, negative means
            they owe.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {balances && balances.length > 0 ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {balances.map((b) => (
                <div
                  key={b.member_id}
                  className="space-y-2 rounded-xl border bg-card p-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{b.name}</h3>
                      {b.is_self ? (
                        <Badge variant="secondary">You</Badge>
                      ) : null}
                    </div>
                  </div>
                  <div className="space-y-1 text-sm text-muted-foreground">
                    <p>Paid {formatCents(b.total_paid, trip.currency)}</p>
                    <p>Share {formatCents(b.total_share, trip.currency)}</p>
                  </div>
                  <p
                    className={`text-base font-semibold ${balanceClassName(b.net_balance)}`}
                  >
                    Net {formatCents(b.net_balance, trip.currency)}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No data yet.</p>
          )}
        </CardContent>
      </Card>

      {/* Settlements */}
      <Card>
        <CardHeader>
          <CardTitle>Settle up</CardTitle>
          <CardDescription>
            The minimum set of payments needed to balance the trip.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {settlements && settlements.length > 0 ? (
            <ul className="divide-y rounded-xl border">
              {settlements.map((s, i) => (
                <li
                  key={`${s.from_member_id}-${s.to_member_id}-${i}`}
                  className="flex items-center justify-between gap-3 px-4 py-3"
                >
                  <span className="text-sm">
                    <span className="font-medium">{s.from_member_name}</span>
                    <span className="mx-2 text-muted-foreground">pays</span>
                    <span className="font-medium">{s.to_member_name}</span>
                  </span>
                  <span className="font-semibold text-primary">
                    {formatCents(s.amount_cents, trip.currency)}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">
              Everyone is settled — no payments needed.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Expenses */}
      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Receipt className="size-4 text-primary" />
              Expenses
            </CardTitle>
            <CardDescription>
              Every shared cost logged for this trip.
            </CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Select value={payerFilter} onValueChange={setPayerFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by payer" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_PAYERS}>All payers</SelectItem>
                {trip.members.map((m) => (
                  <SelectItem key={m.id} value={String(m.id)}>
                    {m.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button asChild variant="secondary" size="sm">
              <a href={exportUrl} target="_blank" rel="noreferrer">
                <Download />
                CSV
              </a>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {expenses && expenses.length > 0 ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Paid by</TableHead>
                    <TableHead>Participants</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {expenses.map((expense) => (
                    <TableRow key={expense.id}>
                      <TableCell className="whitespace-nowrap text-muted-foreground">
                        {expense.expense_date}
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{expense.description}</div>
                        {expense.notes ? (
                          <div className="text-xs text-muted-foreground">
                            {expense.notes}
                          </div>
                        ) : null}
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        {formatCents(expense.amount_cents, trip.currency)}
                      </TableCell>
                      <TableCell>{expense.payer_name}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {expense.participants.map((p) => p.name).join(", ")}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button
                            asChild
                            variant="ghost"
                            size="icon"
                            aria-label="Edit expense"
                          >
                            <Link
                              to={`/trips/${tripId}/expenses/${expense.id}/edit`}
                            >
                              <Pencil className="size-4" />
                            </Link>
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label="Delete expense"
                            onClick={() => setExpenseToDelete(expense)}
                            className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                          >
                            <Trash2 className="size-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="space-y-3 py-2">
              <p className="text-sm text-muted-foreground">
                {payerFilter === ALL_PAYERS
                  ? "No expenses yet. Add the first one to start tracking balances."
                  : "No expenses match this filter."}
              </p>
              {payerFilter === ALL_PAYERS ? (
                <Button asChild size="sm">
                  <Link to={`/trips/${tripId}/expenses/new`}>
                    <Plus />
                    Add the first expense
                  </Link>
                </Button>
              ) : null}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete expense modal */}
      <AlertDialog
        open={expenseToDelete !== null}
        onOpenChange={(open) => !open && setExpenseToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this expense?</AlertDialogTitle>
            <AlertDialogDescription>
              {expenseToDelete?.description} ·{" "}
              {expenseToDelete
                ? formatCents(expenseToDelete.amount_cents, trip.currency)
                : ""}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDeleteExpense}
              className="bg-destructive text-white hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Share dialog */}
      <ShareTripDialog
        open={shareOpen}
        onOpenChange={setShareOpen}
        tripId={tripId as number}
        tripName={trip.name}
        shareToken={trip.share_token}
      />

      {/* Delete trip modal */}
      <AlertDialog
        open={confirmTripDelete}
        onOpenChange={setConfirmTripDelete}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete "{trip.name}"?</AlertDialogTitle>
            <AlertDialogDescription>
              All members, expenses, and balances for this trip will be removed.
              This can't be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDeleteTrip}
              className="bg-destructive text-white hover:bg-destructive/90"
            >
              Delete trip
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

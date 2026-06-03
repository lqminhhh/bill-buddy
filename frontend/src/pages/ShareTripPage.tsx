import { useMemo, useState } from "react"
import { Link, useParams } from "react-router-dom"
import {
  Download,
  Pencil,
  Plus,
  Receipt,
  Trash2,
  Users,
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
import { extractApiErrorMessage } from "@/hooks/useMembers"
import {
  useDeleteSharedExpense,
  useSharedBalances,
  useSharedExpenses,
  useSharedSettlements,
  useSharedTrip,
} from "@/hooks/useSharedTrip"
import { formatCents } from "@/lib/format"

const ALL_PAYERS = "all"

function balanceClassName(net: number): string {
  if (net > 0) return "text-emerald-600 dark:text-emerald-400"
  if (net < 0) return "text-destructive"
  return "text-muted-foreground"
}

export function ShareTripPage() {
  const { token } = useParams<{ token: string }>()
  const [payerFilter, setPayerFilter] = useState<string>(ALL_PAYERS)
  const [expenseToDelete, setExpenseToDelete] = useState<Expense | null>(null)

  const { data: trip, isLoading, isError } = useSharedTrip(token)
  const filters = useMemo(
    () =>
      payerFilter === ALL_PAYERS
        ? undefined
        : { payer_id: Number.parseInt(payerFilter, 10) },
    [payerFilter]
  )
  const { data: expenses } = useSharedExpenses(token, filters)
  const { data: balances } = useSharedBalances(token)
  const { data: settlements } = useSharedSettlements(token)
  const deleteExpense = useDeleteSharedExpense(token ?? "")

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 rounded-2xl" />
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    )
  }

  if (isError || !trip || !token) {
    return (
      <Card>
        <CardContent className="space-y-3 py-10">
          <h2 className="text-xl font-semibold">Trip link not found</h2>
          <p className="text-sm text-muted-foreground">
            This share link is invalid or has been rotated. Ask the trip owner
            for the latest link.
          </p>
          <Button asChild variant="secondary">
            <Link to="/">Go home</Link>
          </Button>
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

  return (
    <div className="space-y-6">
      {/* Banner explaining share mode */}
      <Card className="border-primary/30 bg-primary/5">
        <CardContent className="flex flex-col gap-2 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-primary">
              Shared trip
            </p>
            <p className="text-sm text-muted-foreground">
              You're viewing via a share link — no account needed. Add expenses
              as anyone in the trip.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Hero */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
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
            <Link to={`/share/${token}/expenses/new`}>
              <Plus />
              Add expense
            </Link>
          </Button>
        </div>
      </div>

      {/* Members */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="size-4 text-primary" />
            Members
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {trip.members.map((m) => (
              <Badge key={m.id} variant="secondary" className="px-3 py-1.5">
                {m.name}
                {m.is_self ? " (owner)" : ""}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

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
                    <h3 className="font-semibold">{b.name}</h3>
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
              <a
                href={api.share.exportCsvUrl(token)}
                target="_blank"
                rel="noreferrer"
              >
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
                              to={`/share/${token}/expenses/${expense.id}/edit`}
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
                No expenses yet. Add the first one!
              </p>
              <Button asChild size="sm">
                <Link to={`/share/${token}/expenses/new`}>
                  <Plus />
                  Add the first expense
                </Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete confirmation */}
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
    </div>
  )
}

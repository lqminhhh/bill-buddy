import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { parseAmountToCents, todayIso } from "@/lib/format"
import type { Member } from "@/api/types"

export interface ExpenseFormValues {
  description: string
  amount_cents: number
  expense_date: string
  paid_by_member_id: number
  participant_ids: number[]
  notes: string | null
}

export interface ExpenseFormInitial {
  description?: string
  amountText?: string
  expense_date?: string
  paid_by_member_id?: number
  participant_ids?: number[]
  notes?: string | null
}

interface ExpenseFormProps {
  members: Member[]
  initial?: ExpenseFormInitial
  submitLabel: string
  pendingLabel: string
  isPending: boolean
  onCancel: () => void
  onSubmit: (values: ExpenseFormValues) => void
}

export function ExpenseForm({
  members,
  initial,
  submitLabel,
  pendingLabel,
  isPending,
  onCancel,
  onSubmit,
}: ExpenseFormProps) {
  const defaultPayerId =
    initial?.paid_by_member_id ??
    members.find((m) => m.is_self)?.id ??
    members[0]?.id

  const defaultParticipants =
    initial?.participant_ids ?? members.map((m) => m.id)

  const [description, setDescription] = useState(initial?.description ?? "")
  const [amount, setAmount] = useState(initial?.amountText ?? "")
  const [expenseDate, setExpenseDate] = useState(
    initial?.expense_date ?? todayIso()
  )
  const [payerId, setPayerId] = useState<number | undefined>(defaultPayerId)
  const [participantIds, setParticipantIds] = useState<number[]>(defaultParticipants)
  const [notes, setNotes] = useState(initial?.notes ?? "")
  const [errors, setErrors] = useState<string[]>([])

  useEffect(() => {
    if (payerId === undefined && members.length > 0) {
      setPayerId(members.find((m) => m.is_self)?.id ?? members[0].id)
    }
  }, [members, payerId])

  const toggleParticipant = (memberId: number) => {
    setParticipantIds((current) =>
      current.includes(memberId)
        ? current.filter((id) => id !== memberId)
        : [...current, memberId]
    )
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const problems: string[] = []
    if (!description.trim()) problems.push("Description is required.")
    const cents = parseAmountToCents(amount)
    if (cents === null) problems.push("Enter a valid amount (e.g. 12.50).")
    else if (cents <= 0) problems.push("Amount must be greater than zero.")
    if (!expenseDate) problems.push("Date is required.")
    if (!payerId) problems.push("Choose who paid.")
    if (participantIds.length === 0)
      problems.push("Select at least one participant.")
    setErrors(problems)
    if (problems.length > 0) return

    onSubmit({
      description: description.trim(),
      amount_cents: cents as number,
      expense_date: expenseDate,
      paid_by_member_id: payerId as number,
      participant_ids: participantIds,
      notes: notes.trim() ? notes.trim() : null,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Expense details</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Dinner at Tasca da Esquina"
              autoFocus
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="amount">Amount</Label>
            <Input
              id="amount"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="12.50"
              inputMode="decimal"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="expense-date">Date</Label>
            <Input
              id="expense-date"
              type="date"
              value={expenseDate}
              onChange={(e) => setExpenseDate(e.target.value)}
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="payer">Paid by</Label>
            <Select
              value={payerId ? String(payerId) : ""}
              onValueChange={(v) => setPayerId(Number.parseInt(v, 10))}
            >
              <SelectTrigger id="payer">
                <SelectValue placeholder="Select a member" />
              </SelectTrigger>
              <SelectContent>
                {members.map((member) => (
                  <SelectItem key={member.id} value={String(member.id)}>
                    {member.name}
                    {member.is_self ? " (you)" : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Participants</CardTitle>
          <CardDescription>
            Who's splitting this expense? Tap members to toggle.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2">
            {members.map((member) => {
              const checked = participantIds.includes(member.id)
              return (
                <label
                  key={member.id}
                  className={`flex cursor-pointer items-center gap-3 rounded-xl border bg-card px-3 py-2.5 text-sm font-medium transition-colors ${
                    checked
                      ? "border-primary/50 bg-primary/5"
                      : "hover:bg-accent/40"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleParticipant(member.id)}
                    className="size-4 accent-primary"
                  />
                  <span className="flex-1">{member.name}</span>
                  {member.is_self ? (
                    <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                      you
                    </span>
                  ) : null}
                </label>
              )
            })}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notes</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            placeholder="Optional context, receipt number, etc."
          />
        </CardContent>
      </Card>

      {errors.length > 0 && (
        <Card className="border-destructive/40 bg-destructive/5">
          <CardContent className="py-4">
            <ul className="list-disc space-y-1 pl-5 text-sm text-destructive">
              {errors.map((error) => (
                <li key={error}>{error}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isPending}>
          {isPending ? pendingLabel : submitLabel}
        </Button>
      </div>
    </form>
  )
}

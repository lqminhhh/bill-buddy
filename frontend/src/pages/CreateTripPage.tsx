import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Plus, Trash2 } from "lucide-react"
import { toast } from "sonner"

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
import { Separator } from "@/components/ui/separator"
import { useCreateTrip } from "@/hooks/useTrips"
import { extractApiErrorMessage } from "@/hooks/useMembers"

interface MemberRow {
  name: string
  isSelf: boolean
}

const emptyMember = (): MemberRow => ({ name: "", isSelf: false })

export function CreateTripPage() {
  const navigate = useNavigate()
  const createTrip = useCreateTrip()

  const [name, setName] = useState("")
  const [currency, setCurrency] = useState("USD")
  const [members, setMembers] = useState<MemberRow[]>([
    { name: "", isSelf: true },
    { name: "", isSelf: false },
  ])
  const [errors, setErrors] = useState<string[]>([])

  const updateMember = (index: number, patch: Partial<MemberRow>) => {
    setMembers((current) =>
      current.map((member, i) =>
        i === index ? { ...member, ...patch } : member
      )
    )
  }

  const setSelfAt = (index: number) => {
    setMembers((current) =>
      current.map((member, i) => ({ ...member, isSelf: i === index }))
    )
  }

  const addRow = () => {
    setMembers((current) => [...current, emptyMember()])
  }

  const removeRow = (index: number) => {
    setMembers((current) => {
      if (current.length <= 1) return current
      const wasSelf = current[index].isSelf
      const next = current.filter((_, i) => i !== index)
      if (wasSelf && next.length > 0) next[0].isSelf = true
      return next
    })
  }

  const validate = (): string[] => {
    const problems: string[] = []
    if (!name.trim()) problems.push("Trip name is required.")
    const cleanCurrency = currency.trim().toUpperCase()
    if (cleanCurrency.length !== 3)
      problems.push("Currency must be a 3-letter code (e.g. USD).")
    if (members.length < 1) problems.push("Add at least one member.")
    if (members.some((m) => !m.name.trim()))
      problems.push("Every member needs a name.")
    if (members.filter((m) => m.isSelf).length !== 1)
      problems.push("Select exactly one member as yourself.")
    const names = members.map((m) => m.name.trim().toLowerCase())
    if (new Set(names).size !== names.length)
      problems.push("Member names must be unique within a trip.")
    return problems
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const problems = validate()
    setErrors(problems)
    if (problems.length > 0) return

    createTrip.mutate(
      {
        name: name.trim(),
        currency: currency.trim().toUpperCase(),
        members: members.map((m) => ({ name: m.name.trim(), is_self: m.isSelf })),
      },
      {
        onSuccess: (trip) => {
          toast.success(`Created "${trip.name}"`)
          navigate(`/trips/${trip.id}`)
        },
        onError: (error) => {
          toast.error(extractApiErrorMessage(error, "Couldn't create trip"))
        },
      }
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-primary">
          New trip
        </p>
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          Set up your trip
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Name the trip, list everyone who's coming, and mark which one is you.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Trip details</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-[1fr_140px]">
            <div className="space-y-2">
              <Label htmlFor="trip-name">Trip name</Label>
              <Input
                id="trip-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Weekend in Lisbon"
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="currency">Currency</Label>
              <Input
                id="currency"
                value={currency}
                onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                maxLength={3}
                placeholder="USD"
                className="uppercase"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Members</CardTitle>
            <CardDescription>
              Add every person who'll share expenses. Pick exactly one as
              yourself.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {members.map((member, index) => (
              <div
                key={index}
                className="flex flex-col gap-2 rounded-xl border bg-card p-3 sm:flex-row sm:items-center"
              >
                <Input
                  value={member.name}
                  onChange={(e) =>
                    updateMember(index, { name: e.target.value })
                  }
                  placeholder={`Member ${index + 1}`}
                  className="flex-1"
                />
                <label className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium sm:px-2">
                  <input
                    type="radio"
                    name="self-member"
                    checked={member.isSelf}
                    onChange={() => setSelfAt(index)}
                    className="size-4 accent-primary"
                  />
                  This is me
                </label>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  disabled={members.length <= 1}
                  onClick={() => removeRow(index)}
                  aria-label="Remove member"
                  className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                >
                  <Trash2 className="size-4" />
                </Button>
              </div>
            ))}
            <Separator />
            <Button
              type="button"
              variant="secondary"
              onClick={addRow}
              className="w-full sm:w-auto"
            >
              <Plus />
              Add member
            </Button>
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
          <Button asChild variant="ghost">
            <Link to="/">Cancel</Link>
          </Button>
          <Button type="submit" disabled={createTrip.isPending}>
            {createTrip.isPending ? "Creating…" : "Create trip"}
          </Button>
        </div>
      </form>
    </div>
  )
}

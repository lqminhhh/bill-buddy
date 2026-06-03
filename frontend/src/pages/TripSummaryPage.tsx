import { Link, useParams } from "react-router-dom"
import { ArrowLeft, type LucideIcon, Receipt, TrendingDown, TrendingUp, Users, Wallet } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useSummary } from "@/hooks/useTripDerived"
import { useTrip } from "@/hooks/useTrips"
import { formatCents } from "@/lib/format"

interface MetricCardProps {
  icon: LucideIcon
  label: string
  value: string
  sublabel?: string
}

function MetricCard({ icon: Icon, label, value, sublabel }: MetricCardProps) {
  return (
    <Card>
      <CardContent className="space-y-2 py-5">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <Icon className="size-4 text-primary" />
          {label}
        </div>
        <div className="text-2xl font-semibold tracking-tight">{value}</div>
        {sublabel ? (
          <div className="text-xs text-muted-foreground">{sublabel}</div>
        ) : null}
      </CardContent>
    </Card>
  )
}

export function TripSummaryPage() {
  const { id } = useParams<{ id: string }>()
  const tripId = id ? Number.parseInt(id, 10) : undefined
  const { data: trip } = useTrip(tripId)
  const { data: summary, isLoading } = useSummary(tripId)

  if (isLoading) {
    return <Skeleton className="h-72 rounded-2xl" />
  }
  if (!summary || !trip) {
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
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-primary">
            {summary.trip_name}
          </p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Trip summary
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            High-level stats for everyone in the trip.
          </p>
        </div>
        <Button asChild variant="secondary">
          <Link to={`/trips/${tripId}`}>
            <ArrowLeft />
            Back to trip
          </Link>
        </Button>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          icon={Wallet}
          label="Total spending"
          value={formatCents(summary.total_trip_spending, summary.currency)}
        />
        <MetricCard
          icon={Receipt}
          label="Expenses"
          value={String(summary.total_expenses)}
        />
        <MetricCard
          icon={Users}
          label="Members"
          value={String(summary.total_members)}
        />
        <MetricCard
          icon={TrendingUp}
          label="Highest spender"
          value={
            summary.highest_spender
              ? formatCents(summary.highest_spender.amount_cents, summary.currency)
              : "—"
          }
          sublabel={summary.highest_spender?.name}
        />
        <MetricCard
          icon={TrendingUp}
          label="Highest share"
          value={
            summary.highest_total_share
              ? formatCents(
                  summary.highest_total_share.amount_cents,
                  summary.currency
                )
              : "—"
          }
          sublabel={summary.highest_total_share?.name}
        />
        <MetricCard
          icon={TrendingDown}
          label="Owes the most"
          value={
            summary.member_who_owes_most
              ? formatCents(
                  summary.member_who_owes_most.amount_cents,
                  summary.currency
                )
              : "—"
          }
          sublabel={summary.member_who_owes_most?.name}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>What this means</CardTitle>
          <CardDescription>How each metric is calculated.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            <span className="font-medium text-foreground">Highest spender</span>
            {" "}is the member who paid out the most across all expenses.
          </p>
          <p>
            <span className="font-medium text-foreground">Highest share</span>
            {" "}is the member who participated in expenses with the largest
            cumulative split — typically someone who joined every meal.
          </p>
          <p>
            <span className="font-medium text-foreground">Owes the most</span>
            {" "}is the member with the lowest net balance (paid − share). They'll
            be sending the most money in the settle-up.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

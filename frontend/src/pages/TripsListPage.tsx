import { useState } from "react"
import { Link } from "react-router-dom"
import { ArrowRight, Plus, Trash2 } from "lucide-react"
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
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useDeleteTrip, useTrips } from "@/hooks/useTrips"
import type { Trip } from "@/api/types"

function formatRelativeDate(iso: string): string {
  try {
    const date = new Date(iso)
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  } catch {
    return iso
  }
}

export function TripsListPage() {
  const { data, isLoading, isError, error } = useTrips()
  const deleteTrip = useDeleteTrip()
  const [pendingDelete, setPendingDelete] = useState<Trip | null>(null)

  const handleConfirmDelete = () => {
    if (!pendingDelete) return
    const tripName = pendingDelete.name
    deleteTrip.mutate(pendingDelete.id, {
      onSuccess: () => {
        toast.success(`Deleted "${tripName}"`)
        setPendingDelete(null)
      },
      onError: () => toast.error("Couldn't delete trip"),
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-primary">
            Your trips
          </p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Track shared spending
          </h1>
          <p className="mt-2 max-w-prose text-sm text-muted-foreground">
            Create a trip, add who came along, log every shared expense, and Bill Buddy
            will tell you exactly who owes whom.
          </p>
        </div>
        <Button asChild size="lg" className="self-start sm:self-end">
          <Link to="/trips/new">
            <Plus />
            New trip
          </Link>
        </Button>
      </div>

      {isLoading && (
        <div className="grid gap-3 sm:grid-cols-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-2xl" />
          ))}
        </div>
      )}

      {isError && (
        <Card className="border-destructive/40">
          <CardContent className="py-6 text-sm text-destructive">
            {(error as Error)?.message ?? "Couldn't load trips"}
          </CardContent>
        </Card>
      )}

      {!isLoading && !isError && data && data.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-start gap-3 py-10">
            <Badge variant="secondary">No trips yet</Badge>
            <h2 className="text-xl font-semibold">Start your first trip</h2>
            <p className="text-sm text-muted-foreground">
              Add a destination, the people coming along, and start logging expenses.
            </p>
            <Button asChild>
              <Link to="/trips/new">
                <Plus />
                Create a trip
              </Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {!isLoading && data && data.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {data.map((trip) => (
            <Card
              key={trip.id}
              className="group transition-shadow hover:shadow-md"
            >
              <CardContent className="flex items-start justify-between gap-3 py-5">
                <Link
                  to={`/trips/${trip.id}`}
                  className="flex-1 space-y-1"
                >
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold tracking-tight group-hover:text-primary">
                      {trip.name}
                    </h3>
                    <ArrowRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {trip.currency} · created {formatRelativeDate(trip.created_at)}
                  </p>
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.preventDefault()
                    setPendingDelete(trip)
                  }}
                  aria-label="Delete trip"
                  className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                >
                  <Trash2 className="size-4" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <AlertDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => !open && setPendingDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Delete &quot;{pendingDelete?.name}&quot;?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This removes the trip and all its members and expenses. This action
              can't be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
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

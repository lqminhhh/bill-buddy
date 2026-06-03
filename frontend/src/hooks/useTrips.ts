import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/api/client"
import { qk } from "@/api/queryKeys"
import type { CreateTripInput } from "@/api/types"

export function useTrips() {
  return useQuery({ queryKey: qk.trips, queryFn: api.listTrips })
}

export function useTrip(tripId: number | undefined) {
  return useQuery({
    queryKey: tripId ? qk.trip(tripId) : ["trip", "missing"],
    queryFn: () => api.getTrip(tripId as number),
    enabled: typeof tripId === "number",
  })
}

export function useCreateTrip() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateTripInput) => api.createTrip(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.trips }),
  })
}

export function useDeleteTrip() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.deleteTrip(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.trips }),
  })
}

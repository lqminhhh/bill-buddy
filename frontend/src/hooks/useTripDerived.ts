import { useQuery } from "@tanstack/react-query"

import { api } from "@/api/client"
import { qk } from "@/api/queryKeys"

export function useBalances(tripId: number | undefined) {
  return useQuery({
    queryKey: tripId ? qk.balances(tripId) : ["balances", "missing"],
    queryFn: () => api.getBalances(tripId as number),
    enabled: typeof tripId === "number",
  })
}

export function useSettlements(tripId: number | undefined) {
  return useQuery({
    queryKey: tripId ? qk.settlements(tripId) : ["settlements", "missing"],
    queryFn: () => api.getSettlements(tripId as number),
    enabled: typeof tripId === "number",
  })
}

export function useSummary(tripId: number | undefined) {
  return useQuery({
    queryKey: tripId ? qk.summary(tripId) : ["summary", "missing"],
    queryFn: () => api.getSummary(tripId as number),
    enabled: typeof tripId === "number",
  })
}

import { useMutation, useQueryClient } from "@tanstack/react-query"
import axios from "axios"

import { http } from "@/api/client"
import { qk } from "@/api/queryKeys"
import type { Member } from "@/api/types"

interface AddMemberInput {
  name: string
  is_self?: boolean
}

export function useAddMember(tripId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: AddMemberInput) =>
      http
        .post<Member>(`/api/trips/${tripId}/members`, input)
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.trip(tripId) })
    },
  })
}

export function useRemoveMember(tripId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (memberId: number) =>
      http
        .delete(`/api/trips/${tripId}/members/${memberId}`)
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.trip(tripId) })
      qc.invalidateQueries({ queryKey: qk.balances(tripId) })
      qc.invalidateQueries({ queryKey: qk.settlements(tripId) })
    },
  })
}

export function extractApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === "string") return detail
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  }
  return fallback
}

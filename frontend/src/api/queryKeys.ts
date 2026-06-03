export const qk = {
  trips: ["trips"] as const,
  trip: (id: number) => ["trips", id] as const,
  expenses: (tripId: number) => ["trips", tripId, "expenses"] as const,
  expense: (id: number) => ["expenses", id] as const,
  balances: (tripId: number) => ["trips", tripId, "balances"] as const,
  settlements: (tripId: number) => ["trips", tripId, "settlements"] as const,
  summary: (tripId: number) => ["trips", tripId, "summary"] as const,
}

export function formatCents(amountCents: number, currency: string) {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency,
  }).format(amountCents / 100)
}

export function parseAmountToCents(value: string): number | null {
  const normalized = value.trim().replace(/,/g, "")
  if (!normalized) return null
  if (!/^\d+(\.\d{1,2})?$/.test(normalized)) return null

  const amount = Number(normalized)
  if (!Number.isFinite(amount)) return null

  return Math.round(amount * 100)
}

export function todayIso() {
  const now = new Date()
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000)
  return local.toISOString().slice(0, 10)
}

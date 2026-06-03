export interface Trip {
  id: number
  name: string
  currency: string
  created_at: string
  share_token?: string | null
}

export interface User {
  id: number
  email: string
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface LoginInput {
  email: string
  password: string
}

export interface SignupInput {
  email: string
  password: string
}

export interface Member {
  id: number
  name: string
  is_self: number
}

export interface TripDetail extends Trip {
  members: Member[]
}

export interface ExpenseParticipant {
  id: number
  name: string
}

export interface Expense {
  id: number
  description: string
  amount_cents: number
  expense_date: string
  paid_by_member_id: number
  payer_name: string
  notes: string | null
  participants: ExpenseParticipant[]
}

export interface Balance {
  member_id: number
  name: string
  is_self: number
  total_paid: number
  total_share: number
  net_balance: number
}

export interface Settlement {
  from_member_id: number
  from_member_name: string
  to_member_id: number
  to_member_name: string
  amount_cents: number
}

export interface SummaryMetric {
  name: string
  amount_cents: number
}

export interface TripSummary {
  trip_name: string
  currency: string
  total_trip_spending: number
  total_expenses: number
  total_members: number
  highest_spender: SummaryMetric | null
  member_who_owes_most: SummaryMetric | null
  highest_total_share: SummaryMetric | null
}

export interface CreateTripInput {
  name: string
  currency: string
  members: { name: string; is_self: boolean }[]
}

export interface CreateExpenseInput {
  description: string
  amount_cents: number
  expense_date: string
  paid_by_member_id: number
  participant_ids: number[]
  notes?: string | null
}

export interface UpdateExpenseInput {
  description?: string
  amount_cents?: number
  expense_date?: string
  paid_by_member_id?: number
  participant_ids?: number[]
  notes?: string | null
}

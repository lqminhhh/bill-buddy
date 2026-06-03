import axios from "axios"

import { clearStoredAuth, getStoredToken } from "./auth-storage"
import type {
  AuthResponse,
  Balance,
  CreateExpenseInput,
  CreateTripInput,
  Expense,
  LoginInput,
  Settlement,
  SignupInput,
  Trip,
  TripDetail,
  TripSummary,
  UpdateExpenseInput,
  User,
} from "./types"

const baseURL = import.meta.env.VITE_API_BASE_URL ?? ""

export const http = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
})

http.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let onUnauthorized: (() => void) | null = null
export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler
}

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const url = error.config?.url ?? ""
      // 401s from share-link routes don't apply (they're public)
      if (!url.includes("/api/share/") && !url.includes("/api/auth/login") && !url.includes("/api/auth/signup")) {
        clearStoredAuth()
        onUnauthorized?.()
      }
    }
    return Promise.reject(error)
  }
)

export const api = {
  // ---------- Auth ----------
  signup: (input: SignupInput) =>
    http.post<AuthResponse>("/api/auth/signup", input).then((r) => r.data),
  login: (input: LoginInput) =>
    http.post<AuthResponse>("/api/auth/login", input).then((r) => r.data),
  me: () => http.get<User>("/api/auth/me").then((r) => r.data),

  // ---------- Owner trips ----------
  listTrips: () => http.get<Trip[]>("/api/trips").then((r) => r.data),
  getTrip: (id: number) =>
    http.get<TripDetail>(`/api/trips/${id}`).then((r) => r.data),
  createTrip: (input: CreateTripInput) =>
    http.post<TripDetail>("/api/trips", input).then((r) => r.data),
  deleteTrip: (id: number) =>
    http.delete(`/api/trips/${id}`).then((r) => r.data),
  rotateShareToken: (id: number) =>
    http.post<Trip>(`/api/trips/${id}/rotate-share-token`).then((r) => r.data),

  // ---------- Owner expenses ----------
  listExpenses: (
    tripId: number,
    params?: { payer_id?: number; from?: string; to?: string }
  ) =>
    http
      .get<Expense[]>(`/api/trips/${tripId}/expenses`, { params })
      .then((r) => r.data),
  createExpense: (tripId: number, input: CreateExpenseInput) =>
    http
      .post<Expense>(`/api/trips/${tripId}/expenses`, input)
      .then((r) => r.data),
  getExpense: (id: number) =>
    http.get<Expense>(`/api/expenses/${id}`).then((r) => r.data),
  updateExpense: (id: number, input: UpdateExpenseInput) =>
    http.patch<Expense>(`/api/expenses/${id}`, input).then((r) => r.data),
  deleteExpense: (id: number) =>
    http.delete(`/api/expenses/${id}`).then((r) => r.data),

  // ---------- Derived ----------
  getBalances: (tripId: number) =>
    http.get<Balance[]>(`/api/trips/${tripId}/balances`).then((r) => r.data),
  getSettlements: (tripId: number) =>
    http
      .get<Settlement[]>(`/api/trips/${tripId}/settlements`)
      .then((r) => r.data),
  getSummary: (tripId: number) =>
    http.get<TripSummary>(`/api/trips/${tripId}/summary`).then((r) => r.data),

  exportExpensesCsvUrl: (
    tripId: number,
    params?: { payer_id?: number; from?: string; to?: string }
  ) => {
    const query = new URLSearchParams()
    if (params?.payer_id) query.set("payer_id", String(params.payer_id))
    if (params?.from) query.set("from", params.from)
    if (params?.to) query.set("to", params.to)
    const qs = query.toString()
    return `${baseURL}/api/trips/${tripId}/expenses.csv${qs ? `?${qs}` : ""}`
  },

  // ---------- Share-token (no auth) ----------
  share: {
    getTrip: (token: string) =>
      http.get<TripDetail>(`/api/share/${token}`).then((r) => r.data),
    listExpenses: (
      token: string,
      params?: { payer_id?: number; from?: string; to?: string }
    ) =>
      http
        .get<Expense[]>(`/api/share/${token}/expenses`, { params })
        .then((r) => r.data),
    createExpense: (token: string, input: CreateExpenseInput) =>
      http
        .post<Expense>(`/api/share/${token}/expenses`, input)
        .then((r) => r.data),
    updateExpense: (token: string, expenseId: number, input: UpdateExpenseInput) =>
      http
        .patch<Expense>(`/api/share/${token}/expenses/${expenseId}`, input)
        .then((r) => r.data),
    deleteExpense: (token: string, expenseId: number) =>
      http.delete(`/api/share/${token}/expenses/${expenseId}`).then((r) => r.data),
    getBalances: (token: string) =>
      http.get<Balance[]>(`/api/share/${token}/balances`).then((r) => r.data),
    getSettlements: (token: string) =>
      http
        .get<Settlement[]>(`/api/share/${token}/settlements`)
        .then((r) => r.data),
    getSummary: (token: string) =>
      http
        .get<TripSummary>(`/api/share/${token}/summary`)
        .then((r) => r.data),
    exportCsvUrl: (token: string) =>
      `${baseURL}/api/share/${token}/expenses.csv`,
  },
}

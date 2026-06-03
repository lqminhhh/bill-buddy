const TOKEN_KEY = "bill-buddy.token"
const USER_KEY = "bill-buddy.user"

import type { User } from "./types"

export function getStoredToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function getStoredUser(): User | null {
  try {
    const raw = window.localStorage.getItem(USER_KEY)
    return raw ? (JSON.parse(raw) as User) : null
  } catch {
    return null
  }
}

export function storeAuth(token: string, user: User): void {
  try {
    window.localStorage.setItem(TOKEN_KEY, token)
    window.localStorage.setItem(USER_KEY, JSON.stringify(user))
  } catch {
    // ignore (e.g. private browsing)
  }
}

export function clearStoredAuth(): void {
  try {
    window.localStorage.removeItem(TOKEN_KEY)
    window.localStorage.removeItem(USER_KEY)
  } catch {
    // ignore
  }
}

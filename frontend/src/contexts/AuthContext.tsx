import { createContext, useCallback, useEffect, useMemo, useState } from "react"

import { api } from "@/api/client"
import { clearStoredAuth, getStoredUser, storeAuth } from "@/api/auth-storage"
import type { AuthResponse, LoginInput, SignupInput, User } from "@/api/types"

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (input: LoginInput) => Promise<void>
  signup: (input: SignupInput) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

interface ProviderProps {
  children: React.ReactNode
  onLogout?: () => void
}

export function AuthProvider({ children, onLogout }: ProviderProps) {
  const [user, setUser] = useState<User | null>(() => getStoredUser())
  const [isLoading, setIsLoading] = useState<boolean>(false)

  useEffect(() => {
    // Verify stored token still works on mount (silent refresh of `me`)
    if (!user) return
    setIsLoading(true)
    api
      .me()
      .then((fresh) => setUser(fresh))
      .catch(() => {
        clearStoredAuth()
        setUser(null)
      })
      .finally(() => setIsLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const applyAuth = useCallback((response: AuthResponse) => {
    storeAuth(response.access_token, response.user)
    setUser(response.user)
  }, [])

  const login = useCallback(
    async (input: LoginInput) => {
      const response = await api.login(input)
      applyAuth(response)
    },
    [applyAuth]
  )

  const signup = useCallback(
    async (input: SignupInput) => {
      const response = await api.signup(input)
      applyAuth(response)
    },
    [applyAuth]
  )

  const logout = useCallback(() => {
    clearStoredAuth()
    setUser(null)
    onLogout?.()
  }, [onLogout])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: user !== null,
      login,
      signup,
      logout,
    }),
    [user, isLoading, login, signup, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

import { useEffect } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import {
  BrowserRouter,
  Route,
  Routes,
  useNavigate,
} from "react-router-dom"

import { setUnauthorizedHandler } from "@/api/client"
import { Toaster } from "@/components/ui/sonner"
import { Layout } from "@/components/Layout"
import { RequireAuth } from "@/components/RequireAuth"
import { AuthProvider } from "@/contexts/AuthContext"
import { AddExpensePage } from "@/pages/AddExpensePage"
import { CreateTripPage } from "@/pages/CreateTripPage"
import { EditExpensePage } from "@/pages/EditExpensePage"
import { LoginPage } from "@/pages/LoginPage"
import { PlaceholderPage } from "@/pages/PlaceholderPage"
import { ShareAddExpensePage } from "@/pages/ShareAddExpensePage"
import { ShareEditExpensePage } from "@/pages/ShareEditExpensePage"
import { ShareTripPage } from "@/pages/ShareTripPage"
import { SignupPage } from "@/pages/SignupPage"
import { TripDetailPage } from "@/pages/TripDetailPage"
import { TripSummaryPage } from "@/pages/TripSummaryPage"
import { TripsListPage } from "@/pages/TripsListPage"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30_000,
    },
  },
})

function UnauthorizedRedirect({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  useEffect(() => {
    setUnauthorizedHandler(() => {
      queryClient.clear()
      navigate("/login", { replace: true })
    })
    return () => setUnauthorizedHandler(null)
  }, [navigate])
  return <>{children}</>
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <UnauthorizedRedirect>
            <Routes>
              <Route element={<Layout />}>
                {/* Public auth pages */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/signup" element={<SignupPage />} />

                {/* Public share routes */}
                <Route path="/share/:token" element={<ShareTripPage />} />
                <Route
                  path="/share/:token/expenses/new"
                  element={<ShareAddExpensePage />}
                />
                <Route
                  path="/share/:token/expenses/:expenseId/edit"
                  element={<ShareEditExpensePage />}
                />

                {/* Owner-protected routes */}
                <Route element={<RequireAuth />}>
                  <Route index element={<TripsListPage />} />
                  <Route path="/trips/new" element={<CreateTripPage />} />
                  <Route path="/trips/:id" element={<TripDetailPage />} />
                  <Route
                    path="/trips/:id/summary"
                    element={<TripSummaryPage />}
                  />
                  <Route
                    path="/trips/:tripId/expenses/new"
                    element={<AddExpensePage />}
                  />
                  <Route
                    path="/trips/:tripId/expenses/:expenseId/edit"
                    element={<EditExpensePage />}
                  />
                </Route>

                <Route
                  path="*"
                  element={<PlaceholderPage title="Page not found" />}
                />
              </Route>
            </Routes>
          </UnauthorizedRedirect>
        </AuthProvider>
      </BrowserRouter>
      <Toaster richColors closeButton />
    </QueryClientProvider>
  )
}

export default App

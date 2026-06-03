import { Link, NavLink, Outlet, useNavigate } from "react-router-dom"
import { LogOut, Wallet } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useAuth } from "@/hooks/useAuth"
import { cn } from "@/lib/utils"

export function Layout() {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate("/login")
  }

  return (
    <div className="min-h-svh bg-background text-foreground">
      <header className="border-b">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-4 sm:px-6 sm:py-5">
          <Link
            to="/"
            className="flex items-center gap-2 transition-opacity hover:opacity-80"
          >
            <div className="grid size-9 place-items-center rounded-xl bg-primary text-primary-foreground">
              <Wallet className="size-5" />
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-lg font-semibold tracking-tight">
                Bill Buddy
              </span>
              <span className="text-xs text-muted-foreground">
                Split trips. Settle up.
              </span>
            </div>
          </Link>

          {isAuthenticated ? (
            <nav className="flex items-center gap-1 sm:gap-2">
              <NavLink
                to="/"
                end
                className={({ isActive }) =>
                  cn(
                    "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                  )
                }
              >
                All trips
              </NavLink>
              <NavLink
                to="/trips/new"
                className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
              >
                New trip
              </NavLink>
              <div className="hidden items-center gap-2 pl-2 sm:flex">
                <span
                  className="max-w-[160px] truncate text-xs text-muted-foreground"
                  title={user?.email}
                >
                  {user?.email}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleLogout}
                  aria-label="Log out"
                  className="text-muted-foreground"
                >
                  <LogOut className="size-4" />
                </Button>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleLogout}
                aria-label="Log out"
                className="text-muted-foreground sm:hidden"
              >
                <LogOut className="size-4" />
              </Button>
            </nav>
          ) : (
            <nav className="flex items-center gap-2">
              <NavLink
                to="/login"
                className="rounded-lg px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground"
              >
                Sign in
              </NavLink>
              <NavLink
                to="/signup"
                className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90"
              >
                Get started
              </NavLink>
            </nav>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-10">
        <Outlet />
      </main>
      <footer className="border-t">
        <div className="mx-auto max-w-5xl px-4 py-5 text-xs text-muted-foreground sm:px-6">
          Bill Buddy · built with FastAPI + React
        </div>
      </footer>
    </div>
  )
}

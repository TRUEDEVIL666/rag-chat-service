"use client"

import { type ReactNode, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { Sidebar } from "./sidebar"

export function DashboardLayout({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading, user } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/auth/login")
      return
    }

    const isAdmin = user?.role === "admin"
    const currentPath = window.location.pathname

    if (
      !isAdmin &&
      (currentPath.includes("/dashboard") ||
        currentPath.includes("/users") ||
        currentPath.includes("/knowledge-base"))
    ) {
      router.push("/chat")
    }
  }, [isAuthenticated, isLoading, user, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="flex gap-4 min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 lg:ml-0 pt-16 lg:pt-0">
        <div className="p-8">{children}</div>
      </main>
    </div>
  )
}

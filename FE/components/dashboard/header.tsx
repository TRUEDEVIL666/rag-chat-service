"use client"

import { useAuth } from "@/lib/auth-context"
import { Card } from "@/components/ui/card"

export function DashboardHeader() {
  const { user } = useAuth()

  return (
    <Card className="mb-6">
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-muted-foreground">Welcome back, {user?.email}</p>
      </div>
    </Card>
  )
}

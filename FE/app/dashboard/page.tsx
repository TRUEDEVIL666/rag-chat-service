import { DashboardLayout } from "@/components/dashboard/layout"
import { DashboardHeader } from "@/components/dashboard/header"
import { Card } from "@/components/ui/card"

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <DashboardHeader />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card className="p-6">
          <div className="text-sm text-muted-foreground mb-2">Total Users</div>
          <div className="text-3xl font-bold">0</div>
        </Card>
        <Card className="p-6">
          <div className="text-sm text-muted-foreground mb-2">Knowledge Bases</div>
          <div className="text-3xl font-bold">0</div>
        </Card>
        <Card className="p-6">
          <div className="text-sm text-muted-foreground mb-2">Active Bots</div>
          <div className="text-3xl font-bold">0</div>
        </Card>
        <Card className="p-6">
          <div className="text-sm text-muted-foreground mb-2">Total Messages</div>
          <div className="text-3xl font-bold">0</div>
        </Card>
      </div>

      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">System Status</h2>
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">API Status</span>
            <span className="text-green-600">Healthy</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Database</span>
            <span className="text-green-600">Connected</span>
          </div>
        </div>
      </Card>
    </DashboardLayout>
  )
}

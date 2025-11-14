import { DashboardLayout } from "@/components/dashboard/layout"
import { Button } from "@/components/ui/button"
import { KnowledgeBaseList } from "@/components/knowledge-base/kb-list"
import { Plus } from "lucide-react"
import Link from "next/link"

export default function KnowledgeBasePage() {
  return (
    <DashboardLayout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Knowledge Bases</h1>
          <p className="text-muted-foreground">Manage subjects for your RAG system</p>
        </div>
        <Link href="/knowledge-base/create">
          <Button className="gap-2">
            <Plus size={18} />
            New Knowledge Base
          </Button>
        </Link>
      </div>

      <KnowledgeBaseList />
    </DashboardLayout>
  )
}

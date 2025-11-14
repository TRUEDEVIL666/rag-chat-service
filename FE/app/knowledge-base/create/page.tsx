import { DashboardLayout } from "@/components/dashboard/layout"
import { KnowledgeBaseCreateForm } from "@/components/knowledge-base/kb-create-form"

export default function CreateKnowledgeBasePage() {
  return (
    <DashboardLayout>
      <div className="max-w-2xl">
        <KnowledgeBaseCreateForm />
      </div>
    </DashboardLayout>
  )
}

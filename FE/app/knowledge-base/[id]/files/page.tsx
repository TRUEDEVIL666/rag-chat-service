"use client"

import { useParams } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard/layout"
import { FileUploader } from "@/components/file-manager/file-uploader"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export default function FileManagementPage() {
  const params = useParams()
  const id = params.id as string

  return (
    <DashboardLayout>
      <div className="mb-6">
        <Link href={`/knowledge-base/${id}`}>
          <Button variant="outline" className="mb-4 bg-transparent">
            ← Back
          </Button>
        </Link>
        <h1 className="text-3xl font-bold mb-2">File Management</h1>
        <p className="text-muted-foreground">Upload and manage documents for this knowledge base</p>
      </div>

      <FileUploader knowledgeBaseId={id} />
    </DashboardLayout>
  )
}

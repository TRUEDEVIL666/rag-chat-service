"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard/layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { apiClient } from "@/lib/api-client"
import { FileText } from "lucide-react"

export default function KnowledgeBaseDetailPage() {
  const params = useParams()
  const id = params.id as string
  const [kb, setKb] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    fetchKnowledgeBase()
  }, [id])

  const fetchKnowledgeBase = async () => {
    try {
      setIsLoading(true)
      const response = await apiClient.get(`/knowledge_bases/${id}`)
      setKb(response)
    } catch (err: any) {
      setError(err.message || "Failed to fetch knowledge base")
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="text-center py-12">Loading...</div>
      </DashboardLayout>
    )
  }

  if (error) {
    return (
      <DashboardLayout>
        <Card className="p-6 text-destructive">Error: {error}</Card>
      </DashboardLayout>
    )
  }

  if (!kb) {
    return (
      <DashboardLayout>
        <Card className="p-6">Knowledge base not found</Card>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="mb-6">
        <Link href="/knowledge-base">
          <Button variant="outline" className="mb-4 bg-transparent">
            ← Back
          </Button>
        </Link>
        <h1 className="text-3xl font-bold mb-2">{kb.name}</h1>
        <p className="text-muted-foreground">{kb.description}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card className="p-6">
          <div className="text-sm text-muted-foreground mb-2">Documents</div>
          <div className="text-3xl font-bold">{kb.document_count}</div>
        </Card>
        <Card className="p-6">
          <div className="text-sm text-muted-foreground mb-2">Words</div>
          <div className="text-3xl font-bold">{kb.word_count.toLocaleString()}</div>
        </Card>
        <Card className="p-6">
          <div className="text-sm text-muted-foreground mb-2">Permission</div>
          <Badge variant="outline" className="capitalize">
            {kb.permission}
          </Badge>
        </Card>
        <Card className="p-6">
          <div className="text-sm text-muted-foreground mb-2">Indexing</div>
          <Badge variant="outline" className="capitalize">
            {kb.indexing_technique}
          </Badge>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <FileText size={20} />
            Files
          </CardTitle>
          <Link href={`/knowledge-base/${id}/files`}>
            <Button>Manage Files</Button>
          </Link>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">No files uploaded yet</p>
        </CardContent>
      </Card>
    </DashboardLayout>
  )
}

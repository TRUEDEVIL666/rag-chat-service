"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { MoreHorizontal } from "lucide-react"
import { apiClient, type KnowledgeBase, type KnowledgeBaseListResponse } from "@/lib/api-client"
import { Card } from "@/components/ui/card"

export function KnowledgeBaseList() {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const [page, setPage] = useState(1)
  const router = useRouter()

  useEffect(() => {
    fetchKnowledgeBases()
  }, [page])

  const fetchKnowledgeBases = async () => {
    try {
      setIsLoading(true)
      const response = await apiClient.get<KnowledgeBaseListResponse>(`/knowledge_bases?page=${page}&limit=10`)
      setKbs(response.data)
    } catch (err: any) {
      setError(err.message || "Failed to fetch knowledge bases")
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this knowledge base?")) return

    try {
      await apiClient.delete(`/knowledge_bases/${id}`)
      setKbs(kbs.filter((kb) => kb.id !== id))
    } catch (err: any) {
      setError(err.message || "Failed to delete knowledge base")
    }
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-destructive">Error: {error}</div>
      </Card>
    )
  }

  return (
    <Card>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Documents</TableHead>
              <TableHead>Words</TableHead>
              <TableHead>Permission</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  Loading knowledge bases...
                </TableCell>
              </TableRow>
            ) : kbs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                  No knowledge bases found
                </TableCell>
              </TableRow>
            ) : (
              kbs.map((kb) => (
                <TableRow key={kb.id}>
                  <TableCell className="font-medium">{kb.name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{kb.description || "-"}</TableCell>
                  <TableCell>{kb.document_count}</TableCell>
                  <TableCell>{kb.word_count.toLocaleString()}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">
                      {kb.permission}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal size={18} />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => router.push(`/knowledge-base/${kb.id}`)}>
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => router.push(`/knowledge-base/${kb.id}/files`)}>
                          Manage Files
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleDelete(kb.id)} className="text-destructive">
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </Card>
  )
}

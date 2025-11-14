"use client"

import { useState, useEffect } from "react"
import { apiClient, type KnowledgeBase, type KnowledgeBaseListResponse } from "@/lib/api-client"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface BotSelectorProps {
  value?: string
  onChange: (value: string) => void
}

export function BotSelector({ value, onChange }: BotSelectorProps) {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchKnowledgeBases()
  }, [])

  const fetchKnowledgeBases = async () => {
    try {
      setIsLoading(true)
      const response = await apiClient.get<KnowledgeBaseListResponse>("/knowledge_bases?limit=100")
      setKbs(response.data)
    } catch (error) {
      console.error("Failed to fetch knowledge bases:", error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Select value={value || ""} onValueChange={onChange}>
      <SelectTrigger>
        <SelectValue placeholder="Select a knowledge base..." />
      </SelectTrigger>
      <SelectContent>
        {isLoading ? (
          <SelectItem value="loading" disabled>
            Loading...
          </SelectItem>
        ) : kbs.length === 0 ? (
          <SelectItem value="empty" disabled>
            No knowledge bases available
          </SelectItem>
        ) : (
          kbs.map((kb) => (
            <SelectItem key={kb.id} value={kb.id}>
              {kb.name}
            </SelectItem>
          ))
        )}
      </SelectContent>
    </Select>
  )
}

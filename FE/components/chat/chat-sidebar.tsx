"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/lib/auth-context"
import { apiClient, type BotResponse } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Plus, Trash2 } from "lucide-react"

interface ChatSidebarProps {
  selectedBotId?: string
  onSelectBot: (botId: string) => void
  onNewChat: () => void
}

export function ChatSidebar({ selectedBotId, onSelectBot, onNewChat }: ChatSidebarProps) {
  const [bots, setBots] = useState<BotResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { user } = useAuth()

  useEffect(() => {
    fetchBots()
  }, [])

  const fetchBots = async () => {
    try {
      setIsLoading(true)
      const response = await apiClient.get<BotResponse[]>("/bots")
      setBots(response)
      if (response.length > 0 && !selectedBotId) {
        onSelectBot(response[0].id)
      }
    } catch (error) {
      console.error("Failed to fetch bots:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteBot = async (id: string) => {
    if (!confirm("Delete this chat?")) return

    try {
      await apiClient.delete(`/bots/${id}`)
      setBots(bots.filter((bot) => bot.id !== id))
      if (selectedBotId === id) {
        onNewChat()
      }
    } catch (error) {
      console.error("Failed to delete bot:", error)
    }
  }

  return (
    <div className="flex flex-col h-full bg-card border-r border-border">
      <div className="p-4 border-b border-border">
        <Button className="w-full gap-2" onClick={onNewChat}>
          <Plus size={18} />
          New Chat
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {isLoading ? (
          <p className="text-sm text-muted-foreground text-center py-4">Loading chats...</p>
        ) : bots.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">No chats yet</p>
        ) : (
          bots.map((bot) => (
            <div
              key={bot.id}
              className={`p-3 rounded-lg border transition-colors cursor-pointer group flex items-center justify-between ${
                selectedBotId === bot.id
                  ? "bg-primary text-primary-foreground border-primary"
                  : "border-border hover:bg-secondary"
              }`}
              onClick={() => onSelectBot(bot.id)}
            >
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate text-sm">{bot.name}</p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleDeleteBot(bot.id)
                }}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-destructive/20 rounded transition-opacity"
              >
                <Trash2 size={16} className="text-destructive" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { apiClient } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { BotSelector } from "./bot-selector"
import { Send, Loader } from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [selectedKB, setSelectedKB] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [botId, setBotId] = useState<string>("")
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim() || !selectedKB) {
      alert("Please select a knowledge base and enter a message")
      return
    }

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      let currentBotId = botId

      // Create bot if needed
      if (!currentBotId) {
        const botResponse = await apiClient.post("/bots", {
          name: `Chat - ${new Date().toLocaleString()}`,
          description: "RAG Chat",
          knowledge_base_id: selectedKB,
        })
        currentBotId = botResponse.id
        setBotId(currentBotId)
      }

      // Send message to bot
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/bots/${currentBotId}/ask`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
          },
          body: JSON.stringify({
            message: userMessage.content,
            streaming: false,
          }),
        },
      )

      if (!response.ok) {
        throw new Error("Failed to send message")
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.answer || "No response",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error: any) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `Error: ${error.message}`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full gap-4">
      <Card className="p-4">
        <label className="text-sm font-medium mb-2 block">Knowledge Base</label>
        <BotSelector value={selectedKB} onChange={setSelectedKB} />
      </Card>

      <Card className="flex-1 flex flex-col overflow-hidden min-h-0"> {/* Added min-h-0 */}
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4 pb-4 h-0"> {/* Removed h-full */}
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full text-muted-foreground text-center py-12">
                <p>Select a knowledge base and start chatting with your RAG bot</p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-xs px-4 py-2 rounded-lg ${
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-secondary text-secondary-foreground"
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    <span className="text-xs opacity-70 mt-1 block">
                      {message.timestamp.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex gap-3">
                <div className="bg-secondary text-secondary-foreground px-4 py-2 rounded-lg">
                  <Loader className="animate-spin" size={18} />
                </div>
              </div>
            )}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>

        <form onSubmit={handleSendMessage} className="border-t border-border p-4">
          <div className="flex gap-2">
            <Input
              placeholder="Type a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading || !selectedKB}
              className="flex-1"
            />
            <Button type="submit" disabled={isLoading || !selectedKB || !input.trim()} size="sm">
              <Send size={18} />
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

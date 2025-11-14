"use client"

import { ChatSidebar } from "@/components/chat/chat-sidebar"
import { ChatInterface } from "@/components/chat/chat-interface"
import { useState } from "react"
import { Sidebar } from "@/components/dashboard/sidebar" // Import Sidebar
import { useAuth } from "@/lib/auth-context" // Import useAuth
import { useRouter } from "next/navigation" // Import useRouter
import { useEffect } from "react"

export default function ChatPage() {
  const [selectedBotId, setSelectedBotId] = useState<string | undefined>()
  const { isLoading, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/auth/login")
    }
  }, [isLoading, isAuthenticated, router])

  const handleNewChat = () => {
    setSelectedBotId(undefined)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen flex bg-background"> {/* Removed flex-col */}
      {/* Removed TopNavbar */}
      <Sidebar />
      <main className="flex-1 md:ml-2 overflow-auto p-8">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 h-[calc(100vh-120px)]">
            <div className="lg:col-span-1 hidden lg:block h-full">
              <ChatSidebar selectedBotId={selectedBotId} onSelectBot={setSelectedBotId} onNewChat={handleNewChat} />
            </div>
            <div className="lg:col-span-4 h-full">
              <ChatInterface />
            </div>
          </div>
        </main>
      </div>
  )
}

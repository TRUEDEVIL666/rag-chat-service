"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { Button } from "@/components/ui/button"
import { LayoutDashboard, BookOpen, MessageSquare, Users, LogOut, Menu, X } from "lucide-react"
import { useState } from "react"

export function Sidebar() {
  const pathname = usePathname()
  const { user, logout } = useAuth()
  const [isOpen, setIsOpen] = useState(false)

  console.log("Sidebar - user:", user)
  console.log("Sidebar - user?.role:", user?.role)
  const isAdmin = user?.role === "admin"
  console.log("Sidebar - isAdmin:", isAdmin)

  const navigationItems = [
    {
      name: "Chat",
      href: "/chat",
      icon: MessageSquare,
      visible: true,
    },
    {
      name: "Dashboard",
      href: "/dashboard",
      icon: LayoutDashboard,
      visible: isAdmin,
    },
    {
      name: "Knowledge Base",
      href: "/knowledge-base",
      icon: BookOpen,
      visible: isAdmin,
    },
    {
      name: "Users",
      href: "/users",
      icon: Users,
      visible: isAdmin,
    },
  ]

  const visibleItems = navigationItems.filter((item) => item.visible)

  return (
    <>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 left-4 z-40 lg:hidden p-2 rounded-md bg-primary text-primary-foreground"
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      <aside
        className={`fixed inset-y-0 left-0 z-30 w-72 bg-background border-r-2 border-border/50 transform transition-transform duration-200 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0 lg:static`}
      >
        <div className="flex flex-col h-full">
          <div className="p-6 border-b border-border">
            <h1 className="text-xl font-bold text-primary">RAG Platform</h1>
          </div>

          <nav className="flex-1 overflow-y-auto p-4 space-y-2">
            {visibleItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href || pathname.startsWith(item.href + "/")

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsOpen(false)}
                  className={`flex items-center gap-4 px-5 py-2.5 rounded-lg transition-colors ${
                    isActive ? "bg-primary text-primary-foreground shadow-neon-glow" : "text-foreground hover:bg-accent/20"
                  }`}
                >
                  <Icon size={20} />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </nav>

          <div className="p-4 border-t border-border space-y-2">
            <div className="px-4 py-2 text-sm text-muted-foreground">
              <p className="font-medium text-foreground">{user?.email}</p>
              <p className="capitalize">{user?.role}</p>
            </div>
            <Button variant="outline" className="w-full justify-start gap-2 bg-transparent" onClick={logout}>
              <LogOut size={18} />
              Logout
            </Button>
          </div>
        </div>
      </aside>

      {isOpen && <div className="fixed inset-0 z-20 bg-black/50 lg:hidden" onClick={() => setIsOpen(false)} />}
    </>
  )
}

"use client"

import { useEffect, useState } from "react"
import { DashboardLayout } from "@/components/dashboard/layout"
import { Button } from "@/components/ui/button"
import UsersTable from "@/components/users/users-table"
import { Plus } from "lucide-react"
import { apiClient, type User } from "@/lib/api-client"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface KnowledgeBase {
  id: string
  name: string
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isLoadingUsers, setIsLoadingUsers] = useState(true)
  const [newUser, setNewUser] = useState({
    email: "",
    password: "",
    knowledge_base_id: "",
    role: "user",
  })

  const fetchUsers = async () => {
    setIsLoadingUsers(true) // Set loading to true before fetching
    try {
      const response = await apiClient.get<User[]>("/users")
      setUsers(response)
    } catch (error) {
      console.error("Failed to fetch users:", error)
    } finally {
      setIsLoadingUsers(false) // Set loading to false after fetching
    }
  }

  const fetchKnowledgeBases = async () => {
    try {
      const response = await apiClient.get<{ data: KnowledgeBase[] }>("/knowledge_bases")
      setKnowledgeBases(response.data)
    } catch (error) {
      console.error("Failed to fetch knowledge bases:", error)
    }
  }

  useEffect(() => {
    (async () => {
      await fetchUsers()
      await fetchKnowledgeBases()
    })()
  }, [])

  const handleAddUser = async () => {
    try {
      await apiClient.post("/users", newUser)
      fetchUsers() // Refresh the user list
      setIsDialogOpen(false) // Close the dialog
    } catch (error) {
      console.error("Failed to add user:", error)
    }
  }

  const handleDeleteUser = async (userId: string) => {
    try {
      await apiClient.delete(`/users/${userId}`)
      fetchUsers() // Refresh the user list
    } catch (error) {
      console.error("Failed to delete user:", error)
    }
  }

  const handleBulkDeleteUsers = async (userIds: string[]) => {
    try {
      await apiClient.delete("/users", userIds)
      fetchUsers() // Refresh the user list
    } catch (error) {
      console.error("Failed to delete users:", error)
    }
  }

  return (
    <DashboardLayout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Users</h1>
          <p className="text-muted-foreground">Manage users and their roles</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2">
              <Plus size={18} />
              Add User
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New User</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="email" className="text-right">
                  Email
                </Label>
                <Input
                  id="email"
                  value={newUser.email}
                  onChange={(e) =>
                    setNewUser({ ...newUser, email: e.target.value })
                  }
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="password" className="text-right">
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  value={newUser.password}
                  onChange={(e) =>
                    setNewUser({ ...newUser, password: e.target.value })
                  }
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="kb" className="text-right">
                  Knowledge Base
                </Label>
                <Select
                  onValueChange={(value) =>
                    setNewUser({ ...newUser, knowledge_base_id: value })
                  }
                >
                  <SelectTrigger className="col-span-3">
                    <SelectValue placeholder="Select a knowledge base" />
                  </SelectTrigger>
                  <SelectContent>
                    {knowledgeBases.map((kb) => (
                      <SelectItem key={kb.id} value={kb.id}>
                        {kb.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button onClick={handleAddUser}>Add User</Button>
          </DialogContent>
        </Dialog>
      </div>

      <UsersTable
        users={users}
        onUserDeleted={handleDeleteUser}
        onBulkDelete={handleBulkDeleteUsers}
        isLoadingUsers={isLoadingUsers}
      />
    </DashboardLayout>
  )
}
"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { useRouter } from "next/navigation" // Import useRouter
import { apiClient, type LoginResponse } from "./api-client"

interface User {
  id: string
  email: string
  tenant_id: string
  role: string
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, tenant_id?: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter() // Initialize useRouter

  useEffect(() => {
    const token = localStorage.getItem("auth_token")
    const userData = localStorage.getItem("user_data")

    if (token && userData) {
      try {
        apiClient.setToken(token)
        setUser(JSON.parse(userData))
      } catch (error) {
        localStorage.removeItem("auth_token")
        localStorage.removeItem("user_data")
      }
    }
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const response = await apiClient.post<LoginResponse>("/login", {
        email,
        password,
      })

      localStorage.setItem("auth_token", response.token) // Use response.token
      const userData = {
        id: response.user.id, // Extract from response.user
        email: response.user.email, // Extract from response.user
        tenant_id: response.user.tenant_id, // Extract from response.user
        role: response.user.role, // Extract from response.user
      }
      localStorage.setItem("user_data", JSON.stringify(userData))
      apiClient.setToken(response.token) // Use response.token
      setUser(userData)

      // Redirect based on role
      if (userData.role === "admin") {
        router.push("/dashboard")
      } else {
        router.push("/chat")
      }
    } catch (error) {
      throw error
    }
  }

  const register = async (email: string, password: string, tenant_id?: string) => {
    try {
      await apiClient.post("/register", {
        email,
        password,
        tenant_id,
      })
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem("auth_token")
    localStorage.removeItem("user_data")
    apiClient.setToken("")
    setUser(null)
    router.push("/auth/login") // Redirect to login page after logout
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within AuthProvider")
  }
  return context
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"
console.log("API_BASE_URL:", API_BASE_URL)

export interface LoginResponse {
  access_token: string
  token_type: string
  user_id: string
  tenant_id: string
  email: string
  role: string
}

export interface RegisterRequest {
  email: string
  password: string
  tenant_id?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface User {
  id: string
  email: string
  role: string
  created_at: string
  updated_at?: string
}

export interface KnowledgeBase {
  id: string
  name: string
  description?: string
  permission: string
  indexing_technique: string
  app_count: number
  document_count: number
  word_count: number
  created_at: number
  updated_at?: number
  embedding_model?: string
  embedding_model_provider?: string
  embedding_available: boolean
}

export interface KnowledgeBaseListResponse {
  data: KnowledgeBase[]
  has_more: boolean
  limit: number
  total: number
  page: number
}

export interface BotResponse {
  id: string
  name: string
  description?: string
  // ... other bot fields
}

class ApiClient {
  private token: string | null = null

  setToken(token: string) {
    this.token = token
  }

  private getHeaders(isFormData = false) {
    const token = localStorage.getItem("auth_token")
    const headers: HeadersInit = {
      ...(token && { Authorization: `Bearer ${token}` }),
      ...(!isFormData && { "Content-Type": "application/json" }),
    }
    return headers
  }

  private _handleUnauthorized() {
    localStorage.removeItem("auth_token")
    localStorage.removeItem("user_data")
    window.location.href = "/auth/login"
  }

  async post<T>(endpoint: string, data?: any, isFormData = false): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: this.getHeaders(isFormData),
      body: isFormData ? data : JSON.stringify(data),
    })

    if (400 <= response.status && response.status < 500) {
      this._handleUnauthorized()
      // Return a promise that will never resolve, to prevent further processing
      return new Promise(() => {})
    }

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "API error")
    }

    return response.json()
  }

  async postFormData<T>(endpoint: string, formData: FormData): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: {
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
      },
      body: formData,
    })

    if (response.status === 401) {
      this._handleUnauthorized()
      return new Promise(() => {})
    }

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "API error")
    }

    return response.json()
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "GET",
      headers: this.getHeaders(),
    })

    if (response.status === 401) {
      this._handleUnauthorized()
      return new Promise(() => {})
    }

    if (response.status === 403) {
      throw new Error("Forbidden: You don't have permission to access this resource.")
    }

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "API error")
    }

    return response.json()
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "PATCH",
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    })

    if (response.status === 401) {
      this._handleUnauthorized()
      return new Promise(() => {})
    }

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "API error")
    }

    return response.json()
  }

  async delete<T>(endpoint: string, data?: any): Promise<T | void> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    })

    if (response.status === 401) {
      this._handleUnauthorized()
      return new Promise(() => {})
    }

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "API error")
    }

    if (response.status === 204) {
      return
    }

    return response.json()
  }
}

export const apiClient = new ApiClient()

/**
 * API client for the Research Dossier backend.
 */

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Types
export interface User {
  id: string
  email: string
  name: string | null
  credits: number
  is_verified: boolean
  created_at: string
}

export interface ResearchJob {
  id: string
  target: string
  target_type: 'company' | 'person'
  depth: 'quick' | 'standard' | 'deep'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  credits_used: number
  error_message: string | null
  report_url: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface PricingTier {
  id: string
  name: string
  credits: number
  price_cents: number
}

export interface Payment {
  id: string
  amount_cents: number
  credits_purchased: number
  status: string
  created_at: string
}

// Token management
let authToken: string | null = null

export function setAuthToken(token: string | null) {
  authToken = token
  if (token) {
    localStorage.setItem('auth_token', token)
  } else {
    localStorage.removeItem('auth_token')
  }
}

export function getAuthToken(): string | null {
  if (authToken) return authToken
  if (typeof window !== 'undefined') {
    authToken = localStorage.getItem('auth_token')
  }
  return authToken
}

// API helper
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken()

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// Unified API object
export const api = {
  // Auth
  async register(email: string, password: string, name: string) {
    const data = await apiFetch<{ access_token: string; expires_in: number }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    })
    setAuthToken(data.access_token)
    return data
  },

  async login(email: string, password: string) {
    const data = await apiFetch<{ access_token: string; expires_in: number }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    setAuthToken(data.access_token)
    return data
  },

  async logout() {
    try {
      await apiFetch('/api/auth/logout', { method: 'POST' })
    } finally {
      setAuthToken(null)
    }
  },

  // OAuth
  getGoogleAuthUrl() {
    return `${API_URL}/api/auth/google`
  },

  async getOAuthStatus() {
    return apiFetch<{ google: boolean }>('/api/auth/oauth/status')
  },

  // Set token directly (for OAuth callback)
  setToken(token: string) {
    setAuthToken(token)
  },

  async getMe(): Promise<User> {
    return apiFetch<User>('/api/auth/me')
  },

  // Research
  async createResearch(data: { target: string; target_type: 'company' | 'person'; depth: string }) {
    return apiFetch<ResearchJob>('/api/research', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async listResearch(status?: string, limit = 20, offset = 0) {
    const params = new URLSearchParams()
    if (status) params.set('status_filter', status)
    params.set('limit', limit.toString())
    params.set('offset', offset.toString())
    return apiFetch<{ jobs: ResearchJob[]; total: number }>(`/api/research?${params}`)
  },

  async getResearch(id: string) {
    return apiFetch<ResearchJob>(`/api/research/${id}`)
  },

  getDownloadUrl(id: string) {
    const token = getAuthToken()
    return `${API_URL}/api/research/${id}/download${token ? `?token=${token}` : ''}`
  },

  async deleteResearch(id: string) {
    const token = getAuthToken()
    const response = await fetch(`${API_URL}/api/research/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Delete failed' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }
    return true
  },

  // Payments
  async createCheckout(tier: string) {
    return apiFetch<{ checkout_url: string; session_id: string }>('/api/payments/create-checkout', {
      method: 'POST',
      body: JSON.stringify({ tier }),
    })
  },

  async getPaymentHistory(limit = 20) {
    return apiFetch<{ payments: Payment[] }>(`/api/payments/history?limit=${limit}`)
  },

  async getTiers() {
    return apiFetch<{ tiers: PricingTier[] }>('/api/payments/tiers')
  },

  // Users
  async getCredits() {
    return apiFetch<{ credits: number; pending_jobs: number }>('/api/users/credits')
  },

  async updateProfile(data: { name: string }) {
    return apiFetch<User>('/api/users/profile', {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  async changePassword(data: { current_password: string; new_password: string }) {
    return apiFetch<{ message: string }>('/api/users/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
}

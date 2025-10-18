"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface TokenContextType {
  token: string | null
  isLoading: boolean
  refreshToken: () => Promise<void>
}

const TokenContext = createContext<TokenContextType | undefined>(undefined)

export function TokenProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshToken = async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${backendUrl}/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: 'admin', // Use admin credentials automatically
          password: 'secret',
        }),
      })

      if (response.ok) {
        const data = await response.json()
        const { access_token } = data
        
        // Store token in localStorage for persistence
        localStorage.setItem('backend_token', access_token)
        setToken(access_token)
      } else {
        console.error('Failed to get token from backend')
        setToken(null)
      }
    } catch (error) {
      console.error('Error getting token:', error)
      setToken(null)
    }
  }

  // Get token on mount
  useEffect(() => {
    const getToken = async () => {
      // First try to get existing token from localStorage
      const storedToken = localStorage.getItem('backend_token')
      
      if (storedToken) {
        // Verify token is still valid
        try {
          const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
          const response = await fetch(`${backendUrl}/users/me`, {
            headers: {
              'Authorization': `Bearer ${storedToken}`,
            },
          })

          if (response.ok) {
            setToken(storedToken)
            setIsLoading(false)
            return
          }
        } catch (error) {
          console.error('Token verification failed:', error)
        }
      }

      // If no valid token, get a new one
      await refreshToken()
      setIsLoading(false)
    }

    getToken()
  }, [])

  const value: TokenContextType = {
    token,
    isLoading,
    refreshToken,
  }

  return (
    <TokenContext.Provider value={value}>
      {children}
    </TokenContext.Provider>
  )
}

export function useToken() {
  const context = useContext(TokenContext)
  if (context === undefined) {
    throw new Error('useToken must be used within a TokenProvider')
  }
  return context
}

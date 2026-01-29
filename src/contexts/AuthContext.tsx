import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'manager' | 'operator'
}

export interface AuthState {
  user: User | null
  companyId: string
  isAuthenticated: boolean
  isLoading: boolean
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setCompanyId: (companyId: string) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const STORAGE_KEY = 'new-voice-auth'
const DEFAULT_COMPANY_ID = 'default-company'

interface StoredAuth {
  user: User | null
  companyId: string
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    companyId: DEFAULT_COMPANY_ID,
    isAuthenticated: false,
    isLoading: true,
  })

  // Load auth state from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        const parsed: StoredAuth = JSON.parse(stored)
        setState({
          user: parsed.user,
          companyId: parsed.companyId || DEFAULT_COMPANY_ID,
          isAuthenticated: !!parsed.user,
          isLoading: false,
        })
      } catch {
        setState(prev => ({ ...prev, isLoading: false }))
      }
    } else {
      setState(prev => ({ ...prev, isLoading: false }))
    }
  }, [])

  // Save auth state to localStorage when it changes
  useEffect(() => {
    if (!state.isLoading) {
      const toStore: StoredAuth = {
        user: state.user,
        companyId: state.companyId,
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore))
    }
  }, [state.user, state.companyId, state.isLoading])

  const login = async (email: string, _password: string) => {
    // Simulated login - replace with actual API call
    // In production, this should call your auth API
    const mockUser: User = {
      id: 'user-1',
      email,
      name: email.split('@')[0],
      role: 'admin',
    }

    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500))

    setState({
      user: mockUser,
      companyId: DEFAULT_COMPANY_ID,
      isAuthenticated: true,
      isLoading: false,
    })
  }

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY)
    setState({
      user: null,
      companyId: DEFAULT_COMPANY_ID,
      isAuthenticated: false,
      isLoading: false,
    })
  }

  const setCompanyId = (companyId: string) => {
    setState(prev => ({ ...prev, companyId }))
  }

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
        setCompanyId,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function useCompanyId() {
  const { companyId } = useAuth()
  return companyId
}

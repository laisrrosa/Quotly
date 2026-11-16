import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { setUnauthorizedHandler, tokenStorage } from '../services/api.js'
import * as authService from '../services/auth.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // true enquanto verificamos se já existe um token salvo válido
  const [initializing, setInitializing] = useState(true)

  const logout = useCallback(() => {
    tokenStorage.clear()
    setUser(null)
  }, [])

  // Ao abrir o site: se houver token salvo, busca o usuário
  useEffect(() => {
    let cancelled = false
    async function restoreSession() {
      if (!tokenStorage.get()) {
        setInitializing(false)
        return
      }
      try {
        const me = await authService.getMe()
        if (!cancelled) setUser(me)
      } catch {
        tokenStorage.clear()
      } finally {
        if (!cancelled) setInitializing(false)
      }
    }
    restoreSession()
    return () => {
      cancelled = true
    }
  }, [])

  // Se qualquer requisição voltar 401, desloga
  useEffect(() => {
    setUnauthorizedHandler(() => {
      if (tokenStorage.get()) toast.error('Sua sessão expirou. Entre novamente.')
      logout()
    })
    return () => setUnauthorizedHandler(null)
  }, [logout])

  const login = useCallback(async (email, password) => {
    const { access_token } = await authService.login({ email, password })
    tokenStorage.set(access_token)
    const me = await authService.getMe()
    setUser(me)
    return me
  }, [])

  const register = useCallback(
    async (name, email, password) => {
      await authService.register({ name, email, password })
      return login(email, password)
    },
    [login],
  )

  const value = useMemo(
    () => ({ user, initializing, isAuthenticated: !!user, login, register, logout }),
    [user, initializing, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth precisa estar dentro de <AuthProvider>')
  return ctx
}

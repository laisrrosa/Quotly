import axios from 'axios'

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Enquanto o back-end não estiver pronto, deixe VITE_USE_MOCK=true no .env
export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'

const TOKEN_KEY = 'quotly_token'

// localStorage pode lançar erro (aba anônima, bloqueio), por isso o try/catch
export const tokenStorage = {
  get() {
    try {
      return localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  },
  set(token) {
    try {
      localStorage.setItem(TOKEN_KEY, token)
    } catch {
      /* ignora */
    }
  },
  clear() {
    try {
      localStorage.removeItem(TOKEN_KEY)
    } catch {
      /* ignora */
    }
  },
}

export const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
})

// Interceptor de requisição: anexa o JWT em todas as chamadas
api.interceptors.request.use((config) => {
  const token = tokenStorage.get()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor de resposta: se o token expirou (401), desloga o usuário
let unauthorizedHandler = null
export function setUnauthorizedHandler(fn) {
  unauthorizedHandler = fn
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && unauthorizedHandler) {
      unauthorizedHandler()
    }
    return Promise.reject(error)
  },
)

/**
 * Extrai uma mensagem amigável de um erro do axios.
 * O FastAPI devolve { detail: "texto" } ou { detail: [{ msg: "..." }] }.
 */
export function getErrorMessage(error, fallback = 'Algo deu errado. Tente novamente.') {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  if (error?.code === 'ECONNABORTED') return 'O servidor demorou para responder.'
  if (error?.message === 'Network Error') return 'Não foi possível conectar ao servidor.'
  return fallback
}

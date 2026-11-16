import { api, USE_MOCK, tokenStorage } from './api.js'
import * as mock from './mocks/mockServer.js'

// POST /api/auth/register  { name, email, password } -> { id, name, email }
export async function register(payload) {
  if (USE_MOCK) return mock.register(payload)
  const { data } = await api.post('/api/auth/register', payload)
  return data
}

// POST /api/auth/login  { email, password } -> { access_token, token_type }
export async function login(payload) {
  if (USE_MOCK) return mock.login(payload)
  const { data } = await api.post('/api/auth/login', payload)
  return data
}

// GET /api/auth/me -> { id, name, email }
export async function getMe() {
  if (USE_MOCK) return mock.me(tokenStorage.get())
  const { data } = await api.get('/api/auth/me')
  return data
}

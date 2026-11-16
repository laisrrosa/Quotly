import { api, USE_MOCK, tokenStorage } from './api.js'
import * as mock from './mocks/mockServer.js'

// POST /api/auth/register  { name, email, password } -> { id, name, email, ... }
// (a API exige senha com no mínimo 8 caracteres)
export async function register(payload) {
  if (USE_MOCK) return mock.register(payload)
  const { data } = await api.post('/api/auth/register', payload)
  return data
}

// POST /api/auth/login -> { access_token, token_type }
// A API usa o padrão OAuth2 do FastAPI: formulário (não JSON) com os campos
// "username" (que é o e-mail) e "password".
export async function login({ email, password }) {
  if (USE_MOCK) return mock.login({ email, password })
  const form = new URLSearchParams({ username: email, password })
  const { data } = await api.post('/api/auth/login', form)
  return data
}

// GET /api/auth/me -> { id, name, email, ... }
export async function getMe() {
  if (USE_MOCK) return mock.me(tokenStorage.get())
  const { data } = await api.get('/api/auth/me')
  return data
}

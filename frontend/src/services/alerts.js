import { alertCreateToApi, alertFromApi, alertUpdateToApi } from './adapters.js'
import { api, USE_MOCK, tokenStorage } from './api.js'
import * as mock from './mocks/mockServer.js'

// As rotas da API terminam com "/" (sem ela o FastAPI responde com redirecionamento)

// GET /api/alerts/ -> [Alert], do mais novo para o mais antigo
export async function listAlerts() {
  if (USE_MOCK) return mock.listAlerts(tokenStorage.get())
  const { data } = await api.get('/api/alerts/')
  return data.map(alertFromApi).sort((a, b) => b.createdAt.localeCompare(a.createdAt))
}

// POST /api/alerts/  { ticker, target_price, condition } -> Alert
export async function createAlert(payload) {
  if (USE_MOCK) return mock.createAlert(tokenStorage.get(), payload)
  const { data } = await api.post('/api/alerts/', alertCreateToApi(payload))
  return alertFromApi(data)
}

// PATCH /api/alerts/{id}  { target_price?, condition?, is_active? } -> Alert
// A API não permite trocar o ticker nem reativar um alerta já disparado.
export async function updateAlert(id, changes) {
  if (USE_MOCK) return mock.updateAlert(tokenStorage.get(), id, changes)
  const { data } = await api.patch(`/api/alerts/${id}`, alertUpdateToApi(changes))
  return alertFromApi(data)
}

// DELETE /api/alerts/{id}
export async function deleteAlert(id) {
  if (USE_MOCK) return mock.deleteAlert(tokenStorage.get(), id)
  await api.delete(`/api/alerts/${id}`)
}

export const CONDITION_LABELS = {
  above: 'Subir acima de',
  below: 'Cair abaixo de',
}

export const STATUS_LABELS = {
  active: 'Ativo',
  triggered: 'Disparado',
  disabled: 'Desativado',
}

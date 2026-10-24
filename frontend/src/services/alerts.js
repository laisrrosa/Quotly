import { api, USE_MOCK, tokenStorage } from './api.js'
import * as mock from './mocks/mockServer.js'

// GET /api/alerts -> [Alert]
export async function listAlerts() {
  if (USE_MOCK) return mock.listAlerts(tokenStorage.get())
  const { data } = await api.get('/api/alerts')
  return data
}

// POST /api/alerts  { ticker, targetPrice, condition } -> Alert
export async function createAlert(payload) {
  if (USE_MOCK) return mock.createAlert(tokenStorage.get(), payload)
  const { data } = await api.post('/api/alerts', payload)
  return data
}

// PATCH /api/alerts/{id}  { ticker?, targetPrice?, condition?, status? } -> Alert
export async function updateAlert(id, changes) {
  if (USE_MOCK) return mock.updateAlert(tokenStorage.get(), id, changes)
  const { data } = await api.patch(`/api/alerts/${id}`, changes)
  return data
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

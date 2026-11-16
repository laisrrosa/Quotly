import { api, USE_MOCK } from './api.js'
import * as mock from './mocks/mockServer.js'

// GET /api/quotes/{ticker}
export async function getQuote(ticker) {
  if (USE_MOCK) return mock.getQuote(ticker)
  const { data } = await api.get(`/api/quotes/${encodeURIComponent(ticker)}`)
  return data
}

// GET /api/quotes/{ticker}/history?range=7d|1mo|6mo|1y -> [{ date, close }]
export async function getHistory(ticker, range = '1mo') {
  if (USE_MOCK) return mock.getHistory(ticker, range)
  const { data } = await api.get(`/api/quotes/${encodeURIComponent(ticker)}/history`, {
    params: { range },
  })
  return data
}

export const RANGES = [
  { value: '7d', label: '7D' },
  { value: '1mo', label: '1M' },
  { value: '6mo', label: '6M' },
  { value: '1y', label: '1A' },
]

// Sugestões rápidas na tela de busca
export const POPULAR_TICKERS = ['PETR4', 'VALE3', 'ITUB4', 'WEGE3', 'AAPL', 'NVDA']

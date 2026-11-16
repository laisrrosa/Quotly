import { historyFromApi, quoteFromApi } from './adapters.js'
import { api, USE_MOCK } from './api.js'
import * as mock from './mocks/mockServer.js'

// A API devolve no máximo 100 pontos de histórico por chamada
const HISTORY_LIMIT = 100

// GET /api/stocks/{ticker} -> cotação mais recente gravada pelo worker
export async function getQuote(ticker) {
  if (USE_MOCK) return mock.getQuote(ticker)
  const { data } = await api.get(`/api/stocks/${encodeURIComponent(ticker)}`)
  return quoteFromApi(data)
}

// GET /api/stocks/{ticker}/history?limit=100 -> [{ date, close }]
// A API não filtra por período; o filtro (7d, 1mo...) é aplicado no adapter.
export async function getHistory(ticker, range = '1mo') {
  if (USE_MOCK) return mock.getHistory(ticker, range)
  const { data } = await api.get(`/api/stocks/${encodeURIComponent(ticker)}/history`, {
    params: { limit: HISTORY_LIMIT },
  })
  return historyFromApi(data, range)
}

export const RANGES = [
  { value: '7d', label: '7D' },
  { value: '1mo', label: '1M' },
  { value: '6mo', label: '6M' },
  { value: '1y', label: '1A' },
]

// Sugestões rápidas na tela de busca
export const POPULAR_TICKERS = ['PETR4', 'VALE3', 'ITUB4', 'WEGE3', 'AAPL', 'NVDA']

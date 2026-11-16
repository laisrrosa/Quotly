import axios from 'axios'
import { USE_MOCK } from './api.js'
import * as mock from './mocks/mockServer.js'

// API Java (Spring Boot) de análises financeiras. É um serviço separado da API
// Python, roda na porta 8085 e não exige login, por isso tem um axios próprio
// (sem o token JWT).
export const ANALYTICS_URL = import.meta.env.VITE_ANALYTICS_URL || 'http://localhost:8085'

const analyticsApi = axios.create({
  baseURL: ANALYTICS_URL,
  timeout: 10000,
})

// GET /api/analytics/simulate?ticker&initialAmount&monthlyContribution&months&annualRatePercent
// -> { ticker, initialAmount, monthlyContribution, months, annualRatePercent,
//      totalInvested, totalInterest, finalBalance }
export async function simulateInvestment(params) {
  if (USE_MOCK) return mock.simulate(params)
  const { data } = await analyticsApi.get('/api/analytics/simulate', { params })
  return data
}

// GET /api/analytics/variation?ticker&currentPrice&previousClose&targetPrice(opcional)
// -> { ticker, currentPrice, previousClose, absoluteChange, percentageChange,
//      trend: "UP" | "DOWN" | "NEUTRAL", distanceToTargetPercent }
export async function analyzeVariation({ ticker, currentPrice, previousClose, targetPrice }) {
  const params = { ticker, currentPrice, previousClose }
  if (targetPrice != null) params.targetPrice = targetPrice
  if (USE_MOCK) return mock.variation(params)
  const { data } = await analyticsApi.get('/api/analytics/variation', { params })
  return data
}

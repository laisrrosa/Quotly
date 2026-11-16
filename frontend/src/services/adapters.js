/**
 * Tradutores entre a API real (FastAPI do Integrante 1) e o formato usado pelas telas.
 *
 * O back-end usa snake_case, condição em MAIÚSCULAS e dois booleanos
 * (is_active / is_triggered). As telas usam camelCase, condição em minúsculas
 * e um único campo "status". Toda a conversão fica concentrada aqui, para que
 * os componentes não precisem saber como o back-end escreve os campos.
 */

// O back-end grava as datas em UTC, mas o SQLite devolve sem o "Z" no final.
// Sem o "Z" o navegador trataria o horário como local (3 horas de erro no Brasil).
export function toIsoUtc(value) {
  if (!value || typeof value !== 'string') return value ?? null
  const hasTimezone = /(Z|[+-]\d{2}:?\d{2})$/.test(value)
  return hasTimezone ? value : `${value}Z`
}

const round2 = (n) => Math.round(n * 100) / 100

// ---------- cotações ----------

// StockResponse -> quote usado no QuoteCard
export function quoteFromApi(q) {
  const price = q.price
  const pct = q.change_percent ?? null

  // A API só manda a variação percentual; o fechamento anterior e a variação
  // em reais são calculados a partir dela.
  let previousClose = null
  let change = null
  if (pct != null && pct > -100) {
    previousClose = round2(price / (1 + pct / 100))
    change = round2(price - previousClose)
  }

  return {
    ticker: q.ticker,
    name: null, // a API não informa o nome da empresa
    currency: 'BRL', // a API não informa a moeda
    price,
    change,
    changePercent: pct,
    previousClose,
    open: q.open_price ?? null,
    high: q.high_price ?? null,
    low: q.low_price ?? null,
    updatedAt: toIsoUtc(q.timestamp),
  }
}

const RANGE_DAYS = { '7d': 7, '1mo': 30, '6mo': 182, '1y': 365 }

// StockResponse[] -> [{ date, close }] usado no PriceChart.
// A API devolve os últimos N registros (não aceita período), então o filtro
// por período é feito aqui.
export function historyFromApi(list, range = '1mo', now = Date.now()) {
  const days = RANGE_DAYS[range] ?? 30
  const cutoff = now - days * 24 * 60 * 60 * 1000
  return list
    .map((q) => ({ date: toIsoUtc(q.timestamp), close: q.price }))
    .filter((p) => new Date(p.date).getTime() >= cutoff)
}

// ---------- alertas ----------

function statusFromApi(a) {
  if (a.is_triggered) return 'triggered'
  return a.is_active ? 'active' : 'disabled'
}

// AlertResponse -> alerta usado nas telas
export function alertFromApi(a) {
  return {
    id: a.id,
    ticker: a.ticker,
    targetPrice: a.target_price,
    condition: String(a.condition).toLowerCase(), // "ABOVE" -> "above"
    status: statusFromApi(a),
    createdAt: toIsoUtc(a.created_at),
    triggeredAt: null, // a API não guarda a data do disparo
  }
}

// { ticker, targetPrice, condition } -> AlertCreate
export function alertCreateToApi({ ticker, targetPrice, condition }) {
  return {
    ticker,
    target_price: Number(targetPrice),
    condition: String(condition).toUpperCase(),
  }
}

// { targetPrice?, condition?, status? } -> AlertUpdate
// O PATCH da API não aceita trocar o ticker, então ele é ignorado.
export function alertUpdateToApi(changes) {
  const body = {}
  if (changes.targetPrice !== undefined) body.target_price = Number(changes.targetPrice)
  if (changes.condition !== undefined) body.condition = String(changes.condition).toUpperCase()
  if (changes.status !== undefined) body.is_active = changes.status === 'active'
  return body
}

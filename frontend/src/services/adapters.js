/**
 * Tradutores entre as rotas de alertas da API (FastAPI do Integrante 1) e o
 * formato usado pelas telas.
 *
 * O back-end usa snake_case, condição em MAIÚSCULAS e dois booleanos
 * (is_active / is_triggered). As telas usam camelCase, condição em minúsculas
 * e um único campo "status". Toda a conversão fica concentrada aqui, para que
 * os componentes não precisem saber como o back-end escreve os campos.
 *
 * (As cotações de /api/quotes já chegam no formato das telas e não passam por aqui.)
 */

// O back-end grava as datas em UTC, mas o SQLite devolve sem o "Z" no final.
// Sem o "Z" o navegador trataria o horário como local (3 horas de erro no Brasil).
export function toIsoUtc(value) {
  if (!value || typeof value !== 'string') return value ?? null
  const hasTimezone = /(Z|[+-]\d{2}:?\d{2})$/.test(value)
  return hasTimezone ? value : `${value}Z`
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

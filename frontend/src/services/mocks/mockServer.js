/**
 * "Back-end falso" que roda no navegador.
 * Devolve exatamente o mesmo formato combinado no API_CONTRACT.md,
 * para que trocar para a API real seja só mudar VITE_USE_MOCK=false.
 *
 * Usuários e alertas ficam salvos no localStorage do navegador.
 */

const USERS_KEY = 'quotly_mock_users'
const ALERTS_KEY = 'quotly_mock_alerts'

const STOCKS = {
  PETR4: { name: 'Petrobras PN', base: 38.4, currency: 'BRL' },
  VALE3: { name: 'Vale ON', base: 61.2, currency: 'BRL' },
  ITUB4: { name: 'Itaú Unibanco PN', base: 35.9, currency: 'BRL' },
  BBDC4: { name: 'Bradesco PN', base: 14.7, currency: 'BRL' },
  BBAS3: { name: 'Banco do Brasil ON', base: 27.3, currency: 'BRL' },
  WEGE3: { name: 'WEG ON', base: 44.8, currency: 'BRL' },
  MGLU3: { name: 'Magazine Luiza ON', base: 9.6, currency: 'BRL' },
  ABEV3: { name: 'Ambev ON', base: 13.1, currency: 'BRL' },
  AAPL: { name: 'Apple Inc.', base: 228.5, currency: 'USD' },
  MSFT: { name: 'Microsoft Corp.', base: 432.1, currency: 'USD' },
  TSLA: { name: 'Tesla Inc.', base: 251.9, currency: 'USD' },
  NVDA: { name: 'NVIDIA Corp.', base: 138.7, currency: 'USD' },
}

// ---------- utilidades ----------

const wait = (ms = 350) => new Promise((r) => setTimeout(r, ms + Math.random() * 300))

// Erro no mesmo formato que o axios produz, para o front tratar igual
function httpError(status, detail) {
  const err = new Error(detail)
  err.response = { status, data: { detail } }
  return err
}

function load(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function save(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* ignora */
  }
}

// Gerador pseudoaleatório com semente: o mesmo ticker sempre gera o mesmo gráfico
function seededRandom(seedText) {
  let h = 1779033703 ^ seedText.length
  for (let i = 0; i < seedText.length; i++) {
    h = Math.imul(h ^ seedText.charCodeAt(i), 3432918353)
    h = (h << 13) | (h >>> 19)
  }
  return () => {
    h = Math.imul(h ^ (h >>> 16), 2246822507)
    h = Math.imul(h ^ (h >>> 13), 3266489909)
    h ^= h >>> 16
    return (h >>> 0) / 4294967296
  }
}

function toISODate(d) {
  return d.toISOString().slice(0, 10)
}

// Série de 1 ano de pregões (sem fins de semana) terminando hoje
function buildSeries(ticker) {
  const stock = STOCKS[ticker]
  const today = toISODate(new Date())
  const rand = seededRandom(ticker + today)
  const days = []
  const cursor = new Date()
  cursor.setDate(cursor.getDate() - 365)
  let price = stock.base * (0.8 + rand() * 0.3)

  while (toISODate(cursor) <= today) {
    const weekday = cursor.getDay()
    if (weekday !== 0 && weekday !== 6) {
      // pequena tendência em direção ao preço base + ruído
      const drift = (stock.base - price) * 0.01
      price = Math.max(0.5, price + drift + (rand() - 0.5) * price * 0.035)
      days.push({ date: toISODate(cursor), close: Number(price.toFixed(2)), _r: rand() })
    }
    cursor.setDate(cursor.getDate() + 1)
  }
  return days
}

const seriesCache = new Map()
function getSeries(ticker) {
  if (!seriesCache.has(ticker)) seriesCache.set(ticker, buildSeries(ticker))
  return seriesCache.get(ticker)
}

function normalizeTicker(ticker) {
  return String(ticker || '').trim().toUpperCase()
}

function currentUserFromToken(token) {
  if (!token || !token.startsWith('mock-token-')) throw httpError(401, 'Não autenticado.')
  const id = Number(token.replace('mock-token-', ''))
  const user = load(USERS_KEY, []).find((u) => u.id === id)
  if (!user) throw httpError(401, 'Sessão inválida.')
  return user
}

function publicUser(u) {
  return { id: u.id, name: u.name, email: u.email }
}

// ---------- autenticação ----------

export async function register({ name, email, password }) {
  await wait()
  const users = load(USERS_KEY, [])
  const normalized = email.trim().toLowerCase()
  if (users.some((u) => u.email === normalized)) {
    throw httpError(400, 'Este e-mail já está cadastrado.')
  }
  // ATENÇÃO: senha em texto puro só porque é um mock local. O back-end real usa hash.
  const user = { id: Date.now(), name: name.trim(), email: normalized, password }
  save(USERS_KEY, [...users, user])
  return publicUser(user)
}

export async function login({ email, password }) {
  await wait()
  const user = load(USERS_KEY, []).find(
    (u) => u.email === email.trim().toLowerCase() && u.password === password,
  )
  if (!user) throw httpError(401, 'E-mail ou senha incorretos.')
  return { access_token: `mock-token-${user.id}`, token_type: 'bearer' }
}

export async function me(token) {
  await wait(150)
  return publicUser(currentUserFromToken(token))
}

// ---------- cotações ----------

export async function getQuote(rawTicker) {
  await wait()
  const ticker = normalizeTicker(rawTicker)
  const stock = STOCKS[ticker]
  if (!stock) throw httpError(404, `Ativo "${ticker}" não encontrado.`)

  const series = getSeries(ticker)
  const last = series[series.length - 1]
  const prev = series[series.length - 2]
  const change = last.close - prev.close

  return {
    ticker,
    name: stock.name,
    currency: stock.currency,
    price: last.close,
    change: Number(change.toFixed(2)),
    changePercent: Number(((change / prev.close) * 100).toFixed(2)),
    previousClose: prev.close,
    high: Number((Math.max(last.close, prev.close) * (1 + last._r * 0.012)).toFixed(2)),
    low: Number((Math.min(last.close, prev.close) * (1 - last._r * 0.012)).toFixed(2)),
    volume: Math.round(2_000_000 + last._r * 40_000_000),
    updatedAt: new Date().toISOString(),
  }
}

const RANGE_DAYS = { '7d': 7, '1mo': 22, '6mo': 126, '1y': 252 }

export async function getHistory(rawTicker, range = '1mo') {
  await wait()
  const ticker = normalizeTicker(rawTicker)
  if (!STOCKS[ticker]) throw httpError(404, `Ativo "${ticker}" não encontrado.`)
  const n = RANGE_DAYS[range] ?? 22
  return getSeries(ticker)
    .slice(-n)
    .map(({ date, close }) => ({ date, close }))
}

export function listKnownTickers() {
  return Object.keys(STOCKS)
}

// ---------- alertas ----------

function userAlerts(userId) {
  return load(ALERTS_KEY, []).filter((a) => a.userId === userId)
}

function publicAlert({ userId: _userId, ...rest }) {
  return rest
}

export async function listAlerts(token) {
  await wait()
  const user = currentUserFromToken(token)
  const all = load(ALERTS_KEY, [])

  // Simula o worker do Integrante 2: dispara alertas cuja meta já foi atingida
  let changed = false
  for (const a of all) {
    if (a.userId !== user.id || a.status !== 'active' || !STOCKS[a.ticker]) continue
    const series = getSeries(a.ticker)
    const price = series[series.length - 1].close
    const hit = a.condition === 'above' ? price >= a.targetPrice : price <= a.targetPrice
    if (hit) {
      a.status = 'triggered'
      a.triggeredAt = new Date().toISOString()
      changed = true
    }
  }
  if (changed) save(ALERTS_KEY, all)

  return userAlerts(user.id)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
    .map(publicAlert)
}

export async function createAlert(token, { ticker, targetPrice, condition }) {
  await wait()
  const user = currentUserFromToken(token)
  const t = normalizeTicker(ticker)
  if (!STOCKS[t]) throw httpError(404, `Ativo "${t}" não encontrado.`)
  const alert = {
    id: Date.now(),
    userId: user.id,
    ticker: t,
    targetPrice: Number(targetPrice),
    condition,
    status: 'active',
    createdAt: new Date().toISOString(),
    triggeredAt: null,
  }
  save(ALERTS_KEY, [...load(ALERTS_KEY, []), alert])
  return publicAlert(alert)
}

export async function updateAlert(token, id, changes) {
  await wait()
  const user = currentUserFromToken(token)
  const all = load(ALERTS_KEY, [])
  const alert = all.find((a) => a.id === id && a.userId === user.id)
  if (!alert) throw httpError(404, 'Alerta não encontrado.')
  if (changes.ticker !== undefined) alert.ticker = normalizeTicker(changes.ticker)
  if (changes.targetPrice !== undefined) alert.targetPrice = Number(changes.targetPrice)
  if (changes.condition !== undefined) alert.condition = changes.condition
  if (changes.status !== undefined) {
    alert.status = changes.status
    if (changes.status === 'active') alert.triggeredAt = null
  }
  save(ALERTS_KEY, all)
  return publicAlert(alert)
}

export async function deleteAlert(token, id) {
  await wait()
  const user = currentUserFromToken(token)
  const all = load(ALERTS_KEY, [])
  const next = all.filter((a) => !(a.id === id && a.userId === user.id))
  if (next.length === all.length) throw httpError(404, 'Alerta não encontrado.')
  save(ALERTS_KEY, next)
}

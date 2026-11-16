import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import Button from '../components/Button.jsx'
import FormField from '../components/FormField.jsx'
import { analyzeVariation, simulateInvestment } from '../services/analytics.js'
import { getErrorMessage } from '../services/api.js'
import { getQuote } from '../services/quotes.js'
import { formatMoney, formatPercent } from '../utils/format.js'

const TICKER_REGEX = /^[A-Z0-9.]{2,10}$/

const toNumber = (v) => Number(String(v).replace(',', '.'))
const isBlank = (v) => v === '' || v == null

// Sem resposta do servidor = API Java desligada (ela é separada da API Python)
function analyticsError(err, fallback) {
  if (!err?.response) return 'Não foi possível conectar à API de análises (Java, porta 8085).'
  return getErrorMessage(err, fallback)
}

function Stat({ label, value, highlight = false }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className={`mt-0.5 font-mono font-semibold ${highlight ? 'text-xl' : 'text-sm'}`}>
        {value}
      </dd>
    </div>
  )
}

// ---------- Simulação de investimento (GET /api/analytics/simulate) ----------

function validateSimulation(v) {
  const errors = {}
  if (!v.ticker) errors.ticker = 'Informe o código da ação.'
  else if (!TICKER_REGEX.test(v.ticker)) errors.ticker = 'Código inválido (ex: PETR4, AAPL).'

  for (const field of ['initialAmount', 'monthlyContribution']) {
    const n = toNumber(v[field])
    if (isBlank(v[field]) || Number.isNaN(n)) errors[field] = 'Informe um valor.'
    else if (n < 0) errors[field] = 'O valor não pode ser negativo.'
  }

  const months = toNumber(v.months)
  if (isBlank(v.months) || !Number.isInteger(months)) errors.months = 'Informe um número inteiro.'
  else if (months < 1 || months > 600) errors.months = 'O prazo deve ficar entre 1 e 600 meses.'

  const rate = toNumber(v.annualRatePercent)
  if (isBlank(v.annualRatePercent) || Number.isNaN(rate)) errors.annualRatePercent = 'Informe a taxa.'
  else if (rate < -100) errors.annualRatePercent = 'A taxa não pode ser menor que -100%.'

  return errors
}

function SimulationCard({ initialTicker }) {
  const [values, setValues] = useState({
    ticker: initialTicker || 'PETR4',
    initialAmount: '1000',
    monthlyContribution: '200',
    months: '12',
    annualRatePercent: '12',
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  function update(field, value) {
    setValues((v) => ({ ...v, [field]: value }))
    setErrors((e) => ({ ...e, [field]: undefined }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const found = validateSimulation(values)
    setErrors(found)
    if (Object.keys(found).length) return

    setLoading(true)
    try {
      const data = await simulateInvestment({
        ticker: values.ticker,
        initialAmount: toNumber(values.initialAmount),
        monthlyContribution: toNumber(values.monthlyContribution),
        months: toNumber(values.months),
        annualRatePercent: toNumber(values.annualRatePercent),
      })
      setResult(data)
    } catch (err) {
      toast.error(analyticsError(err, 'Não foi possível simular.'))
    } finally {
      setLoading(false)
    }
  }

  // parte do saldo final que veio do próprio bolso (o resto são juros)
  const investedShare =
    result && result.finalBalance > 0 && result.totalInterest >= 0
      ? Math.min(100, (result.totalInvested / result.finalBalance) * 100)
      : null

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <h2 className="text-lg font-semibold">Simulação de investimento</h2>
      <p className="mt-1 text-sm text-slate-500">
        Quanto você teria aplicando todo mês, com juros compostos.
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-4 space-y-4">
        <FormField
          id="sim-ticker"
          label="Ação"
          placeholder="PETR4"
          value={values.ticker}
          onChange={(e) => update('ticker', e.target.value.toUpperCase().trim())}
          error={errors.ticker}
          autoComplete="off"
        />
        <div className="grid grid-cols-2 gap-4">
          <FormField
            id="sim-initial"
            label="Aporte inicial (R$)"
            type="number"
            step="0.01"
            min="0"
            inputMode="decimal"
            value={values.initialAmount}
            onChange={(e) => update('initialAmount', e.target.value)}
            error={errors.initialAmount}
          />
          <FormField
            id="sim-monthly"
            label="Aporte mensal (R$)"
            type="number"
            step="0.01"
            min="0"
            inputMode="decimal"
            value={values.monthlyContribution}
            onChange={(e) => update('monthlyContribution', e.target.value)}
            error={errors.monthlyContribution}
          />
          <FormField
            id="sim-months"
            label="Prazo (meses)"
            type="number"
            step="1"
            min="1"
            max="600"
            inputMode="numeric"
            value={values.months}
            onChange={(e) => update('months', e.target.value)}
            error={errors.months}
          />
          <FormField
            id="sim-rate"
            label="Taxa anual (%)"
            type="number"
            step="0.01"
            inputMode="decimal"
            value={values.annualRatePercent}
            onChange={(e) => update('annualRatePercent', e.target.value)}
            error={errors.annualRatePercent}
          />
        </div>
        <Button type="submit" loading={loading} className="w-full">
          Simular
        </Button>
      </form>

      {result && (
        <div className="mt-6 border-t border-slate-100 pt-4" aria-live="polite">
          <p className="text-sm text-slate-500">
            {result.ticker} · {result.months} {result.months === 1 ? 'mês' : 'meses'} a{' '}
            {formatPercent(result.annualRatePercent).replace('+', '')} ao ano
          </p>
          <dl className="mt-3 grid grid-cols-2 gap-4">
            <Stat label="Saldo final" value={formatMoney(result.finalBalance)} highlight />
            <Stat label="Juros" value={formatMoney(result.totalInterest)} highlight />
            <Stat label="Total investido" value={formatMoney(result.totalInvested)} />
          </dl>
          {investedShare != null && (
            <div className="mt-4">
              <div className="flex h-2 overflow-hidden rounded-full bg-up/70">
                <div className="bg-slate-400" style={{ width: `${investedShare}%` }} />
              </div>
              <div className="mt-1 flex justify-between text-xs text-slate-500">
                <span>Investido</span>
                <span>Juros</span>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  )
}

// ---------- Análise de variação (GET /api/analytics/variation) ----------

const TRENDS = {
  UP: { label: 'Em alta', icon: '▲', className: 'bg-up/10 text-up' },
  DOWN: { label: 'Em baixa', icon: '▼', className: 'bg-down/10 text-down' },
  NEUTRAL: { label: 'Estável', icon: '●', className: 'bg-slate-100 text-slate-600' },
}

function validateVariation(v) {
  const errors = {}
  if (!v.ticker) errors.ticker = 'Informe o código da ação.'
  else if (!TICKER_REGEX.test(v.ticker)) errors.ticker = 'Código inválido (ex: PETR4, AAPL).'

  for (const field of ['currentPrice', 'previousClose']) {
    const n = toNumber(v[field])
    if (isBlank(v[field]) || Number.isNaN(n)) errors[field] = 'Informe o preço.'
    else if (n <= 0) errors[field] = 'O preço deve ser maior que zero.'
  }

  if (!isBlank(v.targetPrice)) {
    const target = toNumber(v.targetPrice)
    if (Number.isNaN(target) || target <= 0) errors.targetPrice = 'O preço deve ser maior que zero.'
  }
  return errors
}

function targetSentence(distance) {
  const pct = formatPercent(Math.abs(distance)).replace('+', '')
  if (distance > 0) return `O preço precisa subir ${pct} para chegar ao alvo.`
  if (distance < 0) return `O preço precisa cair ${pct} para chegar ao alvo.`
  return 'O preço está exatamente no alvo.'
}

function VariationCard({ initialTicker }) {
  const [values, setValues] = useState({
    ticker: initialTicker || '',
    currentPrice: '',
    previousClose: '',
    targetPrice: '',
  })
  const [currency, setCurrency] = useState('BRL')
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [quoteLoading, setQuoteLoading] = useState(false)
  const [result, setResult] = useState(null)

  function update(field, value) {
    setValues((v) => ({ ...v, [field]: value }))
    setErrors((e) => ({ ...e, [field]: undefined }))
  }

  // Preenche preço atual e fechamento anterior com a cotação da API Python
  async function fillFromQuote(ticker) {
    if (!ticker) {
      setErrors((e) => ({ ...e, ticker: 'Informe o código da ação.' }))
      return
    }
    setQuoteLoading(true)
    try {
      const q = await getQuote(ticker)
      setCurrency(q.currency || 'BRL')
      setValues((v) => ({
        ...v,
        ticker: q.ticker,
        currentPrice: String(q.price),
        previousClose: q.previousClose != null ? String(q.previousClose) : v.previousClose,
      }))
      setErrors({})
    } catch (err) {
      toast.error(
        err?.response?.status === 404
          ? `Não encontramos o ativo "${ticker}".`
          : getErrorMessage(err, 'Erro ao buscar a cotação.'),
      )
    } finally {
      setQuoteLoading(false)
    }
  }

  // Veio de "Analisar" na tela de cotações (?ticker=PETR4): já busca os preços
  useEffect(() => {
    if (initialTicker) fillFromQuote(initialTicker)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialTicker])

  async function handleSubmit(e) {
    e.preventDefault()
    const found = validateVariation(values)
    setErrors(found)
    if (Object.keys(found).length) return

    setLoading(true)
    try {
      const data = await analyzeVariation({
        ticker: values.ticker,
        currentPrice: toNumber(values.currentPrice),
        previousClose: toNumber(values.previousClose),
        targetPrice: isBlank(values.targetPrice) ? null : toNumber(values.targetPrice),
      })
      setResult(data)
    } catch (err) {
      toast.error(analyticsError(err, 'Não foi possível analisar.'))
    } finally {
      setLoading(false)
    }
  }

  const trend = result ? (TRENDS[result.trend] ?? TRENDS.NEUTRAL) : null

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <h2 className="text-lg font-semibold">Análise de variação</h2>
      <p className="mt-1 text-sm text-slate-500">
        Compara o preço atual com o fechamento anterior e com um preço-alvo.
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-4 space-y-4">
        <div className="flex items-start gap-2">
          <FormField
            id="var-ticker"
            label="Ação"
            placeholder="PETR4"
            className="flex-1"
            value={values.ticker}
            onChange={(e) => update('ticker', e.target.value.toUpperCase().trim())}
            error={errors.ticker}
            autoComplete="off"
          />
          <Button
            type="button"
            variant="secondary"
            className="mt-6"
            loading={quoteLoading}
            onClick={() => fillFromQuote(values.ticker)}
          >
            Usar cotação atual
          </Button>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <FormField
            id="var-current"
            label="Preço atual"
            type="number"
            step="0.01"
            min="0"
            inputMode="decimal"
            placeholder="0,00"
            value={values.currentPrice}
            onChange={(e) => update('currentPrice', e.target.value)}
            error={errors.currentPrice}
          />
          <FormField
            id="var-previous"
            label="Fechamento anterior"
            type="number"
            step="0.01"
            min="0"
            inputMode="decimal"
            placeholder="0,00"
            value={values.previousClose}
            onChange={(e) => update('previousClose', e.target.value)}
            error={errors.previousClose}
          />
        </div>
        <FormField
          id="var-target"
          label="Preço-alvo (opcional)"
          type="number"
          step="0.01"
          min="0"
          inputMode="decimal"
          placeholder="0,00"
          value={values.targetPrice}
          onChange={(e) => update('targetPrice', e.target.value)}
          error={errors.targetPrice}
        />
        <Button type="submit" loading={loading} className="w-full">
          Analisar
        </Button>
      </form>

      {result && (
        <div className="mt-6 border-t border-slate-100 pt-4" aria-live="polite">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-lg font-bold">{result.ticker}</span>
            <span
              className={`rounded-md px-2 py-1 text-sm font-semibold ${trend.className}`}
            >
              {trend.icon} {trend.label}
            </span>
          </div>
          <dl className="mt-3 grid grid-cols-2 gap-4">
            <Stat
              label="Variação"
              value={formatMoney(result.absoluteChange, currency)}
              highlight
            />
            <Stat label="Variação (%)" value={formatPercent(result.percentageChange)} highlight />
            <Stat label="Preço atual" value={formatMoney(result.currentPrice, currency)} />
            <Stat label="Fech. anterior" value={formatMoney(result.previousClose, currency)} />
          </dl>
          {result.distanceToTargetPercent != null && (
            <p className="mt-4 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
              {targetSentence(result.distanceToTargetPercent)}
            </p>
          )}
        </div>
      )}
    </section>
  )
}

export default function Analytics() {
  // ?ticker=PETR4 vem do botão "Analisar" da tela de cotações
  const [searchParams] = useSearchParams()
  const ticker = (searchParams.get('ticker') ?? '').trim().toUpperCase()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Análises</h1>
        <p className="text-sm text-slate-500">
          Cálculos feitos pela API de análises do Quotly (Java / Spring Boot).
        </p>
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-2">
        <VariationCard key={`var-${ticker}`} initialTicker={ticker} />
        <SimulationCard key={`sim-${ticker}`} initialTicker={ticker} />
      </div>
    </div>
  )
}

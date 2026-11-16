import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Skeleton } from '../components/Spinner.jsx'
import TickerSearch from '../components/TickerSearch.jsx'
import { MAX_SAVED, useSavedTickers } from '../hooks/useSavedTickers.js'
import { getErrorMessage } from '../services/api.js'
import { getQuote } from '../services/quotes.js'
import { formatMoney, formatPercent } from '../utils/format.js'

const TICKER_REGEX = /^[A-Z0-9.]{1,10}$/
const REFRESH_MS = 60_000

function SavedCard({ ticker, quote, onRemove }) {
  // quote: undefined = carregando | null = não foi possível buscar | objeto = cotação
  const up = quote?.change == null || quote.change >= 0

  return (
    <li className="relative rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:border-brand/50">
      <Link to={`/dashboard?ticker=${encodeURIComponent(ticker)}`} className="block p-4 pr-12">
        <p className="font-mono text-lg font-bold">{ticker}</p>

        {quote === undefined && (
          <>
            <Skeleton className="mt-1 h-4 w-32" />
            <Skeleton className="mt-3 h-7 w-24" />
          </>
        )}

        {quote === null && <p className="mt-1 text-sm text-slate-500">Cotação indisponível</p>}

        {quote && (
          <>
            <p className="truncate text-sm text-slate-500">{quote.name || '\u00a0'}</p>
            <div className="mt-2 flex flex-wrap items-baseline gap-2">
              <span className="font-mono text-xl font-semibold">
                {formatMoney(quote.price, quote.currency)}
              </span>
              {quote.changePercent != null && (
                <span
                  className={`rounded-md px-1.5 py-0.5 font-mono text-xs font-semibold ${
                    up ? 'bg-up/10 text-up' : 'bg-down/10 text-down'
                  }`}
                >
                  {up ? '▲' : '▼'} {formatPercent(quote.changePercent)}
                </span>
              )}
            </div>
          </>
        )}
      </Link>

      <button
        onClick={() => onRemove(ticker)}
        aria-label={`Remover ${ticker} dos salvos`}
        title="Remover dos salvos"
        className="absolute right-2 top-2 rounded-lg px-2 py-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
      >
        ✕
      </button>
    </li>
  )
}

export default function Saved() {
  const { saved, add, remove } = useSavedTickers()
  const [input, setInput] = useState('')
  const [adding, setAdding] = useState(false)
  const [quotes, setQuotes] = useState({}) // { PETR4: cotação | null }

  // Busca o preço de todos os salvos ao abrir e de novo a cada minuto
  const savedKey = saved.join(',')
  useEffect(() => {
    const tickers = savedKey ? savedKey.split(',') : []
    if (!tickers.length) return
    let cancelled = false

    async function load() {
      const results = await Promise.allSettled(tickers.map((t) => getQuote(t)))
      if (cancelled) return
      const map = {}
      results.forEach((r, i) => {
        map[tickers[i]] = r.status === 'fulfilled' ? r.value : null
      })
      setQuotes(map)
    }

    load()
    const timer = setInterval(() => {
      if (!document.hidden) load()
    }, REFRESH_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [savedKey])

  // Antes de salvar, confere na API se o ativo existe
  async function handleAdd(value) {
    const ticker = value.trim().toUpperCase()
    if (!ticker) return
    if (!TICKER_REGEX.test(ticker)) {
      toast.error('Código inválido (ex: PETR4, AAPL).')
      return
    }
    if (saved.includes(ticker)) {
      toast(`${ticker} já está nos seus salvos.`)
      setInput('')
      return
    }
    if (saved.length >= MAX_SAVED) {
      toast.error(`Você pode salvar no máximo ${MAX_SAVED} tickers.`)
      return
    }

    setAdding(true)
    try {
      const quote = await getQuote(ticker)
      setQuotes((q) => ({ ...q, [ticker]: quote }))
      add(ticker)
      setInput('')
      toast.success(`${ticker} salvo.`)
    } catch (err) {
      toast.error(
        err?.response?.status === 404
          ? `Não encontramos o ativo "${ticker}".`
          : getErrorMessage(err, 'Não foi possível salvar o ticker.'),
      )
    } finally {
      setAdding(false)
    }
  }

  function handleRemove(ticker) {
    remove(ticker)
    toast.success(`${ticker} removido dos salvos.`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Tickers salvos</h1>
        <p className="text-sm text-slate-500">
          Suas ações de acesso rápido. Clique em uma para ver a cotação completa.
        </p>
      </div>

      <TickerSearch
        value={input}
        onChange={setInput}
        onSearch={handleAdd}
        submitLabel="Salvar"
        loading={adding}
      />

      {saved.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
          <p className="text-slate-600">Você ainda não salvou nenhum ticker.</p>
          <p className="mt-1 text-sm text-slate-500">
            Adicione um no campo acima ou use o botão "☆ Salvar" na tela de{' '}
            <Link to="/dashboard" className="text-brand hover:underline">
              cotações
            </Link>
            .
          </p>
        </div>
      ) : (
        <>
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {saved.map((ticker) => (
              <SavedCard
                key={ticker}
                ticker={ticker}
                quote={quotes[ticker]}
                onRemove={handleRemove}
              />
            ))}
          </ul>
          <p className="text-xs text-slate-400">
            {saved.length} de {MAX_SAVED} salvos · preços atualizam sozinhos a cada minuto · a
            lista fica guardada neste navegador
          </p>
        </>
      )}
    </div>
  )
}

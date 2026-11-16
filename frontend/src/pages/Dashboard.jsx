import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import AlertForm from '../components/AlertForm.jsx'
import Button from '../components/Button.jsx'
import Modal from '../components/Modal.jsx'
import PriceChart from '../components/PriceChart.jsx'
import QuoteCard, { QuoteCardSkeleton } from '../components/QuoteCard.jsx'
import TickerSearch from '../components/TickerSearch.jsx'
import { createAlert } from '../services/alerts.js'
import { getErrorMessage } from '../services/api.js'
import { getHistory, getQuote, POPULAR_TICKERS } from '../services/quotes.js'
import { formatMoney } from '../utils/format.js'

// De quanto em quanto tempo a cotação é buscada de novo sozinha.
// A API guarda cada cotação por 60 s, então atualizar mais rápido não traria preço novo.
const REFRESH_MS = 60_000

export default function Dashboard() {
  // O ticker fica na URL (?ticker=PETR4), assim dá para recarregar/compartilhar
  const [searchParams, setSearchParams] = useSearchParams()
  const ticker = searchParams.get('ticker') ?? ''

  const [input, setInput] = useState(ticker)
  const [quote, setQuote] = useState(null)
  const [quoteLoading, setQuoteLoading] = useState(false)
  const [error, setError] = useState(null)

  const [range, setRange] = useState('1mo')
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)

  const [alertOpen, setAlertOpen] = useState(false)

  // Busca a cotação sempre que o ticker da URL mudar
  useEffect(() => {
    if (!ticker) return
    let cancelled = false
    setQuoteLoading(true)
    setError(null)
    setQuote(null)
    getQuote(ticker)
      .then((q) => !cancelled && setQuote(q))
      .catch((err) => {
        if (cancelled) return
        setError(
          err?.response?.status === 404
            ? `Não encontramos o ativo "${ticker}". Confira o código e tente de novo.`
            : getErrorMessage(err, 'Erro ao buscar a cotação.'),
        )
      })
      .finally(() => !cancelled && setQuoteLoading(false))
    return () => {
      cancelled = true
    }
  }, [ticker])

  // Atualização automática: busca a cotação de novo a cada minuto, sem piscar a tela.
  // Não roda com a aba em segundo plano e, se der erro, mantém o último preço.
  useEffect(() => {
    if (!ticker) return
    let cancelled = false
    const timer = setInterval(() => {
      if (document.hidden) return
      getQuote(ticker)
        .then((q) => {
          // só troca se já havia uma cotação na tela (não mexe em telas de erro/carregando)
          if (!cancelled) setQuote((current) => (current ? q : current))
        })
        .catch(() => {})
    }, REFRESH_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [ticker])

  // Busca o histórico quando o ticker ou o período mudarem
  useEffect(() => {
    if (!ticker) return
    let cancelled = false
    setHistoryLoading(true)
    getHistory(ticker, range)
      .then((h) => !cancelled && setHistory(h))
      .catch(() => !cancelled && setHistory([]))
      .finally(() => !cancelled && setHistoryLoading(false))
    return () => {
      cancelled = true
    }
  }, [ticker, range])

  function search(value) {
    const t = value.trim().toUpperCase()
    if (!t) return
    setInput(t)
    setSearchParams({ ticker: t })
  }

  async function handleCreateAlert(payload) {
    try {
      await createAlert(payload)
      toast.success(
        <span>
          Alerta criado! <Link to="/alerts" className="font-medium underline">Ver alertas</Link>
        </span>,
      )
      setAlertOpen(false)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível criar o alerta.'))
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Consultar cotação</h1>
        <p className="text-sm text-slate-500">
          Digite o código ou o nome de uma ação da B3 ou dos EUA.
        </p>
      </div>

      <TickerSearch value={input} onChange={setInput} onSearch={search} />

      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="text-slate-500">Populares:</span>
        {POPULAR_TICKERS.map((t) => (
          <button
            key={t}
            onClick={() => search(t)}
            className="rounded-full border border-slate-300 bg-white px-3 py-1 font-mono text-xs hover:border-brand hover:text-brand"
          >
            {t}
          </button>
        ))}
      </div>

      {!ticker && (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-500">
          Busque uma ação para ver a cotação e o gráfico.
        </div>
      )}

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center text-red-700">
          {error}
        </div>
      )}

      {quoteLoading && <QuoteCardSkeleton />}

      {quote && (
        <>
          <QuoteCard
            quote={quote}
            autoRefresh
            action={
              <div className="flex flex-wrap gap-2">
                <Link
                  to={`/analytics?ticker=${encodeURIComponent(quote.ticker)}`}
                  className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
                >
                  📊 Analisar
                </Link>
                <Button onClick={() => setAlertOpen(true)}>🔔 Criar alerta</Button>
              </div>
            }
          />
          <PriceChart
            data={history}
            range={range}
            onRangeChange={setRange}
            loading={historyLoading}
            currency={quote.currency}
          />
        </>
      )}

      <Modal open={alertOpen} title="Novo alerta de preço" onClose={() => setAlertOpen(false)}>
        {quote && (
          <AlertForm
            initial={{
              ticker: quote.ticker,
              targetPrice: quote.price,
              condition: 'above',
            }}
            currentPrice={formatMoney(quote.price, quote.currency)}
            onSubmit={handleCreateAlert}
            onCancel={() => setAlertOpen(false)}
          />
        )}
      </Modal>
    </div>
  )
}

import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import AlertForm from '../components/AlertForm.jsx'
import Button from '../components/Button.jsx'
import Modal from '../components/Modal.jsx'
import { Skeleton } from '../components/Spinner.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import {
  CONDITION_LABELS,
  createAlert,
  deleteAlert,
  listAlerts,
  updateAlert,
} from '../services/alerts.js'
import { getErrorMessage } from '../services/api.js'
import { getQuote } from '../services/quotes.js'
import { formatDateTime, formatMoney } from '../utils/format.js'

const FILTERS = [
  { value: 'all', label: 'Todos' },
  { value: 'active', label: 'Ativos' },
  { value: 'triggered', label: 'Disparados' },
  { value: 'disabled', label: 'Desativados' },
]

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [quotes, setQuotes] = useState({}) // { PETR4: quote, ... }
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  // modal: null | { mode: 'create' } | { mode: 'edit', alert }
  const [modal, setModal] = useState(null)
  const [confirmDeleteId, setConfirmDeleteId] = useState(null)
  const [busyId, setBusyId] = useState(null)

  const load = useCallback(async () => {
    try {
      const data = await listAlerts()
      setAlerts(data)
      // busca o preço atual de cada ticker (sem repetir)
      const tickers = [...new Set(data.map((a) => a.ticker))]
      const results = await Promise.allSettled(tickers.map((t) => getQuote(t)))
      const map = {}
      results.forEach((r, i) => {
        if (r.status === 'fulfilled') map[tickers[i]] = r.value
      })
      setQuotes(map)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Erro ao carregar alertas.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function handleSubmit(payload) {
    try {
      if (modal?.mode === 'edit') {
        // editar reativa o alerta, para que ele volte a ser verificado
        await updateAlert(modal.alert.id, { ...payload, status: 'active' })
        toast.success('Alerta atualizado.')
      } else {
        await createAlert(payload)
        toast.success('Alerta criado.')
      }
      setModal(null)
      load()
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível salvar o alerta.'))
    }
  }

  async function handleToggle(alert) {
    const next = alert.status === 'active' ? 'disabled' : 'active'
    setBusyId(alert.id)
    try {
      await updateAlert(alert.id, { status: next })
      toast.success(next === 'active' ? 'Alerta reativado.' : 'Alerta desativado.')
      load()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusyId(null)
    }
  }

  async function handleDelete(id) {
    setBusyId(id)
    try {
      await deleteAlert(id)
      setAlerts((list) => list.filter((a) => a.id !== id))
      toast.success('Alerta excluído.')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível excluir.'))
    } finally {
      setBusyId(null)
      setConfirmDeleteId(null)
    }
  }

  const visible = filter === 'all' ? alerts : alerts.filter((a) => a.status === filter)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Meus alertas</h1>
          <p className="text-sm text-slate-500">
            Você recebe um e-mail quando a ação atingir o preço alvo.
          </p>
        </div>
        <Button onClick={() => setModal({ mode: 'create' })}>+ Novo alerta</Button>
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => {
          const count = f.value === 'all' ? alerts.length : alerts.filter((a) => a.status === f.value).length
          return (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`rounded-full px-3 py-1 text-sm transition ${
                filter === f.value
                  ? 'bg-slate-900 text-white'
                  : 'border border-slate-300 bg-white text-slate-600 hover:bg-slate-50'
              }`}
            >
              {f.label} <span className="opacity-60">({count})</span>
            </button>
          )
        })}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : visible.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
          <p className="text-slate-600">
            {alerts.length === 0 ? 'Você ainda não tem alertas.' : 'Nenhum alerta neste filtro.'}
          </p>
          {alerts.length === 0 && (
            <p className="mt-1 text-sm text-slate-500">
              Crie um aqui ou a partir de uma{' '}
              <Link to="/dashboard" className="text-brand hover:underline">
                consulta de ação
              </Link>
              .
            </p>
          )}
        </div>
      ) : (
        <ul className="space-y-3">
          {visible.map((alert) => {
            const q = quotes[alert.ticker]
            const currency = q?.currency ?? 'BRL'
            const busy = busyId === alert.id
            return (
              <li
                key={alert.id}
                className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="flex items-start gap-4">
                  <Link
                    to={`/dashboard?ticker=${alert.ticker}`}
                    className="w-20 shrink-0 font-mono text-lg font-bold hover:text-brand"
                  >
                    {alert.ticker}
                  </Link>
                  <div className="text-sm">
                    <p>
                      {alert.condition === 'above' ? '▲ ' : '▼ '}
                      {CONDITION_LABELS[alert.condition]}{' '}
                      <strong className="font-mono">{formatMoney(alert.targetPrice, currency)}</strong>
                    </p>
                    <p className="text-slate-500">
                      Atual:{' '}
                      <span className="font-mono">{q ? formatMoney(q.price, currency) : '—'}</span>
                      {alert.status === 'triggered' && alert.triggeredAt && (
                        <> · disparado em {formatDateTime(alert.triggeredAt)}</>
                      )}
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 sm:justify-end">
                  <StatusBadge status={alert.status} />
                  {confirmDeleteId === alert.id ? (
                    <>
                      <span className="text-sm text-slate-600">Excluir?</span>
                      <Button variant="danger" loading={busy} onClick={() => handleDelete(alert.id)}>
                        Sim
                      </Button>
                      <Button variant="secondary" onClick={() => setConfirmDeleteId(null)}>
                        Não
                      </Button>
                    </>
                  ) : (
                    <>
                      {alert.status !== 'triggered' && (
                        <Button variant="ghost" disabled={busy} onClick={() => handleToggle(alert)}>
                          {alert.status === 'active' ? 'Pausar' : 'Reativar'}
                        </Button>
                      )}
                      <Button variant="ghost" onClick={() => setModal({ mode: 'edit', alert })}>
                        Editar
                      </Button>
                      <Button
                        variant="ghost"
                        className="text-red-600 hover:bg-red-50"
                        onClick={() => setConfirmDeleteId(alert.id)}
                      >
                        Excluir
                      </Button>
                    </>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}

      <Modal
        open={!!modal}
        title={modal?.mode === 'edit' ? 'Editar alerta' : 'Novo alerta de preço'}
        onClose={() => setModal(null)}
      >
        {modal && (
          <AlertForm
            key={modal.alert?.id ?? 'new'}
            initial={modal.alert ?? {}}
            onSubmit={handleSubmit}
            onCancel={() => setModal(null)}
            submitLabel={modal.mode === 'edit' ? 'Salvar' : 'Criar alerta'}
          />
        )}
      </Modal>
    </div>
  )
}

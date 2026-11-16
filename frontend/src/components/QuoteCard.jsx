import { formatCompact, formatDateTime, formatMoney, formatPercent } from '../utils/format.js'
import { Skeleton } from './Spinner.jsx'

function Stat({ label, value }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-0.5 font-mono text-sm font-semibold">{value}</dd>
    </div>
  )
}

export default function QuoteCard({ quote, action }) {
  const up = quote.change >= 0
  const color = up ? 'text-up bg-up/10' : 'text-down bg-down/10'

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold">{quote.ticker}</h2>
            <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
              {quote.currency}
            </span>
          </div>
          <p className="text-sm text-slate-500">{quote.name}</p>
        </div>
        {action}
      </div>

      <div className="mt-4 flex flex-wrap items-baseline gap-3">
        <span className="font-mono text-4xl font-semibold">
          {formatMoney(quote.price, quote.currency)}
        </span>
        <span className={`rounded-md px-2 py-1 font-mono text-sm font-semibold ${color}`}>
          {up ? '▲' : '▼'} {formatMoney(Math.abs(quote.change), quote.currency)} (
          {formatPercent(quote.changePercent)})
        </span>
      </div>

      <dl className="mt-6 grid grid-cols-2 gap-4 border-t border-slate-100 pt-4 sm:grid-cols-4">
        <Stat label="Fech. anterior" value={formatMoney(quote.previousClose, quote.currency)} />
        <Stat label="Máxima do dia" value={formatMoney(quote.high, quote.currency)} />
        <Stat label="Mínima do dia" value={formatMoney(quote.low, quote.currency)} />
        <Stat label="Volume" value={formatCompact(quote.volume)} />
      </dl>

      <p className="mt-4 text-xs text-slate-400">Atualizado em {formatDateTime(quote.updatedAt)}</p>
    </section>
  )
}

export function QuoteCardSkeleton() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <Skeleton className="h-7 w-28" />
      <Skeleton className="mt-2 h-4 w-40" />
      <Skeleton className="mt-5 h-10 w-56" />
      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-10" />
        ))}
      </div>
    </section>
  )
}

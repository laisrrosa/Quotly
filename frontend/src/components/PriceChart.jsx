import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { RANGES } from '../services/quotes.js'
import { formatDate, formatMoney } from '../utils/format.js'
import { Skeleton } from './Spinner.jsx'

function ChartTooltip({ active, payload, currency }) {
  if (!active || !payload?.length) return null
  const { date, close } = payload[0].payload
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-md">
      <p className="text-xs text-slate-500">
        {formatDate(date, { day: '2-digit', month: 'short', year: 'numeric' })}
      </p>
      <p className="font-mono font-semibold">{formatMoney(close, currency)}</p>
    </div>
  )
}

export default function PriceChart({ data, range, onRangeChange, loading, currency = 'BRL' }) {
  const up = data.length > 1 && data[data.length - 1].close >= data[0].close
  const color = up ? 'var(--color-up)' : 'var(--color-down)'
  const longRange = range === '6mo' || range === '1y'

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h3 className="font-semibold">Histórico de preço</h3>
        <div className="flex rounded-lg bg-slate-100 p-1" role="group" aria-label="Período">
          {RANGES.map((r) => (
            <button
              key={r.value}
              onClick={() => onRangeChange(r.value)}
              aria-pressed={range === r.value}
              className={`rounded-md px-3 py-1 text-xs font-semibold transition ${
                range === r.value ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <Skeleton className="h-72 w-full" />
      ) : (
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.25} />
                  <stop offset="100%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="date"
                tickFormatter={(d) =>
                  formatDate(d, longRange ? { month: 'short', year: '2-digit' } : undefined)
                }
                tick={{ fontSize: 12, fill: '#64748b' }}
                tickLine={false}
                axisLine={false}
                minTickGap={24}
              />
              <YAxis
                domain={['auto', 'auto']}
                tickFormatter={(v) => v.toFixed(2)}
                tick={{ fontSize: 12, fill: '#64748b' }}
                tickLine={false}
                axisLine={false}
                width={56}
              />
              <Tooltip content={<ChartTooltip currency={currency} />} />
              <Area
                type="monotone"
                dataKey="close"
                stroke={color}
                strokeWidth={2}
                fill="url(#priceFill)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  )
}

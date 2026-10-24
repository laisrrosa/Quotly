import { STATUS_LABELS } from '../services/alerts.js'

const STYLES = {
  active: 'bg-emerald-100 text-emerald-800',
  triggered: 'bg-indigo-100 text-indigo-800',
  disabled: 'bg-slate-200 text-slate-600',
}

export default function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
        STYLES[status] ?? STYLES.disabled
      }`}
    >
      {STATUS_LABELS[status] ?? status}
    </span>
  )
}

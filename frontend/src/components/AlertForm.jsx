import { useState } from 'react'
import Button from './Button.jsx'
import FormField from './FormField.jsx'
import { CONDITION_LABELS } from '../services/alerts.js'

const TICKER_REGEX = /^[A-Z0-9.]{2,10}$/

function validate({ ticker, targetPrice, condition }) {
  const errors = {}
  if (!ticker) errors.ticker = 'Informe o código da ação.'
  else if (!TICKER_REGEX.test(ticker)) errors.ticker = 'Código inválido (ex: PETR4, AAPL).'
  const price = Number(String(targetPrice).replace(',', '.'))
  if (targetPrice === '' || targetPrice == null) errors.targetPrice = 'Informe o preço alvo.'
  else if (Number.isNaN(price) || price <= 0) errors.targetPrice = 'O preço deve ser maior que zero.'
  if (!condition) errors.condition = 'Escolha uma condição.'
  return errors
}

/**
 * Formulário usado tanto para criar quanto para editar alertas.
 * - initial: valores iniciais (ticker pré-preenchido ou alerta existente)
 * - currentPrice: opcional, só para mostrar como referência
 */
export default function AlertForm({ initial = {}, currentPrice, onSubmit, onCancel, submitLabel }) {
  const [values, setValues] = useState({
    ticker: initial.ticker ?? '',
    targetPrice: initial.targetPrice ?? '',
    condition: initial.condition ?? 'above',
  })
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)

  function update(field, value) {
    setValues((v) => ({ ...v, [field]: value }))
    setErrors((e) => ({ ...e, [field]: undefined }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const found = validate(values)
    setErrors(found)
    if (Object.keys(found).length) return

    setSubmitting(true)
    try {
      await onSubmit({
        ticker: values.ticker,
        targetPrice: Number(String(values.targetPrice).replace(',', '.')),
        condition: values.condition,
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <FormField
        id="alert-ticker"
        label="Ação"
        placeholder="PETR4"
        value={values.ticker}
        onChange={(e) => update('ticker', e.target.value.toUpperCase().trim())}
        error={errors.ticker}
        autoComplete="off"
      />

      <fieldset>
        <legend className="mb-1 block text-sm font-medium text-slate-700">Avisar quando</legend>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(CONDITION_LABELS).map(([value, label]) => (
            <label
              key={value}
              className={`cursor-pointer rounded-lg border px-3 py-2 text-center text-sm transition ${
                values.condition === value
                  ? 'border-brand bg-brand/5 font-medium text-brand'
                  : 'border-slate-300 text-slate-600 hover:bg-slate-50'
              }`}
            >
              <input
                type="radio"
                name="condition"
                value={value}
                checked={values.condition === value}
                onChange={() => update('condition', value)}
                className="sr-only"
              />
              {value === 'above' ? '▲ ' : '▼ '}
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      <FormField
        id="alert-price"
        label="Preço alvo"
        type="number"
        step="0.01"
        min="0"
        inputMode="decimal"
        placeholder="0,00"
        value={values.targetPrice}
        onChange={(e) => update('targetPrice', e.target.value)}
        error={errors.targetPrice}
      />
      {currentPrice != null && (
        <p className="-mt-2 text-xs text-slate-500">Preço atual: {currentPrice}</p>
      )}

      <div className="flex justify-end gap-2 pt-2">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancelar
          </Button>
        )}
        <Button type="submit" loading={submitting}>
          {submitLabel ?? 'Criar alerta'}
        </Button>
      </div>
    </form>
  )
}

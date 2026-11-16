import { useId, useState } from 'react'
import { suggestTickers } from '../data/tickers.js'
import Button from './Button.jsx'

/**
 * Campo de busca de ação com sugestões (autocomplete).
 * - value / onChange: texto digitado (controlado pela página)
 * - onSearch(ticker): chamado ao enviar o formulário ou escolher uma sugestão
 *
 * Teclado: ↓ e ↑ percorrem as sugestões, Enter escolhe, Esc fecha a lista.
 */
export default function TickerSearch({ value, onChange, onSearch }) {
  const listId = useId()
  const [open, setOpen] = useState(false)
  const [highlight, setHighlight] = useState(-1) // -1 = nenhuma sugestão destacada

  const suggestions = open ? suggestTickers(value) : []
  const showList = suggestions.length > 0

  function choose(ticker) {
    setOpen(false)
    setHighlight(-1)
    onSearch(ticker)
  }

  function handleChange(e) {
    onChange(e.target.value.toUpperCase())
    setOpen(true)
    setHighlight(-1)
  }

  function handleKeyDown(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (!showList) setOpen(true)
      else setHighlight((h) => (h + 1) % suggestions.length)
    } else if (e.key === 'ArrowUp') {
      if (!showList) return
      e.preventDefault()
      setHighlight((h) => (h <= 0 ? suggestions.length - 1 : h - 1))
    } else if (e.key === 'Escape') {
      setOpen(false)
      setHighlight(-1)
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    // Enter com uma sugestão destacada escolhe a sugestão; senão busca o que foi digitado
    if (showList && highlight >= 0) choose(suggestions[highlight].ticker)
    else choose(value)
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <div className="relative w-full">
        <input
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          placeholder="Ex: PETR4, VALE3, AAPL"
          aria-label="Código da ação"
          role="combobox"
          aria-expanded={showList}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={
            showList && highlight >= 0 ? `${listId}-${highlight}` : undefined
          }
          autoComplete="off"
          spellCheck={false}
          className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 font-mono uppercase outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
        />

        {showList && (
          <ul
            id={listId}
            role="listbox"
            aria-label="Sugestões de ações"
            className="absolute left-0 right-0 top-full z-30 mt-1 overflow-hidden rounded-lg border border-slate-200 bg-white py-1 shadow-lg"
          >
            {suggestions.map((s, i) => (
              <li
                key={s.ticker}
                id={`${listId}-${i}`}
                role="option"
                aria-selected={i === highlight}
                // onMouseDown (e não onClick) para rodar antes do onBlur do campo
                onMouseDown={(e) => {
                  e.preventDefault()
                  choose(s.ticker)
                }}
                onMouseEnter={() => setHighlight(i)}
                className={`flex cursor-pointer items-baseline gap-3 px-4 py-2 text-sm ${
                  i === highlight ? 'bg-brand/10' : ''
                }`}
              >
                <span className="w-16 shrink-0 font-mono font-semibold">{s.ticker}</span>
                <span className="truncate text-slate-500">{s.name}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <Button type="submit" className="px-6">
        Buscar
      </Button>
    </form>
  )
}

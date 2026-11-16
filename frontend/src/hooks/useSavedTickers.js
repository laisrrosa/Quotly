import { useCallback, useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'

/**
 * Tickers salvos pelo usuário (lista de acesso rápido).
 *
 * Ficam no localStorage do navegador, numa chave separada para cada usuário.
 * As APIs do projeto não têm rota para isso, então a lista vale só para este
 * navegador: em outro computador o usuário começa com a lista vazia.
 */
export const MAX_SAVED = 20

const keyFor = (userId) => `quotly_saved_tickers_${userId ?? 'anon'}`
const normalize = (ticker) => String(ticker ?? '').trim().toUpperCase()

// localStorage pode lançar erro (aba anônima, bloqueio), por isso o try/catch
function read(key) {
  try {
    const list = JSON.parse(localStorage.getItem(key) ?? '[]')
    return Array.isArray(list) ? list.filter((t) => typeof t === 'string') : []
  } catch {
    return []
  }
}

function write(key, list) {
  try {
    localStorage.setItem(key, JSON.stringify(list))
  } catch {
    /* ignora */
  }
}

export function useSavedTickers() {
  const { user } = useAuth()
  const key = keyFor(user?.id)
  const [saved, setSaved] = useState(() => read(key))

  // Devolve 'added', 'exists' (já estava salvo) ou 'full' (limite atingido)
  const add = useCallback(
    (ticker) => {
      const t = normalize(ticker)
      const current = read(key)
      if (!t || current.includes(t)) return 'exists'
      if (current.length >= MAX_SAVED) return 'full'
      const next = [...current, t]
      write(key, next)
      setSaved(next)
      return 'added'
    },
    [key],
  )

  const remove = useCallback(
    (ticker) => {
      const t = normalize(ticker)
      const next = read(key).filter((item) => item !== t)
      write(key, next)
      setSaved(next)
    },
    [key],
  )

  const isSaved = useCallback((ticker) => saved.includes(normalize(ticker)), [saved])

  return { saved, add, remove, isSaved }
}

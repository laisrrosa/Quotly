import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { USE_MOCK } from '../services/api.js'
import Logo from './Logo.jsx'

const linkClass = ({ isActive }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? 'bg-brand/10 text-brand' : 'text-slate-600 hover:bg-slate-100'
  }`

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen">
      {USE_MOCK && (
        <div className="bg-amber-100 px-4 py-1.5 text-center text-xs text-amber-900">
          Modo demonstração: usando dados simulados (VITE_USE_MOCK=true)
        </div>
      )}

      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-3">
          <div className="flex items-center gap-6">
            <Logo />
            <nav className="flex gap-1">
              <NavLink to="/dashboard" className={linkClass}>
                Cotações
              </NavLink>
              <NavLink to="/alerts" className={linkClass}>
                Meus alertas
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-slate-500 sm:inline">Olá, {user?.name}</span>
            <button
              onClick={handleLogout}
              className="rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-100"
            >
              Sair
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6 sm:py-8">
        <Outlet />
      </main>
    </div>
  )
}

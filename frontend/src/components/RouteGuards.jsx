import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { FullPageSpinner } from './Spinner.jsx'

// Só deixa passar quem está logado. Senão, manda para /login e lembra de onde veio.
export function PrivateRoute() {
  const { isAuthenticated, initializing } = useAuth()
  const location = useLocation()

  if (initializing) return <FullPageSpinner />
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />
  return <Outlet />
}

// Login/cadastro: se já estiver logado, não faz sentido mostrar
export function PublicOnlyRoute() {
  const { isAuthenticated, initializing } = useAuth()

  if (initializing) return <FullPageSpinner />
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <Outlet />
}

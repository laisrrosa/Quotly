import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 px-4 text-center">
      <p className="font-mono text-6xl font-bold text-slate-300">404</p>
      <p className="text-slate-600">Página não encontrada.</p>
      <Link to="/dashboard" className="font-medium text-brand hover:underline">
        Voltar para o início
      </Link>
    </div>
  )
}

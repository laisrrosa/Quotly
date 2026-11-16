import { Link } from 'react-router-dom'

export default function Logo({ size = 'md' }) {
  const text = size === 'lg' ? 'text-3xl' : 'text-xl'
  return (
    <Link to="/" className={`flex items-center gap-2 font-bold tracking-tight ${text}`}>
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-white">
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M3 17l6-6 4 4 8-8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      Quotly
    </Link>
  )
}

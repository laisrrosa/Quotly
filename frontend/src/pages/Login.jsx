import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import AuthLayout from '../components/AuthLayout.jsx'
import Button from '../components/Button.jsx'
import FormField from '../components/FormField.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { getErrorMessage } from '../services/api.js'

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)

  function update(field) {
    return (e) => {
      setForm((f) => ({ ...f, [field]: e.target.value }))
      setErrors((er) => ({ ...er, [field]: undefined }))
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const found = {}
    if (!EMAIL_REGEX.test(form.email)) found.email = 'Informe um e-mail válido.'
    if (!form.password) found.password = 'Informe sua senha.'
    setErrors(found)
    if (Object.keys(found).length) return

    setLoading(true)
    try {
      const user = await login(form.email, form.password)
      toast.success(`Bem-vindo(a), ${user.name}!`)
      // volta para a página que a pessoa tentou acessar antes do login
      navigate(location.state?.from?.pathname ?? '/dashboard', { replace: true })
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível entrar.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      title="Entrar"
      subtitle="Acompanhe cotações e receba alertas por e-mail."
      footer={
        <>
          Ainda não tem conta?{' '}
          <Link to="/register" className="font-medium text-brand hover:underline">
            Cadastre-se
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <FormField
          id="email"
          label="E-mail"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={update('email')}
          error={errors.email}
        />
        <FormField
          id="password"
          label="Senha"
          type="password"
          autoComplete="current-password"
          value={form.password}
          onChange={update('password')}
          error={errors.password}
        />
        <Button type="submit" loading={loading} className="w-full">
          Entrar
        </Button>
      </form>
    </AuthLayout>
  )
}

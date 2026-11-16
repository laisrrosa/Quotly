import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import AuthLayout from '../components/AuthLayout.jsx'
import Button from '../components/Button.jsx'
import FormField from '../components/FormField.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { getErrorMessage } from '../services/api.js'

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function validate({ name, email, password, confirm }) {
  const errors = {}
  if (name.trim().length < 2) errors.name = 'Informe seu nome.'
  if (!EMAIL_REGEX.test(email)) errors.email = 'Informe um e-mail válido.'
  if (password.length < 6) errors.password = 'A senha precisa ter pelo menos 6 caracteres.'
  if (confirm !== password) errors.confirm = 'As senhas não coincidem.'
  return errors
}

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
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
    const found = validate(form)
    setErrors(found)
    if (Object.keys(found).length) return

    setLoading(true)
    try {
      await register(form.name, form.email, form.password)
      toast.success('Conta criada com sucesso!')
      navigate('/dashboard', { replace: true })
    } catch (err) {
      toast.error(getErrorMessage(err, 'Não foi possível criar a conta.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      title="Criar conta"
      subtitle="Leva menos de um minuto."
      footer={
        <>
          Já tem conta?{' '}
          <Link to="/login" className="font-medium text-brand hover:underline">
            Entrar
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <FormField
          id="name"
          label="Nome"
          autoComplete="name"
          value={form.name}
          onChange={update('name')}
          error={errors.name}
        />
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
          autoComplete="new-password"
          value={form.password}
          onChange={update('password')}
          error={errors.password}
        />
        <FormField
          id="confirm"
          label="Confirmar senha"
          type="password"
          autoComplete="new-password"
          value={form.confirm}
          onChange={update('confirm')}
          error={errors.confirm}
        />
        <Button type="submit" loading={loading} className="w-full">
          Criar conta
        </Button>
      </form>
    </AuthLayout>
  )
}

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { supabase } from '../lib/supabase'
import Alert from '../components/Alert'
import { useAuthStore } from '../store/authStore'

export default function Register() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('buyer')
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const [error, setError] = useState('')
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()

  async function handleEmailRegister(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await api.post('/auth/register', { name, email, password, role })
      login(data.token, data.user)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleGoogleRegister() {
    setError('')
    setGoogleLoading(true)
    try {
      const redirectTo = `${window.location.origin}/auth/callback`
      const { error: oauthError } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo },
      })
      if (oauthError) throw oauthError
    } catch (err) {
      setError(err.message)
      setGoogleLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.08),_transparent_28%),linear-gradient(to_bottom,_#050505,_#0b0b0d_55%,_#050505)] px-4">
      <div className="grid w-full max-w-5xl gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="rounded-3xl border border-white/10 bg-white/8 p-8 text-gray-100 shadow-[0_10px_40px_rgba(0,0,0,0.35)] backdrop-blur-2xl">
          <p className="mb-3 text-xs uppercase tracking-[0.35em] text-gray-400">Create access</p>
          <h1 className="text-3xl font-black tracking-tight sm:text-5xl">Join Dhandha in minutes</h1>
          <p className="mt-4 max-w-xl text-sm leading-6 text-gray-300 sm:text-base">
            Create an account with email/password or start with Google. You can switch between both later.
          </p>
        </div>

        <div className="rounded-3xl border border-white/10 bg-white/8 p-6 text-gray-100 shadow-[0_10px_40px_rgba(0,0,0,0.35)] backdrop-blur-2xl">
          <h2 className="mb-2 text-xl font-bold">Register</h2>
          <p className="mb-4 text-sm text-gray-400">Pick the method that feels easiest.</p>

          <Alert type="error">{error}</Alert>

          <form onSubmit={handleEmailRegister} className="space-y-3">
            <div>
              <label className="mb-1 block text-sm text-gray-300">Name</label>
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2.5 text-gray-100 outline-none transition focus:border-white/25"
                placeholder="Your name"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-300">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2.5 text-gray-100 outline-none transition focus:border-white/25"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-300">Password</label>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2.5 text-gray-100 outline-none transition focus:border-white/25"
                placeholder="At least 6 characters"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-gray-300">Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2.5 text-gray-100 outline-none transition focus:border-white/25"
              >
                <option value="buyer">Buyer</option>
                <option value="seller">Seller</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex w-full items-center justify-center rounded-full bg-white px-6 py-3 font-semibold text-gray-900 shadow-[0_10px_30px_rgba(255,255,255,0.12)] transition duration-300 ease-out hover:-translate-y-0.5 hover:bg-white/90 hover:shadow-[0_16px_40px_rgba(255,255,255,0.14)] disabled:translate-y-0 disabled:opacity-50"
            >
              {loading ? 'Creating account...' : 'Create with email'}
            </button>
          </form>

          <div className="my-5 flex items-center gap-3 text-xs uppercase tracking-[0.35em] text-gray-500">
            <span className="h-px flex-1 bg-white/10" />
            or
            <span className="h-px flex-1 bg-white/10" />
          </div>

          <button
            type="button"
            onClick={handleGoogleRegister}
            disabled={googleLoading}
            className="inline-flex w-full items-center justify-center rounded-full border border-white/10 bg-white/95 px-6 py-3 font-semibold text-gray-900 shadow-[0_10px_30px_rgba(255,255,255,0.12)] transition duration-300 ease-out hover:-translate-y-0.5 hover:bg-white disabled:translate-y-0 disabled:opacity-50"
          >
            {googleLoading ? 'Redirecting...' : 'Continue with Google'}
          </button>

          <p className="mt-4 text-center text-sm text-gray-400">
            Already have an account? <Link to="/login" className="text-white">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

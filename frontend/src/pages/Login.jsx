import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { supabase } from '../lib/supabase'
import Alert from '../components/Alert'
import { useAuthStore } from '../store/authStore'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const [error, setError] = useState('')
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()

  async function handleEmailLogin(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await api.post('/auth/login', { email, password })
      login(data.token, data.user)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleGoogleLogin() {
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
      <div className="w-full max-w-xl rounded-3xl border border-white/10 bg-white/8 p-6 text-gray-100 shadow-[0_10px_40px_rgba(0,0,0,0.35)] backdrop-blur-2xl">
        <div className="text-center">
          <p className="mb-3 text-xs uppercase tracking-[0.35em] text-gray-400">Welcome back</p>
          <h1 className="text-3xl font-black tracking-tight sm:text-5xl">
            Sign in to your Dhandha account
          </h1>
        </div>

        <div className="mx-auto mt-8 max-w-md">
          <h2 className="mb-2 text-xl font-bold">Log in</h2>
          <p className="mb-4 text-sm text-gray-400">Choose your preferred sign-in method.</p>

          <Alert type="error">{error}</Alert>

          <form onSubmit={handleEmailLogin} className="space-y-3">
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
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2.5 text-gray-100 outline-none transition focus:border-white/25"
                placeholder="Your password"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex w-full items-center justify-center rounded-full bg-white px-6 py-3 font-semibold text-gray-900 shadow-[0_10px_30px_rgba(255,255,255,0.12)] transition duration-300 ease-out hover:-translate-y-0.5 hover:bg-white/90 hover:shadow-[0_16px_40px_rgba(255,255,255,0.14)] disabled:translate-y-0 disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign in with email'}
            </button>
          </form>

          <div className="my-5 flex items-center gap-3 text-xs uppercase tracking-[0.35em] text-gray-500">
            <span className="h-px flex-1 bg-white/10" />
            or
            <span className="h-px flex-1 bg-white/10" />
          </div>

          <button
            type="button"
            onClick={handleGoogleLogin}
            disabled={googleLoading}
            className="inline-flex w-full items-center justify-center rounded-full border border-white/10 bg-white/95 px-6 py-3 font-semibold text-gray-900 shadow-[0_10px_30px_rgba(255,255,255,0.12)] transition duration-300 ease-out hover:-translate-y-0.5 hover:bg-white disabled:translate-y-0 disabled:opacity-50"
          >
            {googleLoading ? 'Redirecting...' : 'Continue with Google'}
          </button>

          <p className="mt-4 text-center text-sm text-gray-400">
            Need an account? <Link to="/register" className="text-white">Register</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

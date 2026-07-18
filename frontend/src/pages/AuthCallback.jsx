import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { supabase } from '../lib/supabase'
import { useAuthStore } from '../store/authStore'

export default function AuthCallback() {
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)
  const setSupabaseUser = useAuthStore((s) => s.setSupabaseUser)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true

    async function finishLogin() {
      const { data: sessionData, error: sessionError } = await supabase.auth.getSession()
      const session = sessionData?.session
      if (sessionError || !session) {
        throw sessionError || new Error('No Supabase session found')
      }

      const data = await api.post('/auth/supabase', {
        access_token: session.access_token,
      })

      if (!mounted) return

      setSupabaseUser(session.user)
      login(data.token, data.user)
      navigate('/dashboard', { replace: true })
    }

    finishLogin().catch((err) => {
      if (mounted) setError(err.message)
    })

    return () => {
      mounted = false
    }
  }, [login, navigate, setSupabaseUser])

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="rounded-3xl border border-white/10 bg-white/8 p-8 text-center text-gray-100 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl">
        <p className="text-lg font-medium">Finishing Google sign-in...</p>
        {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
      </div>
    </div>
  )
}

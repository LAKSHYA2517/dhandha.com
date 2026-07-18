import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import BlurText from '../components/BlurText'
import { useAuthStore } from '../store/authStore'

export default function Dashboard() {
  const user = useAuthStore((s) => s.user)
  const [company, setCompany] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/company/me')
      .then((data) => setCompany(data.company))
      .catch(() => setCompany(null))
      .finally(() => setLoading(false))
  }, [])

  const headline = useMemo(() => {
    const name = user?.name ? user.name.split(' ')[0] : 'there'
    return `Welcome back, ${name}`
  }, [user?.name])

  return (
    <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center px-4">
      <div className="w-full max-w-4xl text-center">
        <div className="mb-10">
          <BlurText
            text={headline}
            delay={150}
            animateBy="words"
            direction="top"
            onAnimationComplete={() => {}}
            className="text-4xl font-black tracking-tight sm:text-6xl"
          />
          <p className="mt-4 text-base text-gray-400 sm:text-lg">{user?.role} account dashboard</p>
        </div>

        {loading ? (
          <div className="inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/8 px-5 py-3 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl">
            <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-white" />
            <p className="text-sm text-gray-300">Loading dashboard</p>
          </div>
        ) : company ? (
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard label="Company" value={company.name} />
            <StatCard label="RCI Score" value={company.rci_score ?? 'Not calculated'} />
            <StatCard
              label="Compliance"
              value={company.compliance_status ? 'Compliant' : 'Pending'}
            />
          </div>
        ) : (
          <div className="mx-auto max-w-xl rounded-3xl border border-white/10 bg-white/8 p-8 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl">
            <p className="mb-4 text-lg font-medium">
              You haven&apos;t set up a company profile yet.
            </p>
            <Link
              to="/company"
              className="inline-flex items-center justify-center rounded-full bg-white px-6 py-3 font-semibold text-gray-900 shadow-[0_10px_30px_rgba(255,255,255,0.12)] transition duration-300 ease-out hover:-translate-y-0.5 hover:bg-white/90 hover:shadow-[0_16px_40px_rgba(255,255,255,0.14)] active:translate-y-0"
            >
              Create your company profile
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/8 p-6 shadow-[0_10px_40px_rgba(0,0,0,0.2)] backdrop-blur-2xl">
      <p className="mb-3 text-sm uppercase tracking-[0.2em] text-gray-400">{label}</p>
      <p className="text-2xl font-semibold text-white">{value}</p>
    </div>
  )
}

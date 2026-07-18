import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Alert from '../components/Alert'

export default function Admin() {
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [companies, setCompanies] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.get('/admin/stats'), api.get('/admin/users'), api.get('/admin/companies')])
      .then(([s, u, c]) => {
        setStats(s.stats)
        setUsers(u.users)
        setCompanies(c.companies)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-gray-300">Loading...</p>

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-white">Admin Console</h1>
      <Alert type="error">{error}</Alert>

      {stats && (
        <div className="mb-6 grid gap-4 sm:grid-cols-4">
          <StatCard label="Users" value={stats.users} />
          <StatCard label="Companies" value={stats.companies} />
          <StatCard label="Documents" value={stats.documents} />
          <StatCard label="Avg RCI" value={stats.avgRCI} />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <h2 className="mb-2 font-semibold text-white">Users</h2>
          <div className="divide-y divide-white/10 overflow-hidden rounded-3xl border border-white/10 bg-white/8 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl">
            {users.map((u) => (
              <div key={u.id} className="flex justify-between p-3 text-sm text-gray-200">
                <span>
                  {u.name} · {u.email}
                </span>
                <span className="text-gray-400">{u.role}</span>
              </div>
            ))}
          </div>
        </div>
        <div>
          <h2 className="mb-2 font-semibold text-white">Companies</h2>
          <div className="divide-y divide-white/10 overflow-hidden rounded-3xl border border-white/10 bg-white/8 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl">
            {companies.map((c) => (
              <div key={c._id} className="flex justify-between p-3 text-sm text-gray-200">
                <span>
                  {c.name} · {c.country}
                </span>
                <span className="text-gray-400">RCI {c.rci_score ?? '—'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/8 p-4 shadow-[0_10px_40px_rgba(0,0,0,0.2)] backdrop-blur-2xl">
      <p className="text-sm text-gray-400">{label}</p>
      <p className="text-xl font-semibold text-white">{value}</p>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Alert from '../components/Alert'

export default function Matches() {
  const [matches, setMatches] = useState([])
  const [myCompany, setMyCompany] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [explanation, setExplanation] = useState(null)

  useEffect(() => {
    api
      .get('/match')
      .then((data) => {
        setMatches(data.matches)
        setMyCompany(data.myCompany)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  async function viewExplanation(companyId) {
    setExplanation(null)
    try {
      const data = await api.get(`/explanation/${companyId}`)
      setExplanation(data)
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) return <p className="text-gray-300">Loading...</p>

  return (
    <div>
      <h1 className="mb-1 text-2xl font-bold text-white">Partner Matches</h1>
      {myCompany && <p className="mb-4 text-gray-400">{myCompany.name} · RCI {myCompany.rciScore}</p>}
      <Alert type="error">{error}</Alert>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="grid gap-3 sm:grid-cols-2">
          {matches.length === 0 ? (
            <p className="text-gray-400">No matches found yet.</p>
          ) : (
            matches.map((m) => (
              <div
                key={m.companyId}
                className="rounded-3xl border border-white/10 bg-white/8 p-4 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl"
              >
                <p className="font-semibold text-white">{m.name}</p>
                <p className="text-sm text-gray-400">
                  {m.country} · {m.industry}
                </p>
                <p className="text-sm text-gray-200">
                  RCI: {m.rciScore} · Compatibility: {m.compatibilityScore}%
                </p>
                <p className={`text-sm ${m.complianceStatus ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {m.complianceStatus ? 'Compliant' : 'Pending review'}
                </p>
                <button onClick={() => viewExplanation(m.companyId)} className="mt-2 text-sm font-medium text-white">
                  Why this match? →
                </button>
              </div>
            ))
          )}
        </div>

        {explanation && (
          <div className="h-fit rounded-3xl border border-white/10 bg-white/8 p-4 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl">
            <h2 className="mb-2 font-semibold text-white">{explanation.targetCompany.name}</h2>
            <p className="mb-3 text-sm font-medium text-gray-200">{explanation.explanation.recommendation}</p>
            <ul className="mb-3 list-disc list-inside space-y-1 text-sm text-gray-300">
              {explanation.explanation.reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
            {explanation.explanation.warnings.length > 0 && (
              <ul className="list-disc list-inside space-y-1 text-sm text-amber-400">
                {explanation.explanation.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

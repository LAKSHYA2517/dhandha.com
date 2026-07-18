import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Alert from '../components/Alert'

const defaultSubcomponents = {
  core: { AS: 0.7, DC: 0.7, RF: 0.7, CS: 0.7, PC: 0.7 },
  external: { CR: 0.7, TLR: 0.7, MSP: 1.0, CI: 0.7 },
  operational: { LR: 0.7, CCP: 0.7 },
  macro: { FH: 0.7, FB: 0.7, DV: 0.7 },
}

const FIELD_LABELS = {
  AS: 'Audit Score', DC: 'Documentation Completeness', RF: 'Regulatory Filing',
  CS: 'Compliance Standing', PC: 'Policy Conformance',
  CR: 'Country Risk', TLR: 'Trade Law Risk', MSP: 'Market Sanctions Position (0 = sanctioned)', CI: 'Corruption Index',
  LR: 'Litigation Risk', CCP: 'Corporate Compliance Program',
  FH: 'Financial Health', FB: 'Financial Backing', DV: 'Demand Volatility',
}

export default function Rci() {
  const [company, setCompany] = useState(null)
  const [subcomponents, setSubcomponents] = useState(defaultSubcomponents)
  const [tradeRoute, setTradeRoute] = useState('generic')
  const [loading, setLoading] = useState(true)
  const [calculating, setCalculating] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  function load() {
    return api
      .get('/company/me')
      .then((data) => {
        setCompany(data.company)
        if (data.company.rci_subcomponents && Object.keys(data.company.rci_subcomponents).length > 0) {
          setSubcomponents(data.company.rci_subcomponents)
        }
      })
      .catch(() => setCompany(null))
  }

  useEffect(() => {
    load().finally(() => setLoading(false))
  }, [])

  function handleFieldChange(group, key, value) {
    setSubcomponents({
      ...subcomponents,
      [group]: { ...subcomponents[group], [key]: Number(value) },
    })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!company) return
    setError('')
    setCalculating(true)
    try {
      const data = await api.post(`/company/${company._id}/run-compliance`, {
        subcomponents,
        vendor_data: { name: company.name, country: company.country, industry: company.industry },
        trade_route: tradeRoute,
      })
      setResult(data)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setCalculating(false)
    }
  }

  if (loading) return <p>Loadingâ€¦</p>

  if (!company) {
    return <p className="text-gray-400">Create a company profile first to calculate an RCI score.</p>
  }

  return (
    <div className="max-w-4xl">
      <h1 className="mb-4 text-2xl font-bold text-white">Regulatory Compliance Index</h1>
      <Alert type="error">{error}</Alert>

      {(result || company.current_rci_score != null) && (
        <div className="mb-6 rounded-3xl border border-white/10 bg-white/8 p-6 text-gray-100 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl">
          <p className="mb-1 text-4xl font-bold">{result?.rci_score ?? company.current_rci_score}</p>
          {(result?.explanation || company.latest_ai_explanation) && (
            <p className="mb-3 text-sm text-gray-300">
              {result?.explanation ?? company.latest_ai_explanation}
            </p>
          )}
          {(result?.breakdown || company.rci_breakdown) && (
            <div className="grid gap-3 sm:grid-cols-3 text-sm">
              {Object.entries(result?.breakdown ?? company.rci_breakdown).map(([key, value]) => (
                <div key={key} className="rounded-2xl border border-white/10 bg-black/15 p-3">
                  <p className="text-gray-400">{key}</p>
                  <p className="font-semibold text-white">{String(value)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-3xl border border-white/10 bg-white/8 p-6 text-gray-100 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl"
      >
        <div>
          <label className="mb-1 block text-sm text-gray-300">Trade Route</label>
          <input
            value={tradeRoute}
            onChange={(e) => setTradeRoute(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-gray-100 outline-none focus:border-white/25"
          />
        </div>

        {Object.entries(subcomponents).map(([group, fields]) => (
          <div key={group}>
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-gray-400">{group}</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              {Object.entries(fields).map(([key, value]) => (
                <div key={key}>
                  <label className="mb-1 block text-xs text-gray-300">
                    {FIELD_LABELS[key] || key} ({key})
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.05"
                    value={value}
                    onChange={(e) => handleFieldChange(group, key, e.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-gray-100 outline-none focus:border-white/25"
                  />
                </div>
              ))}
            </div>
          </div>
        ))}

        <button
          type="submit"
          disabled={calculating}
          className="w-full rounded-full bg-white py-2 font-semibold text-gray-900 transition hover:bg-white/90 disabled:opacity-50"
        >
          {calculating ? 'Running compliance checkâ€¦' : 'Run Compliance Check'}
        </button>
      </form>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Alert from '../components/Alert'

const emptyForm = {
  name: '',
  country: '',
  industry: '',
  trade_category: '',
  description: '',
  contact_email: '',
  website: '',
}

export default function Company() {
  const [company, setCompany] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    api
      .get('/company/me')
      .then((data) => {
        setCompany(data.company)
        setForm({ ...emptyForm, ...data.company })
      })
      .catch(() => setCompany(null))
      .finally(() => setLoading(false))
  }, [])

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setSaving(true)
    try {
      const data = company
        ? await api.put('/company/me', form)
        : await api.post('/company', form)
      setCompany(data.company)
      setSuccess('Company profile saved.')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p>Loading…</p>

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-4 text-white">Company Profile</h1>
      <Alert type="error">{error}</Alert>
      <Alert type="success">{success}</Alert>
      <form onSubmit={handleSubmit} className="rounded-3xl border border-white/10 bg-white/8 p-6 space-y-3 text-gray-100 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl">
        <Field label="Company Name" name="name" value={form.name} onChange={handleChange} required />
        <Field label="Country" name="country" value={form.country} onChange={handleChange} required />
        <Field label="Industry" name="industry" value={form.industry} onChange={handleChange} required />
        <Field label="Trade Category" name="trade_category" value={form.trade_category} onChange={handleChange} required />
        <Field label="Description" name="description" value={form.description} onChange={handleChange} />
        <Field label="Contact Email" name="contact_email" value={form.contact_email} onChange={handleChange} />
        <Field label="Website" name="website" value={form.website} onChange={handleChange} />
        <button
          type="submit"
          disabled={saving}
          className="w-full rounded-full bg-white py-2 font-semibold text-gray-900 transition hover:bg-white/90 disabled:opacity-50"
        >
          {saving ? 'Saving…' : company ? 'Update Profile' : 'Create Profile'}
        </button>
      </form>
    </div>
  )
}

function Field({ label, name, value, onChange, required }) {
  return (
    <div>
      <label className="block text-sm mb-1 text-gray-300">{label}</label>
      <input
        name={name}
        value={value || ''}
        onChange={onChange}
        required={required}
        className="w-full px-3 py-2 rounded-xl border border-white/10 bg-black/20 text-gray-100 outline-none focus:border-white/25"
      />
    </div>
  )
}

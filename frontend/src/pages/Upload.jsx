import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Alert from '../components/Alert'

const DOC_TYPES = [
  { value: 'trade_license', label: 'Trade License' },
  { value: 'iso_certificate', label: 'ISO Certificate' },
  { value: 'tax_compliance', label: 'Tax Compliance' },
  { value: 'export_permit', label: 'Export Permit' },
  { value: 'quality_cert', label: 'Quality Certificate' },
  { value: 'other', label: 'Other' },
]

export default function Upload() {
  const [documents, setDocuments] = useState([])
  const [type, setType] = useState('trade_license')
  const [expiryDate, setExpiryDate] = useState('')
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(true)

  function loadDocuments() {
    return api
      .get('/upload/my-documents')
      .then((data) => setDocuments(data.documents))
      .catch(() => setDocuments([]))
  }

  useEffect(() => {
    loadDocuments().finally(() => setLoading(false))
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('type', type)
      formData.append('expiry_date', expiryDate)
      if (file) formData.append('document', file)
      await api.upload('/upload', formData)
      setFile(null)
      setExpiryDate('')
      await loadDocuments()
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-5xl">
      <h1 className="mb-4 text-2xl font-bold text-white">Compliance Documents</h1>
      <Alert type="error">{error}</Alert>

      <form
        onSubmit={handleSubmit}
        className="mb-6 flex flex-wrap items-end gap-3 rounded-3xl border border-white/10 bg-white/8 p-6 text-gray-100 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl"
      >
        <div>
          <label className="mb-1 block text-sm text-gray-300">Document Type</label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-gray-100 outline-none focus:border-white/25"
          >
            {DOC_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-300">Expiry Date</label>
          <input
            type="date"
            required
            value={expiryDate}
            onChange={(e) => setExpiryDate(e.target.value)}
            className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-gray-100 outline-none focus:border-white/25"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-300">File (optional)</label>
          <input
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={(e) => setFile(e.target.files[0])}
            className="block text-sm text-gray-300 file:mr-4 file:rounded-full file:border-0 file:bg-white file:px-4 file:py-2 file:font-semibold file:text-gray-900 file:transition file:duration-300 hover:file:-translate-y-0.5 hover:file:bg-gray-100"
          />
        </div>
        <button
          type="submit"
          disabled={uploading}
          className="inline-flex items-center justify-center rounded-full bg-white px-6 py-2.5 font-semibold text-gray-900 shadow-[0_10px_30px_rgba(255,255,255,0.12)] transition duration-300 ease-out hover:-translate-y-0.5 hover:bg-white/90 hover:shadow-[0_16px_40px_rgba(255,255,255,0.14)] active:translate-y-0 disabled:translate-y-0 disabled:opacity-50"
        >
          {uploading ? 'Uploading...' : 'Upload Document'}
        </button>
      </form>

      <h2 className="mb-2 font-semibold text-white">My Documents</h2>
      {loading ? (
        <p className="text-gray-400">Loading...</p>
      ) : documents.length === 0 ? (
        <p className="text-gray-400">No documents uploaded yet.</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {documents.map((doc) => (
            <div
              key={doc._id}
              className="rounded-2xl border border-white/10 bg-white/8 p-4 text-gray-100 shadow-[0_10px_40px_rgba(0,0,0,0.2)] backdrop-blur-2xl"
            >
              <p className="font-medium">{doc.original_name}</p>
              <p className="text-sm text-gray-400">{doc.type.replace('_', ' ')}</p>
              <p className="text-sm text-gray-300">Issuer: {doc.issuing_authority}</p>
              <p className="text-sm text-gray-300">Expires: {new Date(doc.expiry_date).toLocaleDateString()}</p>
              <p className={`text-sm font-medium ${doc.is_valid ? 'text-green-400' : 'text-red-300'}`}>
                {doc.is_valid ? 'Valid' : 'Invalid/Expired'}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

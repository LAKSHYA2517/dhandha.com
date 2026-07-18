import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useCartStore } from '../store/cartStore'
import { posterUrl } from '../lib/images'
import Alert from './Alert'
import RciBadge from './RciBadge'

function daysUntil(dateStr) {
  if (!dateStr) return null
  const diffMs = new Date(dateStr).getTime() - Date.now()
  return Math.ceil(diffMs / (1000 * 60 * 60 * 24))
}

function Field({ label, value }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wide text-gray-500">{label}</p>
      <p className="text-gray-200">{value || '—'}</p>
    </div>
  )
}

// Demo-only specimen certificates (frontend/public/demo-certs) — styled to look
// like a real Indian compliance document but clearly fictional/watermarked, not
// a copy of any real government template. The holder name and signature are
// pre-blurred directly in the artwork; everything else (issuer, cert type,
// cert no.) stays legible, so it demonstrates *selective* masking rather than
// covering the whole document.
const CERT_IMAGES = {
  trade_license: '/demo-certs/trade_license.svg',
  iso_certificate: '/demo-certs/iso_certificate.svg',
  tax_compliance: '/demo-certs/tax_compliance.svg',
  export_permit: '/demo-certs/export_permit.svg',
  quality_cert: '/demo-certs/quality_cert.svg',
}

function MaskedDocumentCard({ doc }) {
  const days = daysUntil(doc.expiry_date)
  const expiringSoon = days !== null && days <= 30 && days >= 0
  const expired = days !== null && days < 0
  const meta = doc.extracted_metadata || {}
  const certImage = CERT_IMAGES[doc.type] || CERT_IMAGES.trade_license

  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/5">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-2.5">
        <p className="text-sm font-semibold text-white">{doc.label}</p>
        <span className={`text-xs font-medium ${doc.is_valid ? 'text-green-400' : 'text-red-400'}`}>
          {doc.is_valid ? 'Valid' : 'Invalid'}
        </span>
      </div>

      <div className="grid gap-px bg-white/10 sm:grid-cols-2">
        <div className="space-y-3 bg-[#0b0b0d] p-4 text-xs">
          <img src={certImage} alt={`${doc.label} specimen`} className="w-full rounded-lg border border-white/10" />
          <div className="grid grid-cols-2 gap-3 pt-1">
            <Field label="Issuing Authority" value={doc.issuing_authority} />
            <Field label="Certificate Type" value={meta.certificate_type} />
            <Field label="Status" value={meta.status} />
            <Field
              label="Valid Until"
              value={
                expired
                  ? `Expired ${Math.abs(days)}d ago`
                  : expiringSoon
                  ? `${days}d remaining`
                  : meta.expiry_date
              }
            />
          </div>
          <p className="pt-1 text-[10px] text-gray-500">🔒 Holder name & signature masked by SecureWatch AI</p>
        </div>

        <div className="bg-[#0b0b0d] p-4 text-xs">
          <p className="mb-2 text-[10px] uppercase tracking-wide text-gray-500">Structured Extraction (Gemma)</p>
          <pre className="overflow-x-auto rounded-lg bg-black/30 p-2 text-gray-300">
{JSON.stringify(meta, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  )
}

export default function ProductDetailModal({ product, onClose }) {
  const seller = product.seller
  const [documents, setDocuments] = useState([])
  const [docsLoading, setDocsLoading] = useState(true)
  const [docsError, setDocsError] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [cartMessage, setCartMessage] = useState('')
  const [cartError, setCartError] = useState('')
  const addItem = useCartStore((s) => s.addItem)

  useEffect(() => {
    let cancelled = false
    setDocsLoading(true)
    api
      .get(`/company/${seller.company_id}/documents`)
      .then((data) => {
        if (!cancelled) setDocuments(data.documents)
      })
      .catch((err) => {
        if (!cancelled) setDocsError(err.message)
      })
      .finally(() => {
        if (!cancelled) setDocsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [seller.company_id])

  function handleAddToCart() {
    setCartError('')
    setCartMessage('')
    if (quantity < 1 || quantity > product.quantity_available) {
      setCartError(`Choose a quantity between 1 and ${product.quantity_available}.`)
      return
    }
    addItem(product, quantity)
    setCartMessage(`Added ${quantity} × ${product.name} to cart.`)
  }

  const breakdown = seller.rci_breakdown || {}
  const sub = seller.rci_subcomponents || {}
  const rf = sub.core?.RF ?? null

  const soonestExpiry = documents
    .map((d) => ({ label: d.label, days: daysUntil(d.expiry_date) }))
    .filter((d) => d.days !== null)
    .sort((a, b) => a.days - b.days)[0]

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/70 p-4 backdrop-blur-sm">
      <div className="my-8 w-full max-w-3xl overflow-hidden rounded-3xl border border-white/10 bg-[#0b0b0d] shadow-[0_20px_80px_rgba(0,0,0,0.6)]">
        <img src={posterUrl(product)} alt={product.name} className="h-56 w-full object-cover" />

        <div className="flex items-start justify-between border-b border-white/10 p-5">
          <div>
            <h2 className="text-xl font-bold text-white">{product.name}</h2>
            <p className="text-sm text-gray-400">
              Sold by {seller.name} ({seller.country}) · {seller.industry}
            </p>
          </div>
          <button onClick={onClose} className="text-xl leading-none text-gray-400 transition hover:text-white">
            ×
          </button>
        </div>

        <div className="space-y-6 p-5">
          {/* Buy section */}
          <section>
            {product.description && <p className="mb-3 text-sm text-gray-300">{product.description}</p>}
            <p className="mb-3 text-sm text-gray-200">
              {product.currency} {product.price} · {product.quantity_available} available
            </p>
            <Alert type="error">{cartError}</Alert>
            <Alert type="success">{cartMessage}</Alert>
            <div className="flex gap-2">
              <input
                type="number"
                min="1"
                max={product.quantity_available}
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                className="w-20 rounded-xl border border-white/10 bg-black/20 px-2 py-2 text-gray-100 outline-none focus:border-white/25"
              />
              <button
                onClick={handleAddToCart}
                className="flex-1 rounded-full bg-white py-2 font-semibold text-gray-900 transition hover:bg-white/90"
              >
                Add to Cart
              </button>
            </div>
          </section>

          {/* RCI Equation Visualizer */}
          <section>
            <div className="mb-3 flex items-center gap-3">
              <span className="text-3xl font-bold text-white">
                {(seller.current_rci_score ?? 0).toFixed(1)}
              </span>
              <RciBadge score={seller.current_rci_score ?? 0} />
            </div>
            <div className="grid gap-3 text-sm sm:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                <p className="mb-1 font-medium text-white">Expiration Decay</p>
                <p className="text-gray-400">
                  {soonestExpiry
                    ? soonestExpiry.days >= 0
                      ? `${soonestExpiry.label} expiring in ${soonestExpiry.days} day${soonestExpiry.days === 1 ? '' : 's'}`
                      : `${soonestExpiry.label} expired ${Math.abs(soonestExpiry.days)} day${Math.abs(soonestExpiry.days) === 1 ? '' : 's'} ago`
                    : 'No expiry data available'}
                  {typeof breakdown.missing_doc_penalty === 'number' && (
                    <> ({breakdown.missing_doc_penalty.toFixed(2)}x penalty applied)</>
                  )}
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                <p className="mb-1 font-medium text-white">Historical Risk</p>
                <p className="text-gray-400">
                  {rf !== null ? `${rf.toFixed(2)} risk factor score` : 'Not yet assessed'}
                  {rf === 1 && ' — no historical default flags'}
                </p>
              </div>
            </div>
          </section>

          {/* Qualitative explanation */}
          <section>
            <p className="mb-1 font-medium text-white">Gemma 4 Compliance Officer Reasoning</p>
            <div className="rounded-2xl border border-purple-400/20 bg-purple-500/10 p-3 text-sm text-gray-200">
              {seller.latest_ai_explanation || 'No AI assessment on file yet for this vendor.'}
            </div>
          </section>

          {/* Privacy engine visualizer */}
          <section>
            <p className="mb-2 font-medium text-white">Document Privacy Engine</p>
            {docsLoading && <p className="text-sm text-gray-400">Loading documents…</p>}
            {docsError && <p className="text-sm text-red-400">{docsError}</p>}
            {!docsLoading && !docsError && documents.length === 0 && (
              <p className="text-sm text-gray-400">No documents uploaded yet.</p>
            )}
            <div className="space-y-3">
              {documents.map((doc, i) => (
                <MaskedDocumentCard key={i} doc={doc} />
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

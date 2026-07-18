import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import Alert from '../components/Alert'
import ProductDetailModal from '../components/ProductDetailModal'
import RciBadge from '../components/RciBadge'
import { posterUrl } from '../lib/images'

function ProductPoster({ product, onOpen }) {
  return (
    <button
      onClick={() => onOpen(product)}
      className="group relative aspect-[3/4] w-44 flex-none overflow-hidden rounded-2xl border border-white/10 bg-white/5 text-left shadow-[0_10px_30px_rgba(0,0,0,0.35)] ring-1 ring-white/0 transition-all duration-300 hover:z-10 hover:-translate-y-1.5 hover:scale-[1.04] hover:shadow-[0_20px_50px_rgba(0,0,0,0.55)] hover:ring-white/15 sm:w-48"
    >
      <img
        src={posterUrl(product)}
        alt={product.name}
        className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/25 to-transparent" />
      <div className="absolute right-2 top-2">
        <RciBadge score={product.seller.current_rci_score ?? 0} />
      </div>
      <div className="absolute inset-x-0 bottom-0 p-3">
        <p className="line-clamp-2 text-sm font-semibold leading-snug text-white">{product.name}</p>
        <p className="mt-1 truncate text-xs text-gray-400">{product.seller.name}</p>
        <p className="mt-0.5 text-xs font-medium text-gray-200">{product.currency} {product.price}</p>
      </div>
    </button>
  )
}

export default function Marketplace() {
  const [products, setProducts] = useState([])
  const [search, setSearch] = useState('')
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/products')
      .then((data) => setProducts(data.products))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase()
    if (!query) return products
    return products.filter((p) => {
      const complianceLabel = p.seller.compliance_status ? 'compliant' : 'pending review'
      return (
        p.name?.toLowerCase().includes(query) ||
        p.seller.name?.toLowerCase().includes(query) ||
        p.category?.toLowerCase().includes(query) ||
        complianceLabel.includes(query)
      )
    })
  }, [products, search])

  const lanes = useMemo(() => {
    const grouped = new Map()
    for (const p of filtered) {
      const industry = p.seller.industry?.trim() || p.category?.trim() || 'Other'
      if (!grouped.has(industry)) grouped.set(industry, [])
      grouped.get(industry).push(p)
    }
    return Array.from(grouped.entries()).sort((a, b) => a[0].localeCompare(b[0]))
  }, [filtered])

  if (loading) return <p className="text-gray-400">Loading…</p>

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Marketplace</h1>
        <Link to="/cart" className="font-medium text-white transition hover:text-gray-300">View Cart →</Link>
      </div>
      <Alert type="error">{error}</Alert>

      <input
        type="text"
        placeholder="Search products, vendors, or compliance status…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-8 w-full rounded-full border border-white/10 bg-black/20 px-4 py-2.5 text-gray-100 outline-none backdrop-blur-2xl focus:border-white/25"
      />

      {lanes.length === 0 && <p className="mb-8 text-gray-400">No products match your search.</p>}

      <div className="space-y-8">
        {lanes.map(([industry, laneProducts]) => (
          <section key={industry}>
            <h2 className="mb-3 text-lg font-semibold text-white">{industry}</h2>
            <div className="flex gap-4 overflow-x-auto scrollbar-none pb-2">
              {laneProducts.map((p) => (
                <ProductPoster key={p.id} product={p} onOpen={setSelectedProduct} />
              ))}
            </div>
          </section>
        ))}
      </div>

      {selectedProduct && (
        <ProductDetailModal product={selectedProduct} onClose={() => setSelectedProduct(null)} />
      )}
    </div>
  )
}

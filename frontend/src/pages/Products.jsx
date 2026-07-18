import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Alert from '../components/Alert'

const emptyForm = {
  name: '',
  description: '',
  category: '',
  price: '',
  currency: 'INR',
  quantity_available: '',
}

export default function Products() {
  const [products, setProducts] = useState([])
  const [orders, setOrders] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  function loadAll() {
    return Promise.all([
      api.get('/products/mine').then((data) => setProducts(data.products)),
      api.get('/orders/received').then((data) => setOrders(data.orders)),
    ])
  }

  useEffect(() => {
    loadAll()
      .catch((err) => setError(err.message))
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
      await api.post('/products', {
        ...form,
        price: Number(form.price),
        quantity_available: Number(form.quantity_available),
      })
      setForm(emptyForm)
      setSuccess('Product listed successfully.')
      await loadAll()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id) {
    setError('')
    try {
      await api.delete(`/products/${id}`)
      await loadAll()
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading) return <p>Loading…</p>

  return (
    <div className="max-w-5xl">
      <h1 className="mb-4 text-2xl font-bold text-white">My Products</h1>
      <Alert type="error">{error}</Alert>
      <Alert type="success">{success}</Alert>

      <form
        onSubmit={handleSubmit}
        className="mb-6 grid gap-3 rounded-3xl border border-white/10 bg-white/8 p-6 text-gray-100 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl sm:grid-cols-2"
      >
        <Field label="Product Name" name="name" value={form.name} onChange={handleChange} required />
        <Field label="Category" name="category" value={form.category} onChange={handleChange} />
        <Field label="Price" name="price" type="number" min="0.01" step="0.01" value={form.price} onChange={handleChange} required />
        <Field label="Currency" name="currency" value={form.currency} onChange={handleChange} />
        <Field label="Quantity Available" name="quantity_available" type="number" min="0" value={form.quantity_available} onChange={handleChange} required />

        <div className="sm:col-span-2">
          <label className="mb-1 block text-sm text-gray-300">Description</label>
          <textarea
            name="description"
            value={form.description}
            onChange={handleChange}
            className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-gray-100 outline-none focus:border-white/25"
            rows={2}
          />
        </div>

        <button
          type="submit"
          disabled={saving}
          className="sm:col-span-2 w-full rounded-full bg-white py-2 font-semibold text-gray-900 transition hover:bg-white/90 disabled:opacity-50"
        >
          {saving ? 'Listing…' : 'List Product'}
        </button>

        <p className="sm:col-span-2 text-xs text-gray-400">
          Listing requires your company&apos;s current RCI score to be 50 or above. Run a compliance check on the RCI page if this fails.
        </p>
      </form>

      <h2 className="mb-2 font-semibold text-white">Active Listings</h2>
      {products.length === 0 ? (
        <p className="mb-6 text-gray-400">No products listed yet.</p>
      ) : (
        <div className="mb-6 grid gap-3 sm:grid-cols-2">
          {products.map((p) => (
            <div
              key={p._id}
              className="rounded-2xl border border-white/10 bg-white/8 p-4 text-gray-100 shadow-[0_10px_40px_rgba(0,0,0,0.2)] backdrop-blur-2xl"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium">{p.name}</p>
                  <p className="text-sm text-gray-400">{p.category || '—'}</p>
                </div>
                <button onClick={() => handleDelete(p._id)} className="text-sm text-red-300 transition hover:text-red-200">
                  Remove
                </button>
              </div>
              <p className="mt-2 text-sm text-gray-300">
                {p.currency} {p.price} · {p.quantity_available} available
              </p>
              <p className={`text-sm font-medium ${p.is_active ? 'text-green-400' : 'text-gray-400'}`}>
                {p.is_active ? 'Active' : 'Inactive'}
              </p>
            </div>
          ))}
        </div>
      )}

      <h2 className="mb-2 font-semibold text-white">Received Orders</h2>
      {orders.length === 0 ? (
        <p className="text-gray-400">No orders yet.</p>
      ) : (
        <div className="overflow-hidden rounded-3xl border border-white/10 bg-white/8 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl">
          <div className="divide-y divide-white/10">
            {orders.map((o) => (
              <div key={o._id} className="flex justify-between p-3 text-sm text-gray-200">
                <span>
                  {o.product_name} × {o.quantity}
                </span>
                <span className="text-gray-400">
                  {o.currency} {o.total_price}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function Field({ label, name, value, onChange, required, type = 'text', ...rest }) {
  return (
    <div>
      <label className="mb-1 block text-sm text-gray-300">{label}</label>
      <input
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        required={required}
        className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-gray-100 outline-none focus:border-white/25"
        {...rest}
      />
    </div>
  )
}

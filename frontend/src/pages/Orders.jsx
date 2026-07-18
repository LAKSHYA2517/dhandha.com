import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Alert from '../components/Alert'

export default function Orders() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/orders/mine')
      .then((data) => setOrders(data.orders))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-gray-400">Loading…</p>

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-white">My Orders</h1>
      <Alert type="error">{error}</Alert>

      {orders.length === 0 ? (
        <p className="text-gray-400">No orders yet.</p>
      ) : (
        <div className="overflow-hidden rounded-3xl border border-white/10 bg-white/8 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl">
          <div className="divide-y divide-white/10">
            {orders.map((o) => (
              <div key={o._id} className="flex justify-between p-3 text-sm text-gray-200">
                <span>{o.product_name} × {o.quantity}</span>
                <span className="text-gray-400">{o.currency} {o.total_price}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

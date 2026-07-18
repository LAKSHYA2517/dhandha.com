import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { api } from '../api/client'
import { useCartStore } from '../store/cartStore'
import Alert from '../components/Alert'

const emptyAddress = {
  full_name: '',
  phone: '',
  address_line1: '',
  address_line2: '',
  city: '',
  state: '',
  postal_code: '',
  country: '',
}

export default function Checkout() {
  const { items, total, clearCart } = useCartStore()
  const [address, setAddress] = useState(emptyAddress)
  const [placing, setPlacing] = useState(false)
  const [error, setError] = useState('')
  const [placedOrders, setPlacedOrders] = useState(null)

  function handleChange(e) {
    setAddress({ ...address, [e.target.name]: e.target.value })
  }

  async function handlePlaceOrder(e) {
    e.preventDefault()
    setError('')
    setPlacing(true)
    try {
      const results = []
      for (const item of items) {
        const data = await api.post(`/products/${item.productId}/order`, {
          quantity: item.quantity,
          shipping_address: address,
        })
        results.push(data.order)
      }
      setPlacedOrders(results)
      clearCart()
    } catch (err) {
      setError(err.message)
    } finally {
      setPlacing(false)
    }
  }

  if (placedOrders) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="max-w-xl"
      >
        <motion.div
          initial={{ scale: 0, rotate: -20 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ delay: 0.1, type: 'spring', stiffness: 260, damping: 14 }}
          className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full border border-green-500/30 bg-green-500/15"
        >
          <svg viewBox="0 0 24 24" className="h-8 w-8" fill="none">
            <motion.path
              d="M4 12.5 9.5 18 20 6"
              stroke="#4ade80"
              strokeWidth={2.5}
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ delay: 0.35, duration: 0.45, ease: 'easeOut' }}
            />
          </svg>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25, duration: 0.35 }}
          className="mb-4 text-center text-2xl font-bold text-white"
        >
          Order Placed!
        </motion.h1>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.35 }}
        >
          <Alert type="success">
            {placedOrders.length} order{placedOrders.length > 1 ? 's' : ''} placed successfully. The seller has been notified.
          </Alert>
          <div className="mb-4 overflow-hidden rounded-3xl border border-white/10 bg-white/8 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl">
            <div className="divide-y divide-white/10">
              {placedOrders.map((o) => (
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
          <Link to="/marketplace" className="font-medium text-white transition hover:text-gray-300">
            Continue shopping →
          </Link>
        </motion.div>
      </motion.div>
    )
  }

  if (items.length === 0) {
    return (
      <div>
        <h1 className="mb-4 text-2xl font-bold text-white">Checkout</h1>
        <p className="mb-4 text-gray-400">Your cart is empty.</p>
        <Link to="/marketplace" className="font-medium text-white">
          Browse the marketplace →
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-2xl">
      <h1 className="mb-4 text-2xl font-bold text-white">Checkout</h1>
      <Alert type="error">{error}</Alert>

      <div className="mb-6 rounded-3xl border border-white/10 bg-white/8 p-4 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl">
        <h2 className="mb-2 font-semibold text-white">Order Summary</h2>
        {items.map((item) => (
          <div key={item.productId} className="flex justify-between py-1 text-sm text-gray-200">
            <span>
              {item.name} × {item.quantity}
            </span>
            <span>
              {item.currency} {(item.price * item.quantity).toFixed(2)}
            </span>
          </div>
        ))}
        <div className="mt-2 flex justify-between border-t border-white/10 pt-2 font-semibold text-white">
          <span>Total</span>
          <span>
            {items[0]?.currency} {total().toFixed(2)}
          </span>
        </div>
      </div>

      <form
        onSubmit={handlePlaceOrder}
        className="space-y-3 rounded-3xl border border-white/10 bg-white/8 p-6 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl"
      >
        <h2 className="mb-2 font-semibold text-white">Shipping Address</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Full Name" name="full_name" value={address.full_name} onChange={handleChange} required />
          <Field label="Phone" name="phone" value={address.phone} onChange={handleChange} required />
          <Field label="Address Line 1" name="address_line1" value={address.address_line1} onChange={handleChange} required className="sm:col-span-2" />
          <Field label="Address Line 2 (optional)" name="address_line2" value={address.address_line2} onChange={handleChange} className="sm:col-span-2" />
          <Field label="City" name="city" value={address.city} onChange={handleChange} required />
          <Field label="State" name="state" value={address.state} onChange={handleChange} required />
          <Field label="Postal Code" name="postal_code" value={address.postal_code} onChange={handleChange} required />
          <Field label="Country" name="country" value={address.country} onChange={handleChange} required />
        </div>
        <button
          type="submit"
          disabled={placing}
          className="mt-4 w-full rounded-full bg-white py-2 font-semibold text-gray-900 transition hover:bg-white/90 disabled:opacity-50"
        >
          {placing ? 'Placing Order...' : 'Place Order'}
        </button>
      </form>
    </div>
  )
}

function Field({ label, name, value, onChange, required, className = '' }) {
  return (
    <div className={className}>
      <label className="mb-1 block text-sm text-gray-300">{label}</label>
      <input
        name={name}
        value={value}
        onChange={onChange}
        required={required}
        className="w-full rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-gray-100 outline-none focus:border-white/25"
      />
    </div>
  )
}

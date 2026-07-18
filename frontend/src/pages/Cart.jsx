import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'motion/react'
import { useCartStore } from '../store/cartStore'

export default function Cart() {
  const { items, updateQuantity, removeItem, total } = useCartStore()
  const navigate = useNavigate()

  if (items.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-4 text-white">Your Cart</h1>
        <p className="text-gray-400 mb-4">Your cart is empty.</p>
        <Link to="/marketplace" className="text-white font-medium transition hover:text-gray-300">
          Browse the marketplace →
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-4 text-white">Your Cart</h1>

      <div className="mb-4 overflow-hidden rounded-3xl border border-white/10 bg-white/8 divide-y divide-white/10 shadow-[0_10px_40px_rgba(0,0,0,0.25)] backdrop-blur-2xl">
        {items.map((item, index) => (
          <motion.div
            key={item.productId}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05, duration: 0.3, ease: 'easeOut' }}
            className="flex items-center gap-4 p-4"
          >
            {item.imageUrl ? (
              <img src={item.imageUrl} alt={item.name} className="h-16 w-16 rounded-xl object-cover" />
            ) : (
              <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-white/10 text-xs text-gray-400">
                No image
              </div>
            )}
            <div className="flex-1">
              <p className="font-medium text-white">{item.name}</p>
              <p className="text-sm text-gray-400">Sold by {item.sellerName}</p>
              <p className="text-sm text-gray-300">
                {item.currency} {item.price} each
              </p>
            </div>
            <input
              type="number"
              min="1"
              max={item.maxQuantity}
              value={item.quantity}
              onChange={(e) =>
                updateQuantity(
                  item.productId,
                  Math.max(1, Math.min(Number(e.target.value), item.maxQuantity)),
                )
              }
              className="w-16 rounded-lg border border-white/10 bg-black/20 px-2 py-1 text-center text-white outline-none focus:border-white/25"
            />
            <p className="w-24 text-right font-medium text-white">
              {item.currency} {(item.price * item.quantity).toFixed(2)}
            </p>
            <button onClick={() => removeItem(item.productId)} className="text-sm text-red-400 transition hover:text-red-300">
              Remove
            </button>
          </motion.div>
        ))}
      </div>

      <div className="mb-6 flex items-center justify-between">
        <p className="text-lg font-semibold text-white">
          Total: {items[0]?.currency} {total().toFixed(2)}
        </p>
        <button
          onClick={() => navigate('/checkout')}
          className="rounded-full bg-white px-6 py-2 font-medium text-gray-900 transition hover:-translate-y-0.5 hover:bg-white/90"
        >
          Proceed to Checkout
        </button>
      </div>
    </div>
  )
}

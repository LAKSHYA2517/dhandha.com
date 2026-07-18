import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useCartStore = create(
  persist(
    (set, get) => ({
      items: [],

      addItem: (product, quantity) => {
        const items = get().items
        const existing = items.find((i) => i.productId === product.id)
        if (existing) {
          set({
            items: items.map((i) =>
              i.productId === product.id
                ? { ...i, quantity: Math.min(i.quantity + quantity, product.quantity_available) }
                : i
            ),
          })
        } else {
          set({
            items: [
              ...items,
              {
                productId: product.id,
                name: product.name,
                price: product.price,
                currency: product.currency,
                imageUrl: product.image_url,
                sellerName: product.seller?.name,
                maxQuantity: product.quantity_available,
                quantity,
              },
            ],
          })
        }
      },

      updateQuantity: (productId, quantity) => {
        set({
          items: get().items.map((i) => (i.productId === productId ? { ...i, quantity } : i)),
        })
      },

      removeItem: (productId) => {
        set({ items: get().items.filter((i) => i.productId !== productId) })
      },

      clearCart: () => set({ items: [] }),

      itemCount: () => get().items.reduce((sum, i) => sum + i.quantity, 0),
      total: () => get().items.reduce((sum, i) => sum + i.quantity * i.price, 0),
    }),
    { name: 'ciq-cart' }
  )
)

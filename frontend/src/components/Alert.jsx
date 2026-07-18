export default function Alert({ type = 'info', children }) {
  if (!children) return null
  const styles = {
    error: 'bg-red-500/10 text-red-300 border-red-500/30',
    success: 'bg-green-500/10 text-green-300 border-green-500/30',
    info: 'bg-white/10 text-gray-100 border-white/20',
  }
  return (
    <div className={`border rounded-xl px-3 py-2 text-sm mb-4 backdrop-blur-sm ${styles[type]}`}>{children}</div>
  )
}

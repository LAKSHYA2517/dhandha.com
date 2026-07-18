export function rciTier(score) {
  if (score >= 70) return 'high'
  if (score >= 40) return 'medium'
  return 'critical'
}

const TIER_CLASSES = {
  high: 'bg-green-500/20 text-green-300 border-green-400/30',
  medium: 'bg-yellow-500/20 text-yellow-300 border-yellow-400/30',
  critical: 'bg-red-500/20 text-red-300 border-red-400/30',
}

export default function RciBadge({ score, className = '' }) {
  const value = score ?? 0
  const tier = rciTier(value)
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-bold backdrop-blur-md ${TIER_CLASSES[tier]} ${className}`}
    >
      RCI {value.toFixed ? value.toFixed(0) : value}
    </span>
  )
}

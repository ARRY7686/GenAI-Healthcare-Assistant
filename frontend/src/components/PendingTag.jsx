import { Clock } from 'lucide-react'

/** Small marker for UI whose backend feature isn't integrated yet. */
export default function PendingTag({ feature }) {
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-medium uppercase tracking-wide text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5">
      <Clock className="w-3 h-3" />
      Pending{feature ? ` · feature #${feature}` : ''}
    </span>
  )
}

import { Phone, AlertTriangle } from 'lucide-react'
import PendingTag from '@/components/PendingTag'

/**
 * Feature #6 — Safety Guardrails surface (UI only; not integrated).
 * Shown when a deterministic red-flag override routes the case to emergency. India: 112 / 108.
 */
export default function EmergencyBanner({ pending = false }) {
  return (
    <div className="rounded-lg border border-red-300 bg-red-50 p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-red-700 font-semibold text-sm">
          <AlertTriangle className="w-4 h-4" />
          This may be a medical emergency
        </div>
        {pending && <PendingTag feature={6} />}
      </div>
      <p className="text-sm text-red-700/90 leading-relaxed mb-3">
        Call <strong>112</strong> immediately (or <strong>108</strong> for an ambulance). If
        you can, have someone stay with you.
      </p>
      <a
        href="tel:112"
        className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-md px-3 py-2 transition-colors"
      >
        <Phone className="w-4 h-4" />
        Call 112 now
      </a>
    </div>
  )
}

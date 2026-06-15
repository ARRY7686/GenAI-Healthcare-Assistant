import { Card, CardContent, CardHeader } from '@/components/ui/card'
import UrgencyBadge from '@/components/UrgencyBadge'
import PendingTag from '@/components/PendingTag'

/**
 * Feature #3 — Urgency Stratification (UI only; not integrated).
 * Renders a backend `Disposition` { tier, rationale, confidence, safety_net }.
 * When wired, this is fed from POST /api/triage/assess.
 */
export default function DispositionCard({ disposition, pending = false }) {
  if (!disposition) return null
  const { tier, rationale, confidence, safety_net } = disposition

  return (
    <Card>
      <CardHeader className="pb-3 flex-row items-center justify-between space-y-0">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
          Urgency Assessment
        </p>
        {pending && <PendingTag feature={3} />}
      </CardHeader>
      <CardContent className="space-y-3">
        <UrgencyBadge tier={tier} showDescription />
        {rationale && <p className="text-sm leading-relaxed">{rationale}</p>}
        {typeof confidence === 'number' && (
          <p className="text-xs text-muted-foreground">
            Model confidence: {Math.round(confidence * 100)}% (advisory only)
          </p>
        )}
        {safety_net && (
          <p className="text-xs text-muted-foreground border-l-2 border-amber-300 pl-3 leading-relaxed">
            {safety_net}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

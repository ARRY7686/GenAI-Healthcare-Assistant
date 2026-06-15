import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { ClipboardCheck, MessageSquareText, Eye } from 'lucide-react'
import PendingTag from '@/components/PendingTag'

/**
 * Feature #4 — Care Pathway Guidance (UI only; not integrated).
 * Renders a backend `CarePathway` { what_to_do, what_to_tell_clinician, red_flags_to_watch }.
 */
export default function CarePathwayPanel({ carePathway, pending = false }) {
  if (!carePathway) return null
  const { what_to_do, what_to_tell_clinician, red_flags_to_watch = [] } = carePathway

  const rows = [
    { icon: <ClipboardCheck className="w-4 h-4" />, label: 'What to do', value: what_to_do },
    { icon: <MessageSquareText className="w-4 h-4" />, label: 'What to tell the provider', value: what_to_tell_clinician },
  ]

  return (
    <Card>
      <CardHeader className="pb-3 flex-row items-center justify-between space-y-0">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
          Care Pathway Guidance
        </p>
        {pending && <PendingTag feature={4} />}
      </CardHeader>
      <CardContent className="space-y-4">
        {rows.map(
          ({ icon, label, value }) =>
            value && (
              <div key={label} className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-accent text-muted-foreground flex items-center justify-center flex-shrink-0">
                  {icon}
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-0.5">{label}</p>
                  <p className="text-sm leading-relaxed">{value}</p>
                </div>
              </div>
            )
        )}

        {red_flags_to_watch.length > 0 && (
          <>
            <Separator />
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-red-50 text-red-500 flex items-center justify-center flex-shrink-0">
                <Eye className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1.5">Red flags to watch for</p>
                <ul className="space-y-1.5">
                  {red_flags_to_watch.map((flag) => (
                    <li key={flag} className="flex items-start gap-2 text-sm">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 flex-shrink-0" />
                      {flag}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

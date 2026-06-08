import { useLocation, Link } from 'react-router-dom'
import { ChevronLeft, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import UrgencyBadge from '@/components/UrgencyBadge'

// Placeholder shape — populated from /api/summary when implemented
const EMPTY_SUMMARY = {
  urgency_tier: null,
  presenting_complaint: null,
  symptom_timeline: null,
  associated_symptoms: [],
  history: null,
  care_pathway: null,
  guidance: null,
  red_flags: [],
}

function Skeleton({ width = 'w-full', height = 'h-4' }) {
  return <div className={`${height} ${width} bg-muted rounded animate-pulse`} />
}

export default function Summary() {
  const { state } = useLocation()

  // TODO: fetch /api/summary with state?.session_id and populate `summary`
  const summary = state?.summary ?? EMPTY_SUMMARY
  const isPending = !summary.urgency_tier

  return (
    <main className="max-w-2xl mx-auto px-6 py-10">

      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Patient Summary</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Structured report for your healthcare provider
          </p>
        </div>
        <Button asChild variant="ghost" size="sm">
          <Link to="/triage">
            <ChevronLeft className="w-4 h-4" />
            Back to Chat
          </Link>
        </Button>
      </div>

      {/* Urgency Assessment */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
            Urgency Assessment
          </p>
        </CardHeader>
        <CardContent>
          {isPending ? (
            <div className="flex items-center gap-3">
              <Skeleton height="h-7" width="w-36" />
              <p className="text-xs text-muted-foreground">Complete the triage to see your result</p>
            </div>
          ) : (
            <UrgencyBadge tier={summary.urgency_tier} showDescription />
          )}
        </CardContent>
      </Card>

      {/* Clinical Details */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
            Clinical Details
          </p>
        </CardHeader>
        <CardContent className="space-y-5">
          {[
            { label: 'Presenting Complaint', value: summary.presenting_complaint },
            { label: 'Symptom Timeline', value: summary.symptom_timeline },
            { label: 'Relevant History', value: summary.history },
          ].map(({ label, value }) => (
            <div key={label}>
              <p className="text-xs font-medium text-muted-foreground mb-1.5">{label}</p>
              {value ? (
                <p className="text-sm leading-relaxed">{value}</p>
              ) : (
                <Skeleton width="w-3/4" />
              )}
            </div>
          ))}

          <Separator />

          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">Associated Symptoms</p>
            {summary.associated_symptoms.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {summary.associated_symptoms.map((s) => (
                  <span key={s} className="text-xs bg-secondary text-secondary-foreground px-2.5 py-1 rounded-full border">
                    {s}
                  </span>
                ))}
              </div>
            ) : (
              <div className="flex gap-2">
                {[80, 64, 96].map((w) => (
                  <div key={w} className="h-6 bg-muted rounded-full animate-pulse" style={{ width: w }} />
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Care Guidance */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
            Care Guidance
          </p>
        </CardHeader>
        <CardContent>
          {summary.guidance ? (
            <p className="text-sm leading-relaxed">{summary.guidance}</p>
          ) : (
            <div className="space-y-2">
              <Skeleton />
              <Skeleton width="w-5/6" />
              <Skeleton width="w-4/6" />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Red Flags */}
      <Card className="mb-8 bg-red-50 border-red-200">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-red-600 text-sm">
            <AlertTriangle className="w-4 h-4" />
            Red Flag Symptoms
          </CardTitle>
          <p className="text-xs text-red-500/80">Seek emergency care immediately if these develop</p>
        </CardHeader>
        <CardContent>
          {summary.red_flags.length > 0 ? (
            <ul className="space-y-2">
              {summary.red_flags.map((flag) => (
                <li key={flag} className="flex items-start gap-2.5 text-sm text-red-700">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 flex-shrink-0" />
                  {flag}
                </li>
              ))}
            </ul>
          ) : (
            <div className="space-y-2">
              <Skeleton height="h-4" width="w-4/5" />
              <Skeleton height="h-4" width="w-3/5" />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <p className="text-xs text-muted-foreground text-center leading-relaxed">
        This summary is AI-generated and intended as guidance only.
        Always consult a qualified healthcare professional. In an emergency, call 999.
      </p>
    </main>
  )
}

import { useState, useEffect } from 'react'
import { useLocation, Link } from 'react-router-dom'
import { ChevronLeft, AlertTriangle, Info, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { assessUrgency } from '@/lib/api'
import DispositionCard from '@/components/DispositionCard'
import CarePathwayPanel from '@/components/CarePathwayPanel'
import EmergencyBanner from '@/components/EmergencyBanner'
import PendingTag from '@/components/PendingTag'

// ── SAMPLE data — the assessment (#3) and summary (#5) backends aren't integrated yet.
//    These illustrate the finished layout; real data drops in once those features land. ──
const SAMPLE = {
  routine: {
    disposition: {
      tier: 'PHYSICIAN_URGENT',
      rationale:
        'Moderate, persistent symptoms without a named emergency pattern warrant a same-day physician review.',
      confidence: 0.7,
      safety_net:
        'If symptoms worsen or any emergency sign appears (chest pain, breathing difficulty, weakness on one side, worst-ever headache), call 112 right away.',
      care_pathway: {
        what_to_do:
          'Contact a physician for an urgent appointment today or tomorrow — a clinic, urgent care, or teleconsultation is fine.',
        what_to_tell_clinician:
          'Mention when it started, how it has changed, the severity, and any associated symptoms.',
        red_flags_to_watch: [
          'New chest pain or breathlessness',
          'Weakness or numbness on one side',
          'Worst headache of your life',
        ],
      },
    },
    summary: {
      presenting_complaint: 'Headache',
      timeline: ['Day 0 — gradual onset', 'Day 2 — persistent, moderate'],
      associated_symptoms: ['nausea'],
      history: ['No chronic conditions reported'],
      red_flags: [],
    },
  },
  emergency: {
    disposition: {
      tier: 'EMERGENCY_NOW',
      rationale:
        'A named emergency red-flag pattern is present (cardiac chest pain), so urgency was raised to emergency.',
      confidence: 0.95,
      safety_net: 'If symptoms worsen while waiting for help, call 112 again.',
      care_pathway: {
        what_to_do: 'Call 112 immediately (or 108 for an ambulance). If you can, have someone stay with you.',
        what_to_tell_clinician: 'Report chest pain radiating to the arm with sweating, and when it began.',
        red_flags_to_watch: ['Loss of consciousness', 'Severe breathlessness'],
      },
    },
    summary: {
      presenting_complaint: 'Chest pain radiating to the left arm with sweating',
      timeline: ['~30 minutes ago — sudden onset'],
      associated_symptoms: ['sweating', 'arm pain'],
      history: ['Hypertension'],
      red_flags: ['cardiac_chest_pain'],
    },
  },
}

export default function Summary() {
  const { state } = useLocation()
  const sessionId = state?.session_id
  const [scenario, setScenario] = useState('routine')

  const [disposition, setDisposition] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (sessionId) {
      setLoading(true)
      setError(null)
      assessUrgency(sessionId)
        .then((data) => {
          setDisposition({
            tier: data.tier_code,
            rationale: data.rationale,
            safety_net: data.safety_net,
            care_pathway: data.care_pathway,
            fail_closed: data.fail_closed,
          })
        })
        .catch((err) => {
          setError(err?.response?.data?.detail || err?.message || 'Failed to fetch assessment')
        })
        .finally(() => {
          setLoading(false)
        })
    }
  }, [sessionId])

  if (loading) {
    return (
      <main className="max-w-2xl mx-auto px-6 py-20 flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        <p className="text-sm text-muted-foreground font-medium">Fetching clinical assessment...</p>
      </main>
    )
  }

  const displayDisposition = disposition || SAMPLE[scenario].disposition
  const displaySummary = SAMPLE[scenario].summary
  const isEmergency = displayDisposition.tier === 'EMERGENCY_NOW'

  return (
    <main className="max-w-2xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Assessment &amp; Summary</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Structured report for your healthcare provider
            {sessionId && (
              <span className="text-muted-foreground/70"> · session {sessionId.slice(0, 8)}</span>
            )}
          </p>
        </div>
        <Button asChild variant="ghost" size="sm">
          <Link to="/triage">
            <ChevronLeft className="w-4 h-4" />
            Back to Chat
          </Link>
        </Button>
      </div>

      {error && (
        <div className="flex items-start gap-2 text-sm bg-red-50 border border-red-200 text-red-700 rounded-lg px-3 py-2 mb-6">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <span className="font-semibold">Error.</span> {error}
          </div>
        </div>
      )}

      {/* Preview notice — these surfaces aren't wired to the backend yet */}
      {!sessionId && (
        <div className="flex items-start gap-2 text-sm bg-amber-50 border border-amber-200 text-amber-800 rounded-lg px-3 py-2 mb-6">
          <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <span className="font-medium">Preview.</span> Urgency assessment (feature #3) and the
            patient summary (feature #5) aren&apos;t integrated yet — this shows the finished layout
            with sample data. The symptom check itself (features #1–2) is live.
          </div>
        </div>
      )}

      {/* Scenario toggle so all states are visible while unwired */}
      {!sessionId && (
        <div className="flex items-center gap-2 mb-6">
          <span className="text-xs text-muted-foreground">Sample scenario:</span>
          {[
            { key: 'routine', label: 'Routine' },
            { key: 'emergency', label: 'Emergency' },
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setScenario(key)}
              className={cn(
                'text-xs px-3 py-1 rounded-full border transition-colors',
                scenario === key
                  ? 'bg-foreground text-background border-foreground'
                  : 'text-muted-foreground hover:bg-accent'
              )}
            >
              {label}
            </button>
          ))}
          <PendingTag />
        </div>
      )}

      <div className="space-y-4">
        {/* Feature #6 — safety banner (emergency routing) */}
        {isEmergency && <EmergencyBanner pending />}

        {/* Feature #3 — urgency stratification */}
        <DispositionCard disposition={displayDisposition} pending={false} />

        {/* Feature #4 — care pathway guidance */}
        <CarePathwayPanel carePathway={displayDisposition.care_pathway} pending={false} />

        {/* Feature #5 — clinician summary */}
        <Card>
          <CardHeader className="pb-3 flex-row items-center justify-between space-y-0">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
              Clinical Summary
            </p>
            <PendingTag feature={5} />
          </CardHeader>
          <CardContent className="space-y-5">
            {[
              { label: 'Presenting Complaint', value: summary.presenting_complaint },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-xs font-medium text-muted-foreground mb-1.5">{label}</p>
                <p className="text-sm leading-relaxed">{value}</p>
              </div>
            ))}

            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1.5">Symptom Timeline</p>
              <ul className="space-y-1">
                {summary.timeline.map((t) => (
                  <li key={t} className="text-sm leading-relaxed flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/40 mt-1.5 flex-shrink-0" />
                    {t}
                  </li>
                ))}
              </ul>
            </div>

            <Separator />

            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">Associated Symptoms</p>
              <div className="flex flex-wrap gap-2">
                {summary.associated_symptoms.map((s) => (
                  <span
                    key={s}
                    className="text-xs bg-secondary text-secondary-foreground px-2.5 py-1 rounded-full border"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1.5">Relevant History</p>
              <p className="text-sm leading-relaxed">{summary.history.join('; ')}</p>
            </div>

            <p className="text-[11px] text-muted-foreground border-t pt-3">
              AI-generated triage — not a diagnosis. Clinician must verify.
            </p>
          </CardContent>
        </Card>

        {/* Red flags */}
        <Card className="bg-red-50 border-red-200">
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
              <p className="text-sm text-red-700/70">None recorded for this case.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Disclaimer */}
      <p className="text-xs text-muted-foreground text-center leading-relaxed mt-8">
        This summary is AI-generated and intended as guidance only. Always consult a qualified
        healthcare professional. In an emergency, call 112.
      </p>
    </main>
  )
}

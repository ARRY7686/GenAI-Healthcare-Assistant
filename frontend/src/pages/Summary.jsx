import { useState, useEffect } from 'react'
import { useLocation, Link } from 'react-router-dom'
import { ChevronLeft, AlertTriangle, Info, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { assessUrgency, getSummary } from '@/lib/api'
import DispositionCard from '@/components/DispositionCard'
import CarePathwayPanel from '@/components/CarePathwayPanel'
import EmergencyBanner from '@/components/EmergencyBanner'
import PendingTag from '@/components/PendingTag'

// ── SAMPLE data — shown only in PREVIEW mode (opened without a live session) so every
//    state is visible. With a real session, the live backend (#3 + #5) drives the page. ──
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
      timeline: ['headache, onset gradual, for 2 days, severity moderate'],
      associated_symptoms: ['headache', 'nausea'],
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
      timeline: ['chest pain, onset sudden, severity severe'],
      associated_symptoms: ['chest pain', 'sweating'],
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
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!sessionId) return
    let cancelled = false
    setLoading(true)
    setError(null)
    // Assess first (feature #3) so the disposition is stored, then build the summary (#5).
    assessUrgency(sessionId)
      .then((assess) => {
        if (cancelled) return
        setDisposition({
          tier: assess.tier_code,
          rationale: assess.rationale,
          confidence: assess.confidence,
          safety_net: assess.safety_net,
          care_pathway: assess.care_pathway,
          fail_closed: assess.fail_closed,
        })
        return getSummary(sessionId)
      })
      .then((data) => {
        if (cancelled || !data) return
        setSummary(data)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err?.response?.data?.detail || err?.message || 'Failed to load the assessment')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [sessionId])

  if (sessionId && loading) {
    return (
      <main className="max-w-2xl mx-auto px-6 py-20 flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        <p className="text-sm text-muted-foreground font-medium">Building your clinical summary…</p>
      </main>
    )
  }

  // Live data when we have a session; sample data only in preview mode.
  const displayDisposition = sessionId ? disposition : SAMPLE[scenario].disposition
  const displaySummary = sessionId ? summary : SAMPLE[scenario].summary
  const isEmergency = displayDisposition?.tier === 'EMERGENCY_NOW'

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

      {/* Preview notice — opened without a live triage session */}
      {!sessionId && (
        <div className="flex items-start gap-2 text-sm bg-amber-50 border border-amber-200 text-amber-800 rounded-lg px-3 py-2 mb-6">
          <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <span className="font-medium">Preview.</span> This shows the finished layout with sample
            data. Start a symptom check and open the summary from there to see your real assessment.
          </div>
        </div>
      )}

      {/* Scenario toggle so all states are visible while in preview */}
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

      {displayDisposition && displaySummary && (
        <div className="space-y-4">
          {/* Feature #6 — deterministic safety override routed this case to emergency */}
          {isEmergency && <EmergencyBanner />}

          {/* Feature #3 — urgency stratification */}
          <DispositionCard disposition={displayDisposition} />

          {/* Feature #4 — care pathway guidance */}
          <CarePathwayPanel carePathway={displayDisposition.care_pathway} />

          {/* Feature #5 — clinician summary */}
          <Card>
            <CardHeader className="pb-3">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">
                Clinical Summary
              </p>
            </CardHeader>
            <CardContent className="space-y-5">
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1.5">Presenting Complaint</p>
                <p className="text-sm leading-relaxed">{displaySummary.presenting_complaint || '—'}</p>
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1.5">Symptom Timeline</p>
                {displaySummary.timeline.length > 0 ? (
                  <ul className="space-y-1">
                    {displaySummary.timeline.map((t) => (
                      <li key={t} className="text-sm leading-relaxed flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/40 mt-1.5 flex-shrink-0" />
                        {t}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">No symptoms recorded.</p>
                )}
              </div>

              <Separator />

              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">Associated Symptoms</p>
                {displaySummary.associated_symptoms.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {displaySummary.associated_symptoms.map((s) => (
                      <span
                        key={s}
                        className="text-xs bg-secondary text-secondary-foreground px-2.5 py-1 rounded-full border"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">None recorded.</p>
                )}
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1.5">Relevant History</p>
                <p className="text-sm leading-relaxed">
                  {displaySummary.history.length > 0 ? displaySummary.history.join('; ') : '—'}
                </p>
              </div>

              <p className="text-[11px] text-muted-foreground border-t pt-3">
                {displaySummary.provenance ||
                  'AI-generated triage — not a diagnosis. Clinician must verify.'}
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
              {displaySummary.red_flags.length > 0 ? (
                <ul className="space-y-2">
                  {displaySummary.red_flags.map((flag) => (
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
      )}

      {/* Disclaimer */}
      <p className="text-xs text-muted-foreground text-center leading-relaxed mt-8">
        This summary is AI-generated and intended as guidance only. Always consult a qualified
        healthcare professional. In an emergency, call 112.
      </p>
    </main>
  )
}

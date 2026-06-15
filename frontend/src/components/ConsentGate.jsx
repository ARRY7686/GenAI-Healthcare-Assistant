import { useState } from 'react'
import { ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

const AGE_BANDS = [
  { value: 'under_16', label: 'Under 16' },
  { value: '16-39', label: '16–39' },
  { value: '40-64', label: '40–64' },
  { value: '65+', label: '65+' },
]

const SEXES = [
  { value: 'female', label: 'Female' },
  { value: 'male', label: 'Male' },
  { value: 'other', label: 'Other' },
  { value: 'unknown', label: 'Prefer not to say' },
]

function Pills({ options, value, onChange, ariaLabel }) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label={ariaLabel}>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          aria-pressed={value === o.value}
          onClick={() => onChange(o.value)}
          className={cn(
            'text-sm px-3 py-1.5 rounded-full border transition-colors',
            value === o.value
              ? 'bg-foreground text-background border-foreground'
              : 'text-muted-foreground hover:bg-accent'
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

/**
 * Consent gate — blocks the chat until the user accepts the disclaimer and provides basic
 * demographics. Out-of-scope cases (under-16 / pregnant) are refused up front by the caller.
 * Server-side enforcement + audit are feature #6.
 */
export default function ConsentGate({ onAccept }) {
  const [ageBand, setAgeBand] = useState('')
  const [sex, setSex] = useState('')
  const [pregnant, setPregnant] = useState(false)
  const [accepted, setAccepted] = useState(false)

  const showPregnancy = sex === 'female' || sex === 'other'
  const canContinue = ageBand && sex && accepted

  const submit = () => {
    if (!canContinue) return
    onAccept({
      age_band: ageBand,
      sex,
      pregnancy_flag: showPregnancy ? pregnant : false,
    })
  }

  return (
    <main className="max-w-lg mx-auto px-6 py-10">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldCheck className="w-5 h-5 text-primary" />
            Before we begin
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="text-sm text-muted-foreground leading-relaxed bg-accent/40 border rounded-lg p-3 space-y-2">
            <p>
              This assistant offers <strong>triage guidance, not a diagnosis</strong>, and is not a
              substitute for a clinician. It is validated for <strong>adults 16 and older</strong>.
            </p>
            <p>
              In an emergency, call <strong>112</strong> (or <strong>108</strong> for an ambulance) now.
            </p>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium">Age</p>
            <Pills options={AGE_BANDS} value={ageBand} onChange={setAgeBand} ariaLabel="Age band" />
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium">Sex</p>
            <Pills options={SEXES} value={sex} onChange={setSex} ariaLabel="Sex" />
          </div>

          {showPregnancy && (
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={pregnant}
                onChange={(e) => setPregnant(e.target.checked)}
                className="h-4 w-4 rounded border-input"
              />
              I am currently pregnant
            </label>
          )}

          <label className="flex items-start gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={accepted}
              onChange={(e) => setAccepted(e.target.checked)}
              className="h-4 w-4 rounded border-input mt-0.5"
            />
            <span>I understand this is triage guidance, not a diagnosis, and I agree to continue.</span>
          </label>

          <Button onClick={submit} disabled={!canContinue} className="w-full">
            Accept &amp; start symptom check
          </Button>
        </CardContent>
      </Card>
    </main>
  )
}

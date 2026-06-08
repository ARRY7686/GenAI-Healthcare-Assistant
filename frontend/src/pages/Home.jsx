import { Link } from 'react-router-dom'
import { ArrowRight, MessageCircle, Brain, ShieldCheck, ClipboardList, Activity, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

const CARE_TIERS = [
  { label: 'Emergency',  color: 'bg-red-400',    text: 'Call 999 now' },
  { label: 'A&E Today',  color: 'bg-orange-400',  text: 'Go immediately' },
  { label: 'GP Urgent',  color: 'bg-amber-400',   text: 'See GP today' },
  { label: 'GP Routine', color: 'bg-sky-400',     text: 'Book appointment' },
  { label: 'Self-Care',  color: 'bg-emerald-400', text: 'Manage at home' },
]

const FEATURES = [
  {
    icon: <MessageCircle className="w-5 h-5" />,
    title: 'Conversational Intake',
    description: 'Natural symptom collection through adaptive dialogue — no forms, just a conversation.',
  },
  {
    icon: <Brain className="w-5 h-5" />,
    title: 'Adaptive Questioning',
    description: 'Clinical logic selects the most diagnostically efficient follow-up questions.',
  },
  {
    icon: <ShieldCheck className="w-5 h-5" />,
    title: 'Safety Guardrails',
    description: 'Hard-coded emergency overrides for critical symptom combinations — always safe.',
  },
  {
    icon: <ClipboardList className="w-5 h-5" />,
    title: 'Provider Summary',
    description: 'Structured patient report with complaint, timeline, and urgency for the clinician.',
  },
]

export default function Home() {
  return (
    <main className="max-w-4xl mx-auto px-6 py-16 sm:py-24">

      {/* Hero */}
      <div className="text-center mb-20">
        <div className="inline-flex items-center gap-1.5 bg-primary/10 text-primary text-xs font-medium px-3 py-1.5 rounded-full border border-primary/20 mb-6">
          <Activity className="w-3.5 h-3.5" />
          AI-Powered Healthcare Triage
        </div>

        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight leading-[1.15] mb-5">
          Get to the right care,{' '}
          <span className="text-primary">faster.</span>
        </h1>

        <p className="text-lg text-muted-foreground max-w-lg mx-auto leading-relaxed mb-8">
          Describe your symptoms and get directed to the appropriate level of care —
          before you reach the waiting room.
        </p>

        <div className="flex items-center justify-center gap-3 flex-wrap">
          <Button asChild size="lg">
            <Link to="/triage">
              Start Symptom Check
              <ArrowRight className="w-4 h-4" />
            </Link>
          </Button>
          <Button asChild variant="ghost" size="lg">
            <Link to="/summary">View Sample Summary</Link>
          </Button>
        </div>
      </div>

      {/* Care pathway strip */}
      <div className="mb-20">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest text-center mb-6">
          Five Care Pathways
        </p>
        <div className="flex items-start justify-between gap-1">
          {CARE_TIERS.map(({ label, color, text }, i) => (
            <div key={label} className="flex items-center gap-1 flex-1">
              <div className="flex-1 text-center">
                <div className={`${color} rounded-full h-1 mb-3 opacity-70`} />
                <p className="text-xs font-semibold">{label}</p>
                <p className="text-xs text-muted-foreground mt-0.5 hidden sm:block">{text}</p>
              </div>
              {i < CARE_TIERS.length - 1 && (
                <ChevronRight className="w-3 h-3 text-muted-foreground/40 flex-shrink-0 mt-[-0.5rem]" />
              )}
            </div>
          ))}
        </div>
      </div>

      <Separator className="mb-16" />

      {/* Features */}
      <div className="grid sm:grid-cols-2 gap-4 mb-16">
        {FEATURES.map(({ icon, title, description }) => (
          <Card key={title}>
            <CardContent className="pt-6 flex gap-4">
              <div className="w-9 h-9 rounded-lg bg-accent text-muted-foreground flex items-center justify-center flex-shrink-0">
                {icon}
              </div>
              <div>
                <h3 className="text-sm font-semibold mb-1">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>


      {/* Disclaimer */}
      <Card className="bg-amber-50 border-amber-200">
        <CardContent className="pt-4 pb-4">
          <p className="text-xs text-amber-800 text-center leading-relaxed">
            <strong>Not a substitute for professional medical advice.</strong>{' '}
            This tool provides guidance only. Always consult a qualified healthcare
            professional for medical decisions. In an emergency, call 999 immediately.
          </p>
        </CardContent>
      </Card>
    </main>
  )
}

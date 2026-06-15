import { cn } from '@/lib/utils'

// Tier codes mirror the backend (app/domain/tiers.py) — India-localized (112 / 108).
const URGENCY_CONFIG = {
  EMERGENCY_NOW: {
    label: 'Emergency',
    subtext: 'Call 112 / 108 now',
    className: 'bg-red-50 text-red-700 border-red-200',
    dotClass: 'bg-red-500 animate-pulse',
  },
  CASUALTY_TODAY: {
    label: 'Casualty Today',
    subtext: 'Go to casualty / emergency department today',
    className: 'bg-orange-50 text-orange-700 border-orange-200',
    dotClass: 'bg-orange-500',
  },
  PHYSICIAN_URGENT: {
    label: 'Physician Urgent',
    subtext: 'See a physician urgently (today/tomorrow)',
    className: 'bg-amber-50 text-amber-700 border-amber-200',
    dotClass: 'bg-amber-500',
  },
  PHYSICIAN_ROUTINE: {
    label: 'Physician Routine',
    subtext: 'Book a routine physician visit',
    className: 'bg-sky-50 text-sky-700 border-sky-200',
    dotClass: 'bg-sky-500',
  },
  SELF_CARE: {
    label: 'Self-Care',
    subtext: 'Self-care with monitoring',
    className: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    dotClass: 'bg-emerald-500',
  },
}

export default function UrgencyBadge({ tier, showDescription = false }) {
  const config = URGENCY_CONFIG[tier] ?? {
    label: 'Pending',
    subtext: 'Assessment in progress',
    className: 'bg-muted text-muted-foreground border-border',
    dotClass: 'bg-muted-foreground/40',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-medium',
        config.className
      )}
    >
      <span className={cn('w-2 h-2 rounded-full flex-shrink-0', config.dotClass)} />
      {config.label}
      {showDescription && (
        <span className="text-xs opacity-70 font-normal">— {config.subtext}</span>
      )}
    </span>
  )
}

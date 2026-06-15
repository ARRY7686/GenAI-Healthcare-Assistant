import { Plus } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function ChatBubble({ role, content, timestamp, rationale }) {
  const isUser = role === 'user'

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      {/* AI avatar */}
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Plus className="w-3.5 h-3.5 text-primary" strokeWidth={3} />
        </div>
      )}

      <div className={cn('max-w-[75%] flex flex-col gap-1', isUser ? 'items-end' : 'items-start')}>
        <div
          className={cn(
            'rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
            isUser
              ? 'bg-foreground text-background rounded-br-sm'
              : 'bg-card border shadow-sm rounded-bl-sm text-foreground'
          )}
        >
          {content}
        </div>

        {/* Feature #2 — every adaptive question carries its clinical rationale */}
        {rationale && !isUser && (
          <div className="text-xs text-muted-foreground bg-accent/40 border rounded-lg px-3 py-1.5 max-w-full">
            <span className="font-medium text-foreground/70">Why I&apos;m asking: </span>
            {rationale}
          </div>
        )}

        {timestamp && (
          <p className="text-xs text-muted-foreground">{timestamp}</p>
        )}
      </div>
    </div>
  )
}

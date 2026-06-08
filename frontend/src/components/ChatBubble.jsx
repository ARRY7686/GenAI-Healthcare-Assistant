import { Plus } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function ChatBubble({ role, content, timestamp }) {
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

        {timestamp && (
          <p className="text-xs text-muted-foreground">{timestamp}</p>
        )}
      </div>
    </div>
  )
}

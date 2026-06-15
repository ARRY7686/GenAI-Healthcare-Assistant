import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Send, RotateCcw, FileText, CheckCircle2, AlertTriangle, Loader2, Phone } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'
import ChatBubble from '@/components/ChatBubble'
import ConsentGate from '@/components/ConsentGate'
import { startTriage, respond, detail } from '@/lib/api'

const now = () =>
  new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

let _seq = 0
const nextId = () => ++_seq

const REFUSALS = {
  minor:
    'This assistant is for adults 16 and older. Please ask a parent or guardian to contact a physician or a paediatric service.',
  pregnancy:
    "I'm not able to safely triage symptoms during pregnancy here. Please contact an obstetrician / maternity service.",
}

export default function Triage() {
  const [phase, setPhase] = useState('consent') // 'consent' | 'chat' | 'refused'
  const [refusalReason, setRefusalReason] = useState(null)
  const [demographics, setDemographics] = useState(null)

  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [isComplete, setIsComplete] = useState(false)
  const [booting, setBooting] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Consent gate → up-front scope refusal, else open the session (feature #1).
  const onConsent = (d) => {
    if (d.age_band === 'under_16') return refuse('minor')
    if (d.pregnancy_flag === true) return refuse('pregnancy')
    setDemographics(d)
    setPhase('chat')
    boot(d)
  }

  const refuse = (reason) => {
    setRefusalReason(reason)
    setPhase('refused')
  }

  const boot = async (d) => {
    setBooting(true)
    setError('')
    setMessages([])
    setIsComplete(false)
    setProgress(0)
    setInput('')
    try {
      const data = await startTriage(d)
      setSessionId(data.session_id)
      setProgress(data.progress ?? 0)
      setMessages([
        { id: nextId(), role: 'assistant', content: data.question, timestamp: now() },
      ])
    } catch (e) {
      setSessionId(null)
      setError(detail(e))
    } finally {
      setBooting(false)
    }
  }

  // Back to the consent gate (a fresh triage re-consents).
  const restart = () => {
    setPhase('consent')
    setRefusalReason(null)
    setDemographics(null)
    setSessionId(null)
    setMessages([])
    setIsComplete(false)
    setProgress(0)
    setInput('')
    setError('')
  }

  // Feature #2 — send the answer, render the next adaptive question (+ rationale).
  const handleSend = async () => {
    const text = input.trim()
    if (!text || isLoading || isComplete || !sessionId) return
    setError('')

    const userMsg = { id: nextId(), role: 'user', content: text, timestamp: now() }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    try {
      const data = await respond(sessionId, text)
      setProgress(data.progress ?? progress)
      if (data.is_complete) {
        setIsComplete(true)
        setMessages((prev) => [
          ...prev,
          {
            id: nextId(),
            role: 'assistant',
            content: data.fail_closed
              ? "Thanks. I couldn't fully finish the questions, but I have enough to move you safely to an assessment."
              : "Thanks — I have what I need. Let's look at your assessment.",
            timestamp: now(),
          },
        ])
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: nextId(),
            role: 'assistant',
            content: data.question,
            rationale: data.rationale,
            timestamp: now(),
          },
        ])
      }
    } catch (e) {
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id))
      setInput(text)
      setError(detail(e))
    } finally {
      setIsLoading(false)
      textareaRef.current?.focus()
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      handleSend()
    }
  }

  // ── Consent gate ──────────────────────────────────────────────────────────────
  if (phase === 'consent') {
    return <ConsentGate onAccept={onConsent} />
  }

  // ── Out-of-scope refusal (feature #6 surface, client-side for now) ──────────────
  if (phase === 'refused') {
    return (
      <main className="max-w-lg mx-auto px-6 py-10">
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="pt-6 space-y-4">
            <div className="flex items-center gap-2 text-amber-800 font-semibold">
              <AlertTriangle className="w-5 h-5" />
              We can&apos;t continue here
            </div>
            <p className="text-sm text-amber-800/90 leading-relaxed">{REFUSALS[refusalReason]}</p>
            <a
              href="tel:112"
              className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-md px-3 py-2 transition-colors"
            >
              <Phone className="w-4 h-4" />
              Emergency? Call 112 now
            </a>
            <div>
              <Button variant="ghost" size="sm" onClick={restart}>
                <RotateCcw className="w-3.5 h-3.5" />
                Start over
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    )
  }

  // ── Chat (features #1 + #2) ─────────────────────────────────────────────────────
  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 3.5rem)' }}>
      {/* Header */}
      <div className="border-b bg-card/80 backdrop-blur-sm px-6 py-3 flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-sm font-semibold">Symptom Check</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Answer a few questions to get care guidance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm">
            <Link to="/summary" state={{ session_id: sessionId }}>
              <FileText className="w-3.5 h-3.5" />
              View Summary
            </Link>
          </Button>
          <Button variant="ghost" size="sm" onClick={restart} className="text-muted-foreground">
            <RotateCcw className="w-3.5 h-3.5" />
            Reset
          </Button>
        </div>
      </div>

      {/* Progress (feature #2) */}
      <div className="h-1 bg-muted flex-shrink-0">
        <div
          className="h-1 bg-primary transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-hide">
        <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
          {error && (
            <div
              role="alert"
              className="flex items-start gap-2 text-sm bg-red-50 border border-red-200 text-red-700 rounded-lg px-3 py-2"
            >
              <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                {error}
                {!sessionId && (
                  <span className="block text-xs text-red-500/80 mt-1">
                    Make sure the backend is running:{' '}
                    <code>uvicorn app.main:app --port 8000</code>
                  </span>
                )}
              </div>
              <button className="text-red-400 hover:text-red-600" aria-label="Dismiss" onClick={() => setError('')}>
                ×
              </button>
            </div>
          )}

          {booting && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              Starting your symptom check…
            </div>
          )}

          {!booting && !sessionId && error && (
            <Button onClick={() => boot(demographics)} variant="outline" size="sm">
              <RotateCcw className="w-3.5 h-3.5" />
              Retry
            </Button>
          )}

          {messages.map((msg) => (
            <ChatBubble
              key={msg.id}
              role={msg.role}
              content={msg.content}
              rationale={msg.rationale}
              timestamp={msg.timestamp}
            />
          ))}

          {/* Typing indicator */}
          {isLoading && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center flex-shrink-0">
                <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              </div>
              <div className="bg-card border rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                <div className="flex gap-1 items-center h-4">
                  <span className="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full animate-bounce [animation-delay:-0.3s]" />
                  <span className="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full animate-bounce [animation-delay:-0.15s]" />
                  <span className="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full animate-bounce" />
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Footer — composer while collecting, completion panel once done */}
      <div className="flex-shrink-0 border-t bg-card/80 backdrop-blur-sm">
        <div className="max-w-2xl mx-auto px-4 py-3">
          {isComplete ? (
            <div className="flex flex-col sm:flex-row sm:items-center gap-3 py-1">
              <div className="flex items-center gap-2 text-sm font-medium text-emerald-700 flex-1">
                <CheckCircle2 className="w-4 h-4" />
                Symptom check complete
              </div>
              <div className="flex gap-2">
                <Button asChild size="sm">
                  <Link to="/summary" state={{ session_id: sessionId }}>
                    <FileText className="w-3.5 h-3.5" />
                    View assessment &amp; summary
                  </Link>
                </Button>
                <Button variant="ghost" size="sm" onClick={restart}>
                  <RotateCcw className="w-3.5 h-3.5" />
                  Start new check
                </Button>
              </div>
            </div>
          ) : (
            <>
              <div className="flex gap-2 items-end">
                <Textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Describe your symptoms…"
                  rows={1}
                  disabled={booting || !sessionId || isLoading}
                  className="flex-1 resize-none min-h-[40px] max-h-[120px] overflow-y-auto py-2.5 text-sm"
                />
                <Button
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading || booting || !sessionId}
                  size="icon"
                  className="flex-shrink-0 h-10 w-10"
                  aria-label="Send"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground text-center mt-2">
                Enter to send · Shift+Enter for new line · Triage guidance, not a diagnosis
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

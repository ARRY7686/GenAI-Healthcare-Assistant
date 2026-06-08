import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Send, RotateCcw, FileText } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import ChatBubble from '@/components/ChatBubble'

const now = () =>
  new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

const INITIAL_MESSAGES = [
  {
    id: 1,
    role: 'assistant',
    content:
      "Hello, I'm your triage assistant. I'll ask you a few questions to help guide you to the right level of care. What is your main symptom or concern today?",
    timestamp: now(),
  },
]

export default function Triage() {
  const [messages, setMessages] = useState(INITIAL_MESSAGES)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = async () => {
    const text = input.trim()
    if (!text || isLoading) return

    const userMsg = { id: Date.now(), role: 'user', content: text, timestamp: now() }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    // TODO: Replace with real API call
    // const { data } = await axios.post('/api/triage/respond', {
    //   session_id: sessionId,
    //   message: text,
    // })
    // setMessages((prev) => [...prev, { id: Date.now(), role: 'assistant', content: data.question, timestamp: now() }])
    // if (data.is_complete) navigate('/summary', { state: { session_id: data.session_id } })

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: '[ Connect the Flask /api/triage/respond endpoint here to continue the adaptive questioning. ]',
          timestamp: now(),
        },
      ])
      setIsLoading(false)
      textareaRef.current?.focus()
    }, 700)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleReset = () => {
    setMessages(INITIAL_MESSAGES)
    setInput('')
  }

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 3.5rem)' }}>

      {/* Header */}
      <div className="border-b bg-card/80 backdrop-blur-sm px-6 py-3 flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-sm font-semibold">Symptom Check</h1>
          <p className="text-xs text-muted-foreground mt-0.5">Answer a few questions to get care guidance</p>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm">
            <Link to="/summary">
              <FileText className="w-3.5 h-3.5" />
              View Summary
            </Link>
          </Button>
          <Button variant="ghost" size="sm" onClick={handleReset} className="text-muted-foreground">
            <RotateCcw className="w-3.5 h-3.5" />
            Reset
          </Button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-hide">
        <div className="max-w-2xl mx-auto px-4 py-6 space-y-4">
          {messages.map((msg) => (
            <ChatBubble
              key={msg.id}
              role={msg.role}
              content={msg.content}
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

      {/* Input */}
      <div className="flex-shrink-0 border-t bg-card/80 backdrop-blur-sm">
        <div className="max-w-2xl mx-auto px-4 py-3">
          <div className="flex gap-2 items-end">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe your symptoms…"
              rows={1}
              className="flex-1 resize-none min-h-[40px] max-h-[120px] overflow-y-auto py-2.5 text-sm"
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              size="icon"
              className="flex-shrink-0 h-10 w-10"
              aria-label="Send"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <p className="text-xs text-muted-foreground text-center mt-2">
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  )
}

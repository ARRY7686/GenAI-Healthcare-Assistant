import { Link, useLocation } from 'react-router-dom'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const NAV_LINKS = [
  { label: 'Home', path: '/' },
  { label: 'Check Symptoms', path: '/triage' },
]

export default function Navbar() {
  const { pathname } = useLocation()

  return (
    <nav className="sticky top-0 z-50 bg-card/80 backdrop-blur-md border-b">
      <div className="max-w-4xl mx-auto px-6 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-7 h-7 bg-primary rounded-lg flex items-center justify-center shadow-sm group-hover:bg-primary/90 transition-colors">
            <Plus className="w-4 h-4 text-primary-foreground" strokeWidth={3} />
          </div>
          <span className="font-semibold tracking-tight">TriageAI</span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {NAV_LINKS.map(({ label, path }) => (
            <Link key={path} to={path}>
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  'text-muted-foreground font-medium',
                  pathname === path && 'bg-accent text-foreground'
                )}
              >
                {label}
              </Button>
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}

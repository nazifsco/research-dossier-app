import Link from 'next/link'
import { Scroll } from '@phosphor-icons/react/dist/ssr'

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen flex flex-col gradient-mesh noise-bg">
      {/* Navigation */}
      <nav className="border-b border-border/50 bg-background/50 backdrop-blur-xl">
        <div className="container mx-auto px-6 h-16 flex items-center">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center shadow-lg shadow-primary/20">
              <Scroll className="h-5 w-5 text-primary-foreground" weight="duotone" />
            </div>
            <span className="font-semibold text-lg tracking-tight">ResearchDossier</span>
          </Link>
        </div>
      </nav>

      {/* Main content */}
      <main className="flex-1 flex items-center justify-center p-6 relative">
        {/* Decorative elements */}
        <div className="absolute top-1/4 left-0 w-72 h-72 bg-primary/10 rounded-full blur-3xl -translate-x-1/2" />
        <div className="absolute bottom-1/4 right-0 w-96 h-96 bg-accent/10 rounded-full blur-3xl translate-x-1/2" />

        {/* Content */}
        <div className="relative z-10 w-full max-w-md">
          {children}
        </div>
      </main>
    </div>
  )
}

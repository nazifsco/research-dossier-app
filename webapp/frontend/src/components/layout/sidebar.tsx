"use client"

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  Scroll,
  SquaresFour,
  MagnifyingGlass,
  CreditCard,
  Gear,
  SignOut,
  Plus
} from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/use-auth'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: SquaresFour },
  { href: '/research/new', label: 'New Research', icon: Plus },
  { href: '/credits', label: 'Buy Credits', icon: CreditCard },
  { href: '/settings', label: 'Settings', icon: Gear },
]

export function Sidebar() {
  const pathname = usePathname()
  const { logout } = useAuth()

  return (
    <aside className="w-64 border-r border-border/50 bg-card/50 backdrop-blur-sm h-screen sticky top-0 flex flex-col">
      {/* Logo */}
      <div className="p-5 border-b border-border/50">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center shadow-lg shadow-primary/20">
            <Scroll className="h-5 w-5 text-primary-foreground" weight="duotone" />
          </div>
          <span className="font-semibold text-lg tracking-tight">ResearchDossier</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href ||
              (item.href !== '/dashboard' && pathname.startsWith(item.href))
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                      : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                  )}
                >
                  <item.icon className="h-5 w-5" weight={isActive ? "fill" : "duotone"} />
                  {item.label}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-border/50">
        <Button
          variant="ghost"
          className="w-full justify-start text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-xl px-4 py-2.5 h-auto"
          onClick={() => logout()}
        >
          <SignOut className="h-5 w-5 mr-3" weight="duotone" />
          Log out
        </Button>
      </div>
    </aside>
  )
}

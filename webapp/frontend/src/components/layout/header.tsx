"use client"

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { CreditCard } from 'lucide-react'

export function Header() {
  const [credits, setCredits] = useState<number | null>(null)

  useEffect(() => {
    api.getCredits().then(data => {
      setCredits(data.credits)
    }).catch(() => {
      setCredits(0)
    })
  }, [])

  return (
    <header className="h-16 border-b px-6 flex items-center justify-between bg-card">
      <div>
        <h2 className="text-lg font-semibold">Welcome back</h2>
      </div>
      <div className="flex items-center gap-4">
        <Link href="/credits">
          <Button variant="outline" size="sm" className="gap-2">
            <CreditCard className="h-4 w-4" />
            {credits !== null ? `${credits} credits` : '...'}
          </Button>
        </Link>
      </div>
    </header>
  )
}

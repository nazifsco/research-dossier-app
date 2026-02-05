"use client"

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle, Loader2, ArrowRight, XCircle } from 'lucide-react'
import { api } from '@/lib/api'

export default function PaymentSuccessPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const sessionId = searchParams.get('session_id')

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [credits, setCredits] = useState<number>(0)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) {
      setStatus('error')
      setError('No session ID provided')
      return
    }

    // Poll for credit update (webhook might take a moment)
    let attempts = 0
    const maxAttempts = 10

    const checkCredits = async () => {
      try {
        const data = await api.getCredits()
        setCredits(data.credits || 0)
        setStatus('success')
      } catch (err) {
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(checkCredits, 1000)
        } else {
          setStatus('error')
          setError('Could not verify payment. Please check your credits balance.')
        }
      }
    }

    // Small delay to let webhook process
    setTimeout(checkCredits, 1500)
  }, [sessionId])

  if (status === 'loading') {
    return (
      <div className="max-w-md mx-auto mt-20">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
              <h2 className="text-xl font-semibold">Processing Payment...</h2>
              <p className="text-muted-foreground">
                Please wait while we confirm your payment.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="max-w-md mx-auto mt-20">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <XCircle className="h-12 w-12 mx-auto text-destructive" />
              <h2 className="text-xl font-semibold">Something Went Wrong</h2>
              <p className="text-muted-foreground">{error}</p>
              <div className="flex gap-2 justify-center pt-4">
                <Button variant="outline" asChild>
                  <Link href="/credits">Back to Credits</Link>
                </Button>
                <Button asChild>
                  <Link href="/dashboard">Go to Dashboard</Link>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-md mx-auto mt-20">
      <Card>
        <CardHeader className="text-center">
          <div className="mx-auto mb-4">
            <CheckCircle className="h-16 w-16 text-green-500" />
          </div>
          <CardTitle className="text-2xl">Payment Successful!</CardTitle>
          <CardDescription>
            Your credits have been added to your account.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="text-center p-4 bg-muted rounded-lg">
            <p className="text-sm text-muted-foreground">Current Balance</p>
            <p className="text-4xl font-bold">{credits}</p>
            <p className="text-sm text-muted-foreground">credits</p>
          </div>

          <div className="space-y-2">
            <Button className="w-full" asChild>
              <Link href="/research/new">
                Start New Research
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button variant="outline" className="w-full" asChild>
              <Link href="/dashboard">Go to Dashboard</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

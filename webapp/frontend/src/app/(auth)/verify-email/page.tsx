"use client"

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function VerifyEmailPage() {
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setError('Invalid verification link.')
      return
    }

    const verifyEmail = async () => {
      try {
        const response = await fetch(`${API_URL}/api/auth/verify-email`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token }),
        })

        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.detail || 'Verification failed')
        }

        setStatus('success')
      } catch (err: any) {
        setStatus('error')
        setError(err.message || 'Something went wrong')
      }
    }

    verifyEmail()
  }, [token])

  if (status === 'loading') {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="pt-6">
          <div className="text-center space-y-4">
            <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
            <h2 className="text-xl font-semibold">Verifying your email...</h2>
            <p className="text-muted-foreground">Please wait a moment.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (status === 'error') {
    return (
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 rounded-full bg-red-100 flex items-center justify-center">
            <XCircle className="h-6 w-6 text-red-600" />
          </div>
          <CardTitle className="text-2xl">Verification Failed</CardTitle>
          <CardDescription>{error}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-center text-muted-foreground">
            The verification link may have expired or already been used.
          </p>
        </CardContent>
        <CardFooter className="flex flex-col gap-2">
          <Link href="/dashboard" className="w-full">
            <Button className="w-full">Go to Dashboard</Button>
          </Link>
          <p className="text-sm text-center text-muted-foreground">
            You can request a new verification email from your settings.
          </p>
        </CardFooter>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        <div className="mx-auto mb-4 h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
          <CheckCircle className="h-6 w-6 text-green-600" />
        </div>
        <CardTitle className="text-2xl">Email Verified!</CardTitle>
        <CardDescription>
          Your email has been successfully verified.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-center text-muted-foreground">
          You now have full access to all features.
        </p>
      </CardContent>
      <CardFooter>
        <Link href="/dashboard" className="w-full">
          <Button className="w-full">Go to Dashboard</Button>
        </Link>
      </CardFooter>
    </Card>
  )
}

"use client"

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/hooks/use-auth'
import { api } from '@/lib/api'
import { ArrowRight, Envelope, LockKey, Sparkle, GoogleLogo } from '@phosphor-icons/react'

export default function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleEnabled, setGoogleEnabled] = useState(false)

  useEffect(() => {
    // Check for OAuth errors in URL
    const oauthError = searchParams.get('error')
    if (oauthError) {
      const errorMessages: Record<string, string> = {
        oauth_denied: 'Google sign-in was cancelled',
        oauth_invalid: 'Invalid OAuth response',
        oauth_expired: 'OAuth session expired, please try again',
        oauth_no_email: 'Could not get email from Google',
        oauth_failed: 'Google sign-in failed, please try again',
      }
      setError(errorMessages[oauthError] || 'OAuth error occurred')
    }

    // Check if Google OAuth is enabled
    api.getOAuthStatus().then(status => {
      setGoogleEnabled(status.google)
    }).catch(() => {})
  }, [searchParams])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(email, password)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full animate-fade-in-up">
      {/* Card */}
      <div className="glass-card rounded-2xl p-8 shadow-2xl shadow-black/10">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-muted/50 mb-6">
            <Sparkle className="h-3.5 w-3.5 text-accent" weight="duotone" />
            <span className="text-xs text-muted-foreground">Welcome back</span>
          </div>
          <h1 className="text-3xl font-bold mb-2">Sign In</h1>
          <p className="text-muted-foreground">
            Enter your credentials to access your account
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="p-4 mb-6 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-sm font-medium">Email</Label>
            <div className="relative">
              <Envelope className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" weight="duotone" />
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-11 h-12 bg-muted/50 border-border/50 focus:border-primary/50"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password" className="text-sm font-medium">Password</Label>
              <Link
                href="/forgot-password"
                className="text-sm text-muted-foreground hover:text-primary transition-colors"
              >
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <LockKey className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" weight="duotone" />
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-11 h-12 bg-muted/50 border-border/50 focus:border-primary/50"
                required
              />
            </div>
          </div>

          <Button
            type="submit"
            className="w-full h-12 text-base font-medium glow-primary"
            disabled={loading}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                Signing in...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                Sign In
                <ArrowRight className="h-4 w-4" weight="bold" />
              </span>
            )}
          </Button>
        </form>

        {/* Google OAuth */}
        {googleEnabled && (
          <>
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border/50" />
              </div>
              <div className="relative flex justify-center">
                <span className="px-4 text-xs text-muted-foreground bg-card">
                  Or continue with
                </span>
              </div>
            </div>

            <Button
              type="button"
              variant="outline"
              className="w-full h-12 bg-muted/30 hover:bg-muted/50 border-border/50 gap-2"
              onClick={() => window.location.href = api.getGoogleAuthUrl()}
            >
              <GoogleLogo className="h-5 w-5" weight="bold" />
              Sign in with Google
            </Button>
          </>
        )}

        {/* Footer */}
        <p className="text-sm text-muted-foreground text-center mt-8">
          Don&apos;t have an account?{' '}
          <Link href="/register" className="text-primary hover:underline font-medium">
            Create one
          </Link>
        </p>
      </div>
    </div>
  )
}

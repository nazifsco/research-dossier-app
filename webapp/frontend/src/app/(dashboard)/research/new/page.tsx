"use client"

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Building2, User, Zap, BarChart3, Search } from 'lucide-react'

const depthOptions = [
  {
    value: 'quick',
    label: 'Quick',
    credits: 1,
    description: 'Basic overview with key facts',
    icon: Zap,
  },
  {
    value: 'standard',
    label: 'Standard',
    credits: 2,
    description: 'Comprehensive report with financials and news',
    icon: BarChart3,
  },
  {
    value: 'deep',
    label: 'Deep',
    credits: 4,
    description: 'In-depth analysis with all available sources',
    icon: Search,
  },
]

export default function NewResearchPage() {
  const router = useRouter()
  const [target, setTarget] = useState('')
  const [targetType, setTargetType] = useState<'company' | 'person'>('company')
  const [depth, setDepth] = useState('standard')
  const [credits, setCredits] = useState<number>(0)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const isSubmitting = useRef(false) // Ref to prevent double-clicks

  useEffect(() => {
    api.getCredits().then(data => {
      setCredits(data.credits || 0)
    }).catch(console.error)
  }, [])

  const selectedDepth = depthOptions.find(d => d.value === depth)!
  const hasEnoughCredits = credits >= selectedDepth.credits

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Prevent double-clicks using ref (more reliable than state)
    if (isSubmitting.current) {
      return
    }

    if (!target.trim()) {
      setError('Please enter a target to research')
      return
    }

    if (!hasEnoughCredits) {
      setError('Not enough credits')
      return
    }

    // Lock submission immediately
    isSubmitting.current = true
    setLoading(true)

    try {
      const job = await api.createResearch({
        target: target.trim(),
        target_type: targetType,
        depth,
      })
      router.push(`/research/${job.id}`)
    } catch (err: any) {
      setError(err.message || 'Failed to create research job')
      // Only unlock on error - successful submission navigates away
      isSubmitting.current = false
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">New Research</h1>
        <p className="text-muted-foreground">Create a new research dossier</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Research Target</CardTitle>
          <CardDescription>
            Enter the company or person you want to research
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-6">
            {error && (
              <div className="p-3 text-sm text-red-500 bg-red-500/10 rounded-md">
                {error}
              </div>
            )}

            {/* Target Input */}
            <div className="space-y-2">
              <Label htmlFor="target">Target Name</Label>
              <Input
                id="target"
                placeholder="e.g., OpenAI, Elon Musk, Microsoft"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                required
              />
            </div>

            {/* Target Type */}
            <div className="space-y-2">
              <Label>Target Type</Label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setTargetType('company')}
                  className={`flex items-center gap-3 p-4 rounded-lg border transition-colors ${
                    targetType === 'company'
                      ? 'border-primary bg-primary/5'
                      : 'border-input hover:bg-muted'
                  }`}
                >
                  <Building2 className={`h-5 w-5 ${targetType === 'company' ? 'text-primary' : 'text-muted-foreground'}`} />
                  <div className="text-left">
                    <div className="font-medium">Company</div>
                    <div className="text-xs text-muted-foreground">Business or organization</div>
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() => setTargetType('person')}
                  className={`flex items-center gap-3 p-4 rounded-lg border transition-colors ${
                    targetType === 'person'
                      ? 'border-primary bg-primary/5'
                      : 'border-input hover:bg-muted'
                  }`}
                >
                  <User className={`h-5 w-5 ${targetType === 'person' ? 'text-primary' : 'text-muted-foreground'}`} />
                  <div className="text-left">
                    <div className="font-medium">Person</div>
                    <div className="text-xs text-muted-foreground">Individual profile</div>
                  </div>
                </button>
              </div>
            </div>

            {/* Depth Selection */}
            <div className="space-y-2">
              <Label>Research Depth</Label>
              <div className="space-y-2">
                {depthOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setDepth(option.value)}
                    className={`w-full flex items-center gap-4 p-4 rounded-lg border transition-colors text-left ${
                      depth === option.value
                        ? 'border-primary bg-primary/5'
                        : 'border-input hover:bg-muted'
                    }`}
                  >
                    <option.icon className={`h-5 w-5 ${depth === option.value ? 'text-primary' : 'text-muted-foreground'}`} />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{option.label}</span>
                        <span className={`text-sm ${credits >= option.credits ? 'text-muted-foreground' : 'text-red-500'}`}>
                          {option.credits} credit{option.credits > 1 ? 's' : ''}
                        </span>
                      </div>
                      <div className="text-sm text-muted-foreground">{option.description}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Credits Warning */}
            {!hasEnoughCredits && (
              <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                <p className="text-sm text-yellow-500">
                  You need {selectedDepth.credits} credits but only have {credits}.{' '}
                  <a href="/credits" className="underline">Buy more credits</a>
                </p>
              </div>
            )}

            {/* Submit */}
            <Button
              type="submit"
              className="w-full"
              size="lg"
              disabled={loading || !hasEnoughCredits}
            >
              {loading ? 'Starting Research...' : `Start Research (${selectedDepth.credits} credit${selectedDepth.credits > 1 ? 's' : ''})`}
            </Button>
          </CardContent>
        </form>
      </Card>
    </div>
  )
}

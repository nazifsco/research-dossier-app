"use client"

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { api, ResearchJob } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Plus, FileText, Clock, CheckCircle, XCircle, Trash,
  CreditCard, ChartLineUp, Sparkle, ArrowRight, SpinnerGap, Scroll
} from '@phosphor-icons/react'
import { formatDateTime } from '@/lib/utils'

const statusConfig = {
  pending: { label: 'Pending', variant: 'secondary' as const, icon: Clock, color: 'text-muted-foreground', weight: 'duotone' as const },
  processing: { label: 'Processing', variant: 'warning' as const, icon: SpinnerGap, color: 'text-amber-500', weight: 'bold' as const },
  completed: { label: 'Completed', variant: 'success' as const, icon: CheckCircle, color: 'text-primary', weight: 'duotone' as const },
  failed: { label: 'Failed', variant: 'destructive' as const, icon: XCircle, color: 'text-red-500', weight: 'duotone' as const },
}

export default function DashboardPage() {
  const router = useRouter()
  const [jobs, setJobs] = useState<ResearchJob[]>([])
  const [credits, setCredits] = useState<number>(0)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<string | null>(null)

  const fetchData = () => {
    Promise.all([
      api.listResearch(),
      api.getCredits()
    ]).then(([jobsData, creditsData]) => {
      setJobs(jobsData.jobs || [])
      setCredits(creditsData.credits || 0)
    }).catch(console.error).finally(() => {
      setLoading(false)
    })
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleDelete = async (e: React.MouseEvent, jobId: string) => {
    e.preventDefault()
    e.stopPropagation()

    if (!confirm('Are you sure you want to delete this research? This cannot be undone.')) {
      return
    }

    setDeleting(jobId)
    try {
      await api.deleteResearch(jobId)
      setJobs(jobs.filter(j => j.id !== jobId))
    } catch (err: any) {
      alert(err.message || 'Failed to delete')
    } finally {
      setDeleting(null)
    }
  }

  // Poll for updates on processing jobs
  useEffect(() => {
    const hasProcessing = jobs.some(j => j.status === 'processing' || j.status === 'pending')
    if (!hasProcessing) return

    const interval = setInterval(() => {
      api.listResearch().then(data => {
        setJobs(data.jobs || [])
      }).catch(console.error)
    }, 5000)

    return () => clearInterval(interval)
  }, [jobs])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-4">
          <SpinnerGap className="h-8 w-8 animate-spin text-primary" weight="bold" />
          <p className="text-muted-foreground">Loading your dashboard...</p>
        </div>
      </div>
    )
  }

  const completedJobs = jobs.filter(j => j.status === 'completed').length
  const processingJobs = jobs.filter(j => j.status === 'processing' || j.status === 'pending').length

  return (
    <div className="space-y-8 animate-fade-in-up">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-1">Dashboard</h1>
          <p className="text-muted-foreground">Manage your research intelligence</p>
        </div>
        <Link href="/research/new">
          <Button className="gap-2 glow-primary">
            <Plus className="h-5 w-5" weight="bold" />
            New Research
          </Button>
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300 group">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">Available Credits</p>
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center group-hover:from-primary/30 group-hover:to-primary/10 transition-all shadow-lg shadow-primary/5">
                <CreditCard className="h-6 w-6 text-primary" weight="duotone" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold mb-2">{credits}</p>
            <Link href="/credits" className="text-sm text-primary hover:underline inline-flex items-center gap-1">
              Buy more credits
              <ArrowRight className="h-4 w-4" weight="bold" />
            </Link>
          </CardContent>
        </Card>

        <Card className="border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300 group">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">Total Reports</p>
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-accent/20 to-accent/5 flex items-center justify-center group-hover:from-accent/30 group-hover:to-accent/10 transition-all shadow-lg shadow-accent/5">
                <Scroll className="h-6 w-6 text-accent" weight="duotone" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold mb-2">{jobs.length}</p>
            <p className="text-sm text-muted-foreground">
              {completedJobs} completed
            </p>
          </CardContent>
        </Card>

        <Card className="border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300 group">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">In Progress</p>
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500/20 to-amber-500/5 flex items-center justify-center group-hover:from-amber-500/30 group-hover:to-amber-500/10 transition-all shadow-lg shadow-amber-500/5">
                <ChartLineUp className="h-6 w-6 text-amber-500" weight="duotone" />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold mb-2">{processingJobs}</p>
            <p className="text-sm text-muted-foreground">
              Jobs in queue
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Jobs */}
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardHeader className="border-b border-border/50">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold font-sans">Recent Research</h2>
              <p className="text-sm text-muted-foreground mt-1">Your latest intelligence reports</p>
            </div>
            {jobs.length > 0 && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-muted/50">
                <Sparkle className="h-4 w-4 text-accent" weight="duotone" />
                <span className="text-xs text-muted-foreground">{jobs.length} total</span>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {jobs.length === 0 ? (
            <div className="text-center py-16 px-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mx-auto mb-6 shadow-lg shadow-primary/10">
                <Scroll className="h-8 w-8 text-primary" weight="duotone" />
              </div>
              <h3 className="text-xl font-semibold mb-2 font-sans">No research yet</h3>
              <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
                Create your first research dossier to unlock comprehensive intelligence insights
              </p>
              <Link href="/research/new">
                <Button className="gap-2 glow-primary">
                  <Plus className="h-5 w-5" weight="bold" />
                  Start Research
                </Button>
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-border/50">
              {jobs.slice(0, 10).map((job) => {
                const config = statusConfig[job.status]
                const StatusIcon = config.icon
                const canDelete = job.status === 'completed' || job.status === 'failed'
                return (
                  <div
                    key={job.id}
                    onClick={() => router.push(`/research/${job.id}`)}
                    className="flex items-center justify-between p-5 hover:bg-muted/30 transition-colors cursor-pointer group"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/15 to-primary/5 flex items-center justify-center group-hover:from-primary/25 group-hover:to-primary/10 transition-all">
                        <FileText className="h-6 w-6 text-primary" weight="duotone" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-base mb-0.5 group-hover:text-primary transition-colors">
                          {job.target}
                        </h4>
                        <p className="text-sm text-muted-foreground">
                          <span className="capitalize">{job.target_type}</span>
                          <span className="mx-2 text-border">·</span>
                          <span className="capitalize">{job.depth}</span>
                          <span className="mx-2 text-border">·</span>
                          {formatDateTime(job.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge
                        variant={config.variant}
                        className={`gap-1.5 px-3 py-1 ${config.color}`}
                      >
                        <StatusIcon
                          className={`h-4 w-4 ${job.status === 'processing' ? 'animate-spin' : ''}`}
                          weight={config.weight}
                        />
                        {config.label}
                      </Badge>
                      {canDelete && (
                        <button
                          onClick={(e) => handleDelete(e, job.id)}
                          disabled={deleting === job.id}
                          className="p-2.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-all disabled:opacity-50"
                          title="Delete research"
                        >
                          {deleting === job.id ? (
                            <SpinnerGap className="h-4 w-4 animate-spin" weight="bold" />
                          ) : (
                            <Trash className="h-4 w-4" weight="duotone" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

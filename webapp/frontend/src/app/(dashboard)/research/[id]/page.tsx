"use client"

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, ResearchJob } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  ArrowLeft,
  Download,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  FileText,
  Building2,
  User,
  RefreshCw
} from 'lucide-react'
import { formatDateTime } from '@/lib/utils'

const statusConfig = {
  pending: { label: 'Pending', variant: 'secondary' as const, icon: Clock, color: 'text-muted-foreground' },
  processing: { label: 'Processing', variant: 'warning' as const, icon: Loader2, color: 'text-yellow-500' },
  completed: { label: 'Completed', variant: 'success' as const, icon: CheckCircle, color: 'text-green-500' },
  failed: { label: 'Failed', variant: 'destructive' as const, icon: XCircle, color: 'text-red-500' },
}

export default function ResearchDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [job, setJob] = useState<ResearchJob | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const jobId = params.id as string

  const fetchJob = async () => {
    try {
      const data = await api.getResearch(jobId)
      setJob(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load research')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJob()
  }, [jobId])

  // Poll for updates if processing
  useEffect(() => {
    if (!job || (job.status !== 'processing' && job.status !== 'pending')) return

    const interval = setInterval(fetchJob, 5000)
    return () => clearInterval(interval)
  }, [job?.status])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold mb-2">Research Not Found</h2>
        <p className="text-muted-foreground mb-4">{error || 'This research job does not exist'}</p>
        <Link href="/dashboard">
          <Button>Back to Dashboard</Button>
        </Link>
      </div>
    )
  }

  const config = statusConfig[job.status]
  const StatusIcon = config.icon
  const TypeIcon = job.target_type === 'company' ? Building2 : User

  const handleDownload = () => {
    const url = api.getDownloadUrl(jobId)
    window.open(url, '_blank')
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Back Button */}
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Dashboard
      </Link>

      {/* Header Card */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                <TypeIcon className="h-6 w-6 text-primary" />
              </div>
              <div>
                <CardTitle className="text-2xl">{job.target}</CardTitle>
                <CardDescription className="flex items-center gap-2 mt-1">
                  <span className="capitalize">{job.target_type}</span>
                  <span>&middot;</span>
                  <span className="capitalize">{job.depth} research</span>
                  <span>&middot;</span>
                  <span>{job.credits_used} credit{job.credits_used !== 1 ? 's' : ''}</span>
                </CardDescription>
              </div>
            </div>
            <Badge variant={config.variant} className="gap-1.5">
              <StatusIcon className={`h-3.5 w-3.5 ${job.status === 'processing' ? 'animate-spin' : ''}`} />
              {config.label}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Created</p>
              <p className="font-medium">{formatDateTime(job.created_at)}</p>
            </div>
            {job.started_at && (
              <div>
                <p className="text-muted-foreground">Started</p>
                <p className="font-medium">{formatDateTime(job.started_at)}</p>
              </div>
            )}
            {job.completed_at && (
              <div>
                <p className="text-muted-foreground">Completed</p>
                <p className="font-medium">{formatDateTime(job.completed_at)}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Status-specific content */}
      {job.status === 'pending' && (
        <Card>
          <CardContent className="py-12 text-center">
            <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Waiting in Queue</h3>
            <p className="text-muted-foreground">
              Your research job is queued and will start processing shortly.
            </p>
          </CardContent>
        </Card>
      )}

      {job.status === 'processing' && (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="relative mx-auto w-16 h-16 mb-4">
              <Loader2 className="h-16 w-16 text-primary animate-spin" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Research in Progress</h3>
            <p className="text-muted-foreground mb-4">
              We&apos;re gathering data from multiple sources. This usually takes a few minutes.
            </p>
            <div className="flex justify-center">
              <Button variant="outline" size="sm" onClick={fetchJob} className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Refresh Status
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {job.status === 'completed' && (
        <Card>
          <CardContent className="py-12 text-center">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Research Complete</h3>
            <p className="text-muted-foreground mb-6">
              Your dossier is ready for download.
            </p>
            <Button size="lg" onClick={handleDownload} className="gap-2">
              <Download className="h-5 w-5" />
              Download Report
            </Button>
          </CardContent>
        </Card>
      )}

      {job.status === 'failed' && (
        <Card>
          <CardContent className="py-12 text-center">
            <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Research Failed</h3>
            <p className="text-muted-foreground mb-2">
              {job.error_message || 'An error occurred while generating the report.'}
            </p>
            <p className="text-sm text-muted-foreground mb-6">
              Your credits have been refunded.
            </p>
            <Link href="/research/new">
              <Button>Try Again</Button>
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

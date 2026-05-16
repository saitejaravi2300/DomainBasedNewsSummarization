'use client'

import { useEffect, useState, use } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Clock, FileText, TrendingUp, Sparkles, RefreshCw, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { TrendCard } from '@/components/trend-card'
import { getAuthHeaders } from '@/lib/auth-utils'
import type { Digest, Trend } from '@/lib/types'

interface PageProps {
  params: Promise<{ id: string }>
}

export default function DigestDetailPage({ params }: PageProps) {
  const { id } = use(params)
  const router = useRouter()
  const [digest, setDigest] = useState<Digest | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRegenerating, setIsRegenerating] = useState(false)

  useEffect(() => {
    const loadDigest = async () => {
      try {
        setIsLoading(true)
        const response = await fetch(`/api/digest/history`, {
          headers: getAuthHeaders(),
        })
        
        if (response.ok) {
          const history = await response.json()
          const item = history.find((h: any) => h.id === id)
          
          if (item) {
            setDigest({
              digest_id: item.id,
              domain: item.domain,
              days: 7,
              generated_at: item.date,
              total_trends: item.trends,
              total_articles: item.articles || 0,
              cached: true,
              trends: [],
            })
          }
        }
      } catch (error) {
        console.error('Failed to load digest:', error)
      } finally {
        setIsLoading(false)
      }
    }

    if (id) {
      loadDigest()
    }
  }, [id])

  const handleRegenerate = async () => {
    if (!digest) return
    
    setIsRegenerating(true)
    try {
      const response = await fetch('/api/digest', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          domain: digest.domain.toLowerCase().replace(/[^a-z]/g, '_'),
          days: digest.days,
          skip_cache: true,
        }),
      })
      
      if (response.ok) {
        const data = await response.json()
        setDigest(data)
      }
    } catch (error) {
      console.error('Failed to regenerate digest:', error)
    } finally {
      setIsRegenerating(false)
    }
  }

  if (isLoading) {
    return (
      <div className="p-6 lg:p-8">
        <div className="mb-6 flex items-center gap-4">
          <Link href="/briefings">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div className="h-8 w-48 animate-pulse rounded bg-secondary" />
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse rounded-xl border border-border bg-card p-6">
              <div className="h-6 w-3/4 rounded bg-secondary" />
              <div className="mt-2 h-4 w-full rounded bg-secondary" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!digest) {
    return (
      <div className="p-6 lg:p-8">
        <div className="mb-6 flex items-center gap-4">
          <Link href="/briefings">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
        </div>
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <FileText className="h-12 w-12 text-muted-foreground" />
          <h2 className="mt-4 text-xl font-semibold">Digest not found</h2>
          <p className="mt-2 text-muted-foreground">
            This digest may have expired or been deleted.
          </p>
          <Link href="/briefings" className="mt-6">
            <Button>Back to Briefings</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="mb-4 flex items-center gap-4">
          <Link href="/briefings">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-bold">{digest.domain}</h1>
              <span className="text-muted-foreground">|</span>
              <span className="text-muted-foreground">last {digest.days} days</span>
              <Badge variant="secondary" className="gap-1">
                <FileText className="h-3 w-3" />
                {digest.total_trends} trends
              </Badge>
              {digest.cached && (
                <Badge variant="outline" className="text-xs">
                  Cached
                </Badge>
              )}
            </div>
            <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-3 w-3" />
              Generated {new Date(digest.generated_at).toLocaleDateString('en-US', {
                month: 'long',
                day: 'numeric',
                year: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
              })}
            </div>
          </div>
          <Button 
            onClick={handleRegenerate} 
            disabled={isRegenerating}
            className="gap-2"
          >
            {isRegenerating ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Regenerating...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Regenerate
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Trends */}
      {digest.trends.length > 0 ? (
        <div className="space-y-4">
          {digest.trends
            .sort((a: Trend, b: Trend) => b.signal_score - a.signal_score)
            .map((trend: Trend) => (
              <TrendCard
                key={trend.trend_id}
                trend={trend}
                isExpanded={false}
                onToggle={() => {}}
                showActions={false}
              />
            ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border p-12 text-center">
          <TrendingUp className="h-12 w-12 text-muted-foreground" />
          <h2 className="mt-4 text-lg font-semibold">No trends found</h2>
          <p className="mt-2 max-w-md text-muted-foreground">
            This digest was generated but the trends data is no longer available. 
            Try regenerating to fetch fresh data.
          </p>
          <Button onClick={handleRegenerate} className="mt-4 gap-2">
            <Sparkles className="h-4 w-4" />
            Generate Fresh Digest
          </Button>
        </div>
      )}
    </div>
  )
}

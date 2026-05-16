'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { FileText, Calendar, TrendingUp, Clock, ChevronRight, Sparkles, Filter } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { getAuthHeaders } from '@/lib/auth-utils'
import { DOMAINS } from '@/lib/types'

interface DigestHistoryItem {
  id: string
  domain: string
  date: string
  trends: number
  articles?: number
}

export default function BriefingsPage() {
  const [history, setHistory] = useState<DigestHistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null)

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setIsLoading(true)
        const response = await fetch('/api/digest/history', {
          headers: getAuthHeaders(),
        })
        if (response.ok) {
          const data = await response.json()
          setHistory(Array.isArray(data) ? data : [])
        }
      } catch (error) {
        console.error('Failed to load history:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadHistory()
  }, [])

  const filteredHistory = selectedDomain
    ? history.filter(h => h.domain.toLowerCase() === selectedDomain.toLowerCase())
    : history

  const getDomainLabel = (domainId: string) => {
    const found = DOMAINS.find(d => d.id === domainId || d.label.toLowerCase() === domainId.toLowerCase())
    return found?.label || domainId
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  const getDaysAgo = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffTime = Math.abs(now.getTime() - date.getTime())
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
    return `${Math.floor(diffDays / 30)} months ago`
  }

  const groupedByDate = filteredHistory.reduce((acc, item) => {
    const dateKey = item.date.split('T')[0]
    if (!acc[dateKey]) {
      acc[dateKey] = []
    }
    acc[dateKey].push(item)
    return acc
  }, {} as Record<string, DigestHistoryItem[]>)

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Briefings</h1>
          <p className="mt-2 text-muted-foreground">
            Your digest history and saved intelligence
          </p>
        </div>
        <Link href="/dashboard">
          <Button className="gap-2">
            <Sparkles className="h-4 w-4" />
            New Digest
          </Button>
        </Link>
      </div>

      {/* Filter */}
      <div className="mb-6 flex flex-wrap items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Filter by domain:</span>
        <button
          onClick={() => setSelectedDomain(null)}
          className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
            selectedDomain === null
              ? 'bg-primary text-primary-foreground'
              : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
          }`}
        >
          All
        </button>
        {DOMAINS.map((domain) => (
          <button
            key={domain.id}
            onClick={() => setSelectedDomain(domain.label)}
            className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
              selectedDomain === domain.label
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
          >
            {domain.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse rounded-xl border border-border bg-card p-6">
              <div className="h-6 w-1/3 rounded bg-secondary" />
              <div className="mt-2 h-4 w-1/2 rounded bg-secondary" />
            </div>
          ))}
        </div>
      ) : filteredHistory.length > 0 ? (
        <div className="space-y-8">
          {Object.entries(groupedByDate).map(([dateKey, items]) => (
            <div key={dateKey}>
              <h2 className="mb-4 flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Calendar className="h-4 w-4" />
                {formatDate(dateKey)}
                <span className="text-xs">({getDaysAgo(dateKey)})</span>
              </h2>
              <div className="space-y-3">
                {items.map((item) => (
                  <Link
                    key={item.id}
                    href={`/briefings/${item.id}`}
                    className="group block rounded-xl border border-border bg-card p-6 transition-all hover:border-primary/30 hover:shadow-md"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="font-medium">
                            {getDomainLabel(item.domain)}
                          </Badge>
                          <span className="text-xs text-muted-foreground flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {getDaysAgo(item.date)}
                          </span>
                        </div>
                        <h3 className="mt-2 text-lg font-semibold group-hover:text-primary">
                          {item.domain} Digest
                        </h3>
                        <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <TrendingUp className="h-3 w-3" />
                            {item.trends} trends
                          </span>
                          {item.articles && (
                            <span className="flex items-center gap-1">
                              <FileText className="h-3 w-3" />
                              {item.articles} articles
                            </span>
                          )}
                        </div>
                      </div>
                      <ChevronRight className="h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-1 group-hover:text-primary" />
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary">
            <FileText className="h-8 w-8 text-muted-foreground" />
          </div>
          <h2 className="text-xl font-semibold">No briefings yet</h2>
          <p className="mt-2 max-w-md text-muted-foreground">
            Generate your first digest to start building your intelligence history.
          </p>
          <Link href="/dashboard" className="mt-6">
            <Button className="gap-2">
              <Sparkles className="h-4 w-4" />
              Generate Digest
            </Button>
          </Link>
        </div>
      )}
    </div>
  )
}

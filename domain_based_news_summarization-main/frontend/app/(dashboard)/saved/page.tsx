'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Bookmark, Clock, Users, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { cn } from '@/lib/utils'
import { getAuthHeaders } from '@/lib/auth-utils'
import { SavedTrend } from '@/lib/types'

export default function SavedTrendsPage() {
  const [savedTrends, setSavedTrends] = useState<SavedTrend[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Group trends by domain
  const groupedTrends = savedTrends.reduce((acc, savedTrend) => {
    const domain = savedTrend.domain || 'Unknown'
    if (!acc[domain]) {
      acc[domain] = []
    }
    acc[domain].push(savedTrend)
    return acc
  }, {} as Record<string, SavedTrend[]>)

  useEffect(() => {
    const loadSavedTrends = async () => {
      try {
        setIsLoading(true)
        const response = await fetch('/api/user/saved-trends', {
          headers: getAuthHeaders(),
        })
        if (!response.ok) {
          setSavedTrends([])
          return
        }
        const data = await response.json()
        const normalized = Array.isArray(data)
          ? data.filter((item: any) => {
              return (
                item &&
                typeof item.id === 'string' &&
                item.trend &&
                typeof item.trend.signal_score === 'number' &&
                typeof item.trend.trend_title === 'string'
              )
            })
          : []
        setSavedTrends(normalized)
      } catch (error) {
        console.error('Failed to load saved trends:', error)
        setSavedTrends([])
      } finally {
        setIsLoading(false)
      }
    }

    loadSavedTrends()
  }, [])

  const handleRemove = async (id: string) => {
    try {
      const response = await fetch(`/api/user/saved-trends/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      })
      if (!response.ok) {
        throw new Error('Failed to remove saved trend')
      }
      setSavedTrends(prev => prev.filter(t => t.id !== id))
    } catch (error) {
      console.error('Failed to remove saved trend:', error)
      alert('Could not remove saved trend right now. Please try again.')
    }
  }

  const getSignalColor = (score: number) => {
    if (score >= 8) return 'bg-signal-high'
    if (score >= 5) return 'bg-signal-medium'
    return 'bg-signal-low'
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Saved Trends</h1>
        <p className="mt-2 text-muted-foreground">
          Trends you&apos;ve bookmarked for later reference
        </p>
      </div>

      {isLoading ? (
        <div className="text-sm text-muted-foreground">Loading saved trends...</div>
      ) : savedTrends.length > 0 ? (
        <div className="space-y-8">
          {Object.entries(groupedTrends).map(([domain, trends]) => (
            <div key={domain}>
              <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                <Bookmark className="h-4 w-4 text-primary" />
                {domain}
                <Badge variant="secondary" className="ml-2">{trends.length}</Badge>
              </h2>
              
              <div className="space-y-4">
                {trends.map((savedTrend) => (
                  <div
                    key={savedTrend.id}
                    className="group relative overflow-hidden rounded-xl border border-border bg-card transition-all hover:border-primary/30"
                  >
                    {/* Signal accent bar */}
                    <div className={cn(
                      "absolute left-0 top-0 bottom-0 w-1",
                      getSignalColor(savedTrend.trend.signal_score)
                    )} />
                    
                    <div className="p-6 pl-8">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-semibold leading-tight">
                            {savedTrend.trend.trend_title}
                          </h3>
                          <p className="mt-2 text-muted-foreground line-clamp-2">
                            {savedTrend.trend.tldr}
                          </p>
                        </div>
                        
                        <div className="flex items-center gap-2 shrink-0">
                          <Badge variant="outline" className="font-mono">
                            Signal {savedTrend.trend.signal_score}/10
                          </Badge>
                        </div>
                      </div>

                      {/* So What */}
                      <div className="mt-4 rounded-lg border-l-4 border-primary bg-primary/5 p-3">
                        <p className="text-xs font-medium text-primary mb-1">So What?</p>
                        <p className="text-sm">{savedTrend.trend.so_what}</p>
                      </div>

                      {/* Footer */}
                      <div className="mt-4 flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-border">
                        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            Saved {new Date(savedTrend.saved_at).toLocaleDateString()}
                          </span>
                          <span className="flex items-center gap-1">
                            <Users className="h-3 w-3" />
                            {savedTrend.trend.source_count} sources
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive">
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Remove saved trend?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  This will remove the trend from your saved list. You can always save it again later.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction onClick={() => handleRemove(savedTrend.id)}>
                                  Remove
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      </div>

                      {/* Key Entities */}
                      <div className="mt-4 flex flex-wrap gap-2">
                        {savedTrend.trend.key_entities.slice(0, 4).map((entity) => (
                          <Badge key={entity} variant="secondary" className="text-xs">
                            {entity}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-secondary">
            <Bookmark className="h-8 w-8 text-muted-foreground" />
          </div>
          <h2 className="text-xl font-semibold">No saved trends yet</h2>
          <p className="mt-2 max-w-md text-muted-foreground">
            Click the bookmark icon on any trend to save it for later reference.
          </p>
          <Link href="/dashboard">
            <Button className="mt-6">
              Generate a digest
            </Button>
          </Link>
        </div>
      )}
    </div>
  )
}

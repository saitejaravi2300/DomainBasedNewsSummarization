'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { 
  Sparkles, Download, RefreshCw, Clock, 
  FileText, TrendingUp, Plus,
  Brain, HeartPulse, Leaf, Bitcoin, Scale, Landmark, Shield, X
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { TrendCard } from '@/components/trend-card'
import { cn } from '@/lib/utils'
import { getAuthHeaders } from '@/lib/auth-utils'
import type { Digest, Trend } from '@/lib/types'

const DOMAINS = [
  { id: 'ai', label: 'AI & ML', icon: Brain },
  { id: 'finance', label: 'Finance', icon: TrendingUp },
  { id: 'healthcare', label: 'Healthcare', icon: HeartPulse },
  { id: 'climate', label: 'Climate', icon: Leaf },
  { id: 'crypto', label: 'Crypto', icon: Bitcoin },
  { id: 'legal', label: 'Legal', icon: Scale },
  { id: 'policy', label: 'Policy', icon: Landmark },
  { id: 'cybersecurity', label: 'Cybersecurity', icon: Shield },
]

const TIME_RANGES = [
  { value: 7, label: '7d' },
  { value: 14, label: '14d' },
  { value: 29, label: '29d' },
]

type GenerationStep = 'fetching' | 'clustering' | 'generating' | 'scoring' | 'done'

const GENERATION_STEPS: { step: GenerationStep; label: string }[] = [
  { step: 'fetching', label: 'Fetching articles...' },
  { step: 'clustering', label: 'Grouping into trends...' },
  { step: 'generating', label: 'Generating insights...' },
  { step: 'scoring', label: 'Scoring signals...' },
]

export default function DashboardPage() {
  const [selectedDomain, setSelectedDomain] = useState('ai')
  const [timeRange, setTimeRange] = useState(7)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationStep, setGenerationStep] = useState<GenerationStep>('fetching')
  const [digest, setDigest] = useState<Digest | null>(null)
  const [digestCache, setDigestCache] = useState<Record<string, Digest>>({})
  const [expandedTrends, setExpandedTrends] = useState<Set<number>>(new Set())
  const [savedTrendMap, setSavedTrendMap] = useState<Record<string, string>>({})
  const [showCustomDialog, setShowCustomDialog] = useState(false)
  const [customDomainName, setCustomDomainName] = useState('')
  const [customDomainDescription, setCustomDomainDescription] = useState('')
  const [isAddingCustom, setIsAddingCustom] = useState(false)
  const [customDomains, setCustomDomains] = useState<Array<{ id: string; label: string; keywords: string; isCustom: true }>>([])

  // Prevent race conditions when domain/timeRange changes quickly.
  // We abort in-flight requests and only apply the latest response.
  const abortControllerRef = useRef<AbortController | null>(null)
  const latestRequestIdRef = useRef(0)

  const domainLabel = 
    customDomains.find(d => d.id === selectedDomain)?.label ||
    DOMAINS.find(d => d.id === selectedDomain)?.label || 
    'AI & ML'

  const getDigestCacheKey = useCallback(
    (domainId: string, range: number) => {
      const customDomain = customDomains.find(d => d.id === domainId)
      const keywordPart = (customDomain?.keywords || '').trim().toLowerCase()
      return `${domainId}|${range}|${keywordPart}`
    },
    [customDomains]
  )

  const getTrendSaveKey = useCallback((domain: string, trend: Trend) => {
    return `${(domain || '').toLowerCase()}|${trend.trend_id}|${(trend.trend_title || '').trim().toLowerCase()}`
  }, [])

  const generateDigest = useCallback(async (forceRefresh: boolean = false) => {
    console.log('[Dashboard] generateDigest called with forceRefresh:', forceRefresh)

    // Cancel any in-flight request so older responses can't overwrite state.
    abortControllerRef.current?.abort()
    const abortController = new AbortController()
    abortControllerRef.current = abortController
    const requestId = ++latestRequestIdRef.current

    const cacheKey = getDigestCacheKey(selectedDomain, timeRange)

    setIsGenerating(true)
    setDigest(null)
    
    // Simulate the generation pipeline visually while API processes
    const stepPromise = (async () => {
      for (const { step } of GENERATION_STEPS) {
        setGenerationStep(step)
        await new Promise(resolve => setTimeout(resolve, 600 + Math.random() * 300))
      }
    })()
    
    try {
      // Find the custom domain if selected
      const customDomain = customDomains.find(d => d.id === selectedDomain)
      
      const requestBody: any = { 
        domain: customDomain?.label || selectedDomain, 
        days: timeRange,
        skipCache: forceRefresh  // Force fresh data when manually refreshing
      }
      console.log('[Dashboard] Request body being sent:', requestBody)
      
      // If it's a custom domain, send keywords too
      if (customDomain) {
        requestBody.keywords = customDomain.keywords
      }

      // Call the Next.js API route which proxies to the backend
      const response = await fetch('/api/digest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
        cache: 'no-store',  // Force browser to not cache this request
        signal: abortController.signal,
      })

      // If a newer request started, ignore this one.
      if (requestId !== latestRequestIdRef.current) return
      
      if (!response.ok) {
        const errorPayload = await response.json().catch(() => ({}))
        throw new Error(errorPayload?.error || 'Failed to generate digest')
      }
      
      const data = await response.json()

      // If a newer request started while parsing JSON, ignore this result.
      if (requestId !== latestRequestIdRef.current) return
      
      // Wait for visual steps to complete
      await stepPromise

      // If a newer request started while we were waiting, ignore.
      if (requestId !== latestRequestIdRef.current) return
      
      setDigest(data)
      setDigestCache(prev => ({ ...prev, [cacheKey]: data }))
    } catch (error) {
      // Abort is expected when user switches time range/domain quickly.
      if (error instanceof DOMException && error.name === 'AbortError') {
        return
      }

      console.error('[v0] Error generating digest:', error)

      if (requestId !== latestRequestIdRef.current) return
      // Do not fall back to mockDigest (it can look like stale/cached or fake news).
      await stepPromise

      if (requestId !== latestRequestIdRef.current) return
      setDigest(null)
      alert(error instanceof Error ? error.message : 'Failed to generate digest')
    } finally {
      // Only the latest request should control the loading state.
      if (requestId === latestRequestIdRef.current) {
        setIsGenerating(false)
        setGenerationStep('done')
      }
    }
  }, [selectedDomain, domainLabel, timeRange, customDomains, getDigestCacheKey])

  // On domain/time change, restore previously generated digest for that selection,
  // or clear the old digest so stale content isn't shown.
  useEffect(() => {
    const cacheKey = getDigestCacheKey(selectedDomain, timeRange)
    setDigest(digestCache[cacheKey] ?? null)
  }, [selectedDomain, timeRange, digestCache, getDigestCacheKey])

  // Cleanup any in-flight request on unmount
  useEffect(() => {
    return () => abortControllerRef.current?.abort()
  }, [])

  // Intentionally disabled auto-generation to avoid excessive API usage.
  // Users can trigger generation manually via Refresh/Generate controls.

  useEffect(() => {
    const loadSavedTrends = async () => {
      try {
        const response = await fetch('/api/user/saved-trends', {
          headers: getAuthHeaders(),
        })
        if (!response.ok) return

        const items = await response.json()
        if (!Array.isArray(items)) return

        const nextMap: Record<string, string> = {}
        for (const item of items) {
          if (!item?.id || !item?.trend || !item?.domain) continue
          const key = getTrendSaveKey(String(item.domain), item.trend as Trend)
          nextMap[key] = String(item.id)
        }
        setSavedTrendMap(nextMap)
      } catch (error) {
        console.error('Failed to load saved trends:', error)
      }
    }

    loadSavedTrends()
  }, [getTrendSaveKey])

  useEffect(() => {
    const loadCustomDomains = async () => {
      try {
        const response = await fetch('/api/custom-domains', {
          headers: getAuthHeaders(),
        })
        if (!response.ok) return

        const data = await response.json()
        const domains = Array.isArray(data?.domains)
          ? data.domains
              .filter((d: any) => d?.id && d?.name)
              .map((d: any) => ({
                id: String(d.id),
                label: String(d.name),
                keywords: String(d.keywords || d.name),
                isCustom: true as const,
              }))
          : []

        setCustomDomains(domains)
      } catch (error) {
        console.error('Failed to load custom domains:', error)
      }
    }

    loadCustomDomains()
  }, [])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      
      if (e.key === 'g' || e.key === 'G') {
        e.preventDefault()
        if (!isGenerating) generateDigest()
      } else if (e.key === 'e' || e.key === 'E') {
        e.preventDefault()
        // Export action
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isGenerating, digest, generateDigest])

  const toggleExpanded = (trendId: number) => {
    setExpandedTrends(prev => {
      const next = new Set(prev)
      if (next.has(trendId)) {
        next.delete(trendId)
      } else {
        next.add(trendId)
      }
      return next
    })
  }

  const toggleSaved = async (trend: Trend) => {
    const activeDomain = digest?.domain || domainLabel
    const saveKey = getTrendSaveKey(activeDomain, trend)
    const existingSavedId = savedTrendMap[saveKey]

    try {
      if (existingSavedId) {
        const response = await fetch(`/api/user/saved-trends/${existingSavedId}`, {
          method: 'DELETE',
          headers: getAuthHeaders(),
        })
        if (!response.ok) throw new Error('Failed to remove saved trend')

        setSavedTrendMap(prev => {
          const next = { ...prev }
          delete next[saveKey]
          return next
        })
        return
      }

      const response = await fetch('/api/user/saved-trends', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          digest_id: digest?.digest_id,
          domain: activeDomain,
          trend,
        }),
      })
      if (!response.ok) throw new Error('Failed to save trend')

      const data = await response.json()
      const savedId = String(data?.id || '')
      if (!savedId) return

      setSavedTrendMap(prev => ({ ...prev, [saveKey]: savedId }))
    } catch (error) {
      console.error('Failed to toggle saved trend:', error)
      alert('Could not update saved trend right now. Please try again.')
    }
  }

  const handleAddCustomDomain = async () => {
    if (!customDomainName.trim()) {
      alert('Please enter a domain name')
      return
    }

    setIsAddingCustom(true)
    try {
      const response = await fetch('/api/custom-domains', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          domain_name: customDomainName,
          description: customDomainDescription,
          keywords: customDomainName // Use domain name as keywords if description not provided
        })
      })

      if (response.ok) {
        const data = await response.json()
        const apiDomainId = data?.domain?.id ? String(data.domain.id) : null
        const apiDomainName = data?.domain?.name ? String(data.domain.name) : customDomainName
        const apiKeywords = data?.domain?.keywords ? String(data.domain.keywords) : customDomainName

        const domainId = apiDomainId || `custom-${Date.now()}`
        setCustomDomains([...customDomains, {
          id: domainId,
          label: apiDomainName,
          keywords: apiKeywords,
          isCustom: true
        }])
        setSelectedDomain(domainId)
        setCustomDomainName('')
        setCustomDomainDescription('')
        setShowCustomDialog(false)
      } else {
        const errorData = await response.json().catch(() => ({}))
        console.error('API error:', response.status, errorData)
        alert(`Failed to add custom domain: ${errorData.error || response.statusText}`)
      }
    } catch (error) {
      console.error('Error adding custom domain:', error)
      alert(`Error adding custom domain: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsAddingCustom(false)
    }
  }

  const handleRemoveCustomDomain = async (domainId: string) => {
    try {
      const response = await fetch(`/api/custom-domains/${domainId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      })

      if (!response.ok) {
        throw new Error('Failed to delete custom domain')
      }

      setCustomDomains(prev => prev.filter(d => d.id !== domainId))

      if (selectedDomain === domainId) {
        setSelectedDomain('ai')
      }
    } catch (error) {
      console.error('Failed to delete custom domain:', error)
      alert('Could not remove custom domain right now. Please try again.')
    }
  }

  const generatedMinutesAgo = digest 
    ? Math.floor((Date.now() - new Date(digest.generated_at).getTime()) / 60000)
    : 0

  return (
    <div className="p-6 lg:p-8">
      {/* Top bar - Controls */}
      <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          {/* Domain pills */}
          {DOMAINS.map((domain) => {
            const Icon = domain.icon
            const isSelected = selectedDomain === domain.id
            return (
              <button
                key={domain.id}
                onClick={() => setSelectedDomain(domain.id)}
                className={cn(
                  "flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all",
                  isSelected
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                )}
              >
                <Icon className="h-4 w-4" />
                {domain.label}
              </button>
            )
          })}

          {/* Custom domains */}
          {customDomains.map((customDomain) => {
            const isSelected = selectedDomain === customDomain.id
            return (
              <div
                key={customDomain.id}
                className="group relative"
              >
                <button
                  onClick={() => setSelectedDomain(customDomain.id)}
                  className={cn(
                    "flex items-center gap-2 rounded-full px-4 py-2 pr-8 text-sm font-medium transition-all",
                    isSelected
                      ? "bg-chart-1 text-chart-1-foreground"
                      : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                  )}
                >
                  {customDomain.label}
                </button>

                <button
                  type="button"
                  aria-label={`Remove ${customDomain.label}`}
                  onClick={(e) => {
                    e.stopPropagation()
                    handleRemoveCustomDomain(customDomain.id)
                  }}
                  className={cn(
                    "absolute right-2 top-1/2 -translate-y-1/2 rounded-full p-0.5 transition-opacity",
                    "opacity-0 group-hover:opacity-100",
                    isSelected
                      ? "text-chart-1-foreground/80 hover:text-chart-1-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            )
          })}

          {/* Add custom domain dialog */}
          <Dialog open={showCustomDialog} onOpenChange={setShowCustomDialog}>
            <DialogTrigger asChild>
              <button className="flex items-center gap-2 rounded-full border border-dashed border-border px-4 py-2 text-sm text-muted-foreground transition-colors hover:border-primary hover:text-foreground">
                <Plus className="h-4 w-4" />
                Custom
              </button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Add Custom Domain Tracker</DialogTitle>
                <DialogDescription>
                  Track a custom domain to get targeted news and insights
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="domain-name">Domain Name *</Label>
                  <Input
                    id="domain-name"
                    placeholder="e.g., Data Science, Quantum Computing, Green Energy"
                    value={customDomainName}
                    onChange={(e) => setCustomDomainName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description (optional)</Label>
                  <Input
                    id="description"
                    placeholder="e.g., Focus on machine learning and statistical methods"
                    value={customDomainDescription}
                    onChange={(e) => setCustomDomainDescription(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Add more details to help us find more relevant news
                  </p>
                </div>
              </div>
              <div className="flex justify-end gap-3">
                <Button
                  variant="outline"
                  onClick={() => setShowCustomDialog(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleAddCustomDomain}
                  disabled={isAddingCustom}
                  className="gap-2"
                >
                  {isAddingCustom ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4" />
                      Add Domain
                    </>
                  )}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        <div className="flex items-center gap-3">
          {/* Time range selector */}
          <div className="flex rounded-lg border border-border bg-secondary/50 p-1">
            {TIME_RANGES.map((range) => (
              <button
                key={range.value}
                onClick={() => setTimeRange(range.value)}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-all",
                  timeRange === range.value
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {range.label}
              </button>
            ))}
          </div>

          {/* Generate button */}
          <Button
            onClick={() => generateDigest(true)}
            disabled={isGenerating}
            className="gap-2"
          >
            {isGenerating ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Generate digest
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Loading state */}
      {isGenerating && (
        <div className="mb-8">
          {/* Progress steps */}
          <div className="mb-6 flex items-center justify-center gap-2">
            {GENERATION_STEPS.map(({ step, label }, index) => {
              const currentIndex = GENERATION_STEPS.findIndex(s => s.step === generationStep)
              const isActive = index === currentIndex
              const isDone = index < currentIndex
              
              return (
                <div key={step} className="flex items-center gap-2">
                  <div
                    className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-all",
                      isDone ? "bg-primary text-primary-foreground" :
                      isActive ? "bg-primary/20 text-primary animate-pulse-glow" :
                      "bg-secondary text-muted-foreground"
                    )}
                  >
                    {index + 1}
                  </div>
                  {isActive && (
                    <span className="text-sm text-primary">{label}</span>
                  )}
                  {index < GENERATION_STEPS.length - 1 && (
                    <div className={cn(
                      "h-0.5 w-8",
                      isDone ? "bg-primary" : "bg-border"
                    )} />
                  )}
                </div>
              )
            })}
          </div>

          {/* Skeleton cards */}
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="animate-pulse rounded-xl border border-border bg-card p-6"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-2">
                    <div className="h-6 w-3/4 rounded bg-secondary" />
                    <div className="h-4 w-full rounded bg-secondary" />
                  </div>
                  <div className="flex gap-2">
                    <div className="h-6 w-20 rounded bg-secondary" />
                    <div className="h-6 w-16 rounded bg-secondary" />
                  </div>
                </div>
                <div className="mt-4 space-y-2">
                  <div className="h-4 w-full rounded bg-secondary" />
                  <div className="h-4 w-5/6 rounded bg-secondary" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Digest results */}
      {digest && !isGenerating && (
        <>
          {/* Digest header */}
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-bold">{digest.domain}</h1>
              <span className="text-muted-foreground">|</span>
              <span className="text-muted-foreground">last {digest.days} days</span>
              <Badge variant="secondary" className="gap-1">
                <FileText className="h-3 w-3" />
                {digest.total_trends} trends
              </Badge>
              <Badge variant="secondary" className="gap-1">
                <TrendingUp className="h-3 w-3" />
                {digest.total_articles} articles
              </Badge>
              {digest.model_version && (
                <Badge variant="outline" className="font-mono text-xs">
                  {digest.model_version}
                </Badge>
              )}
            </div>

            <div />
          </div>

          {/* Trend cards */}
          <div className="space-y-4">
            {digest.trends
              .sort((a, b) => b.signal_score - a.signal_score)
              .map((trend: Trend, index: number) => (
                <div
                  key={trend.trend_id}
                  className="transition-all"
                >
                  <TrendCard
                    trend={trend}
                    isExpanded={expandedTrends.has(trend.trend_id)}
                    onToggle={() => toggleExpanded(trend.trend_id)}
                    onSave={() => toggleSaved(trend)}
                    isSaved={Boolean(savedTrendMap[getTrendSaveKey(digest.domain, trend)])}
                    showActions
                  />
                </div>
              ))}
          </div>
        </>
      )}

      {/* Empty state */}
      {!digest && !isGenerating && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
            <Sparkles className="h-8 w-8 text-primary" />
          </div>
          <h2 className="text-2xl font-bold">Generate your first digest</h2>
          <p className="mt-2 max-w-md text-muted-foreground">
            Select a domain and time range above, then click Generate to create your personalized intelligence briefing.
          </p>
          <Button onClick={() => generateDigest(true)} className="mt-6 gap-2">
            <Sparkles className="h-4 w-4" />
            Generate digest
          </Button>
        </div>
      )}
    </div>
  )
}


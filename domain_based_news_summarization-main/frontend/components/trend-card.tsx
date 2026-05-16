'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink, Bookmark, AlertTriangle, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Trend } from '@/lib/types'
import { cn } from '@/lib/utils'

interface TrendCardProps {
  trend: Trend
  isExpanded?: boolean
  onToggle?: () => void
  onSave?: () => void
  isSaved?: boolean
  showActions?: boolean
}

export function TrendCard({ 
  trend, 
  isExpanded = false, 
  onToggle,
  onSave,
  isSaved = false,
  showActions = true
}: TrendCardProps) {
  const [showTimeline, setShowTimeline] = useState(false)
  const [showSources, setShowSources] = useState(false)
  const confidence = (trend.confidence_level || trend.evidence?.confidence_level || 'low').toLowerCase()
  const confidenceClass =
    confidence === 'high' ? 'text-emerald-700 border-emerald-300 bg-emerald-50' :
    confidence === 'medium' ? 'text-amber-700 border-amber-300 bg-amber-50' :
    'text-rose-700 border-rose-300 bg-rose-50'
  const warningFlags = trend.evidence?.warning_flags ?? []

  const SUMMARY_PREVIEW_CHARS = 360
  const summaryText = (trend.summary || '').trim()
  const shouldShowToggle = summaryText.length > SUMMARY_PREVIEW_CHARS
  const summaryPreview = shouldShowToggle
    ? `${summaryText.slice(0, SUMMARY_PREVIEW_CHARS).trimEnd().replace(/\s+\S*$/, '')}...`
    : summaryText

  const formatDisplayDate = (raw: string) => {
    const dt = new Date(raw)
    if (Number.isNaN(dt.getTime())) return raw
    return dt.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    })
  }

  const signalColor = trend.signal_score >= 8 
    ? 'bg-signal-high' 
    : trend.signal_score >= 5 
      ? 'bg-signal-medium' 
      : 'bg-signal-low'

  const signalTextColor = trend.signal_score >= 8 
    ? 'text-signal-high' 
    : trend.signal_score >= 5 
      ? 'text-signal-medium' 
      : 'text-signal-low'

  // Summary engine badge logic
  let engineLabel = null
  if (trend.summary_engine === 'gemma_primary') engineLabel = 'Gemma'
  else if (trend.summary_engine === 'groq_fallback') engineLabel = 'Llama'
  else if (trend.summary_engine === 'extractive_fallback') engineLabel = 'Extractive'

  return (
    <div className="group relative overflow-hidden rounded-xl border border-border bg-card transition-all hover:border-primary/30">
      {/* Signal accent bar */}
      <div className={cn("absolute left-0 top-0 bottom-0 w-1", signalColor)} />
      
      <div className="p-6 pl-8">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold leading-tight break-words">{trend.trend_title}</h3>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {engineLabel && (
              <Badge variant="secondary" className="font-mono bg-blue-100 text-blue-700 border-blue-300">
                {engineLabel}
              </Badge>
            )}
            <Badge variant="outline" className={cn("font-mono", signalTextColor)}>
              Signal {trend.signal_score}/10
            </Badge>
            <Badge variant="outline" className={cn("capitalize", confidenceClass)}>
              Confidence {confidence}
            </Badge>
          </div>
        </div>

        {/* TL;DR - Always visible */}
        <p className="mt-3 text-muted-foreground break-words">{trend.tldr}</p>

        {/* Summary */}
        <div className="mt-4">
          <div className="text-sm leading-relaxed whitespace-pre-line break-words">
            {isExpanded ? summaryText : summaryPreview}
          </div>
          {onToggle && shouldShowToggle && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggle}
              className="mt-2 h-auto p-0 text-primary hover:text-primary/80"
            >
              {isExpanded ? (
                <>Show less <ChevronUp className="ml-1 h-4 w-4" /></>
              ) : (
                <>Read more <ChevronDown className="ml-1 h-4 w-4" /></>
              )}
            </Button>
          )}
        </div>

        {/* So What? - Always visible */}
        <div className="mt-4 rounded-lg border-l-4 border-primary bg-primary/5 p-4">
          <p className="text-sm font-medium text-primary">So What?</p>
          <p className="mt-1 text-sm">{trend.so_what}</p>
        </div>

        {/* Evidence Row */}
        {trend.evidence && (
          <div className="mt-4 rounded-lg border bg-secondary/20 p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Evidence</p>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span>{trend.evidence.unique_source_count} unique sources</span>
              <span>{Math.round((trend.evidence.valid_link_ratio || 0) * 100)}% valid links</span>
              <span>{Math.round((trend.evidence.duplicate_ratio || 0) * 100)}% duplicate overlap</span>
              <span>{trend.evidence.recency_days}d recency</span>
              <span>Relevance {Number(trend.evidence.avg_relevance || 0).toFixed(2)}</span>
            </div>
          </div>
        )}

        {warningFlags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {warningFlags.map((flag) => (
              <Badge key={flag} variant="outline" className="text-[10px] uppercase tracking-wide text-warning border-warning/40">
                {flag.replace(/_/g, ' ')}
              </Badge>
            ))}
          </div>
        )}

        {/* Timeline - Collapsible */}
        {trend.timeline.length > 0 && (
          <div className="mt-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowTimeline(!showTimeline)}
              className="h-auto p-0 text-muted-foreground hover:text-foreground"
            >
              Story evolution {showTimeline ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />}
            </Button>
            {showTimeline && (
              <div className="mt-3 space-y-2 pl-4 border-l-2 border-border">
                {trend.timeline.map((event, index) => (
                  <div key={index} className="relative">
                    <div className="absolute -left-[17px] top-1.5 h-2 w-2 rounded-full bg-primary" />
                    <p className="text-xs text-muted-foreground">{formatDisplayDate(event.date)}</p>
                    <p className="text-sm">{event.event}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Contrast - Only shown if exists */}
        {trend.contrast && (
          <div className="mt-4 rounded-lg border border-warning/30 bg-warning/5 p-4">
            <div className="flex items-center gap-2 text-warning">
              <AlertTriangle className="h-4 w-4" />
              <p className="text-sm font-medium">Sources Disagree</p>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{trend.contrast}</p>
          </div>
        )}

        {/* Footer */}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-border">
          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Users className="h-3 w-3" />
              {trend.source_count} sources
            </span>
          </div>
          
          {showActions && (
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSources(!showSources)}
              >
                Sources {showSources ? <ChevronUp className="ml-1 h-4 w-4" /> : <ChevronDown className="ml-1 h-4 w-4" />}
              </Button>
              {onSave && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onSave}
                  className={isSaved ? 'text-primary' : ''}
                >
                  <Bookmark className={cn("h-4 w-4", isSaved && "fill-current")} />
                </Button>
              )}
            </div>
          )}
        </div>

        {/* Sources - Expandable */}
        {showSources && (
          <div className="mt-4 space-y-2">
            {trend.articles.map((article, index) => {
              const hasValidLink = /^https?:\/\//i.test(article.url || '')

              if (!hasValidLink) {
                return (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-lg bg-secondary/50 p-3 text-sm opacity-80"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="truncate font-medium">{article.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {article.source} · {formatDisplayDate(article.published)}
                      </p>
                    </div>
                  </div>
                )
              }

              return (
                <a
                  key={index}
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between rounded-lg bg-secondary/50 p-3 text-sm transition-colors hover:bg-secondary"
                >
                  <div className="flex-1 min-w-0">
                    <p className="truncate font-medium">{article.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {article.source} · {formatDisplayDate(article.published)}
                    </p>
                  </div>
                  <ExternalLink className="h-4 w-4 shrink-0 ml-3 text-muted-foreground" />
                </a>
              )
            })}
          </div>
        )}

        {/* Key Entities */}
        {trend.key_entities.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {trend.key_entities.map((entity) => (
              <Badge key={entity} variant="secondary" className="text-xs">
                {entity}
              </Badge>
            ))}          </div>
        )}
      </div>
    </div>
  )
}

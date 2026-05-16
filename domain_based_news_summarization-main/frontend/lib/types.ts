export interface Article {
  title: string
  source: string
  url: string
  published: string
  description?: string
  content?: string
}

export interface TimelineEvent {
  date: string
  event: string
}

export interface TrendEvidence {
  confidence_level: 'high' | 'medium' | 'low' | string
  confidence_score: number
  unique_source_count: number
  article_count: number
  valid_link_ratio: number
  duplicate_ratio: number
  recency_days: number
  avg_relevance: number
  warning_flags: string[]
}

export interface Trend {
  trend_id: number
  trend_title: string
  tldr: string
  summary: string
  timeline: TimelineEvent[]
  so_what: string
  signal_score: number
  contrast: string | null
  key_entities: string[]
  source_count: number
  articles: Article[]
  confidence_level?: 'high' | 'medium' | 'low' | string
  evidence?: TrendEvidence | null
  model_version?: string | null
  summary_engine?: 'gemma_primary' | 'groq_fallback' | 'extractive_fallback';
}

export interface Digest {
  digest_id: string
  domain: string
  days: number
  generated_at: string
  total_trends: number
  total_articles: number
  cached: boolean
  trends: Trend[]
  model_version?: string | null
}

export interface User {
  id: string
  email: string
  name: string
  avatar_url?: string
  preferences: UserPreferences
  created_at: string
  last_active_at: string
}

export interface UserPreferences {
  default_domain: string
  default_days: number
  daily_digest_enabled: boolean
  daily_digest_time: string
  daily_digest_domain: string
}

export interface SavedTrend {
  id: string
  user_id: string
  digest_id: string
  trend_id: number
  saved_at: string
  trend: Trend
  domain: string
}

export const DOMAINS = [
  { id: 'ai', label: 'AI & ML', icon: 'brain' },
  { id: 'finance', label: 'Finance', icon: 'trending-up' },
  { id: 'healthcare', label: 'Healthcare', icon: 'heart-pulse' },
  { id: 'climate', label: 'Climate', icon: 'leaf' },
  { id: 'crypto', label: 'Crypto', icon: 'bitcoin' },
  { id: 'legal', label: 'Legal', icon: 'scale' },
  { id: 'policy', label: 'Policy', icon: 'landmark' },
  { id: 'cybersecurity', label: 'Cybersecurity', icon: 'shield' },
] as const

export type DomainId = typeof DOMAINS[number]['id']

export const TIME_RANGES = [
  { value: 7, label: '7d' },
  { value: 14, label: '14d' },
  { value: 29, label: '29d' },
] as const

export type TimeRangeValue = typeof TIME_RANGES[number]['value']

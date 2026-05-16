'use client'

import { useEffect, useState } from 'react'
import { Settings, Bell, Globe, RefreshCw, Plus, Trash2, Check, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { getAuthHeaders } from '@/lib/auth-utils'
import { DOMAINS } from '@/lib/types'
import { cn } from '@/lib/utils'

interface UserPreferences {
  default_domain: string
  default_days: number
  daily_digest_enabled: boolean
  daily_digest_time: string
  daily_digest_domain: string
}

interface CustomDomain {
  id: string
  name: string
  keywords: string
  description?: string
}

export default function SettingsPage() {
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  
  const [preferences, setPreferences] = useState<UserPreferences>({
    default_domain: 'ai',
    default_days: 7,
    daily_digest_enabled: false,
    daily_digest_time: '08:00',
    daily_digest_domain: 'ai',
  })
  
  const [customDomains, setCustomDomains] = useState<CustomDomain[]>([])
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [newDomainName, setNewDomainName] = useState('')
  const [newDomainKeywords, setNewDomainKeywords] = useState('')
  const [newDomainDescription, setNewDomainDescription] = useState('')
  const [isAddingDomain, setIsAddingDomain] = useState(false)

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true)
        
        const prefsResponse = await fetch('/api/user/preferences', {
          headers: getAuthHeaders(),
        })
        if (prefsResponse.ok) {
          const prefsData = await prefsResponse.json()
          if (prefsData.preferences) {
            setPreferences(prefsData.preferences)
          }
        }
        
        const domainsResponse = await fetch('/api/custom-domains', {
          headers: getAuthHeaders(),
        })
        if (domainsResponse.ok) {
          const domainsData = await domainsResponse.json()
          if (Array.isArray(domainsData.domains)) {
            setCustomDomains(domainsData.domains.map((d: any) => ({
              id: d.id,
              name: d.name,
              keywords: d.keywords || d.name,
              description: d.description,
            })))
          }
        }
      } catch (err) {
        console.error('Failed to load settings:', err)
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])

  const handleSavePreferences = async () => {
    setIsSaving(true)
    setError('')
    try {
      const response = await fetch('/api/user/preferences', {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify(preferences),
      })

      if (!response.ok) {
        throw new Error('Failed to save preferences')
      }

      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save preferences')
    } finally {
      setIsSaving(false)
    }
  }

  const handleAddCustomDomain = async () => {
    if (!newDomainName.trim()) {
      setError('Please enter a domain name')
      return
    }

    setIsAddingDomain(true)
    setError('')
    try {
      const response = await fetch('/api/custom-domains', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          domain_name: newDomainName,
          keywords: newDomainKeywords || newDomainName,
          description: newDomainDescription,
        }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Failed to add domain')
      }

      const data = await response.json()
      if (data.domain) {
        setCustomDomains([...customDomains, {
          id: data.domain.id,
          name: data.domain.name,
          keywords: data.domain.keywords || data.domain.name,
          description: data.domain.description,
        }])
      }

      setNewDomainName('')
      setNewDomainKeywords('')
      setNewDomainDescription('')
      setShowAddDialog(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add domain')
    } finally {
      setIsAddingDomain(false)
    }
  }

  const handleDeleteDomain = async (domainId: string) => {
    try {
      const response = await fetch(`/api/custom-domains/${domainId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      })

      if (!response.ok) {
        throw new Error('Failed to delete domain')
      }

      setCustomDomains(customDomains.filter(d => d.id !== domainId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete domain')
    }
  }

  if (isLoading) {
    return (
      <div className="p-6 lg:p-8">
        <div className="flex items-center gap-2">
          <Settings className="h-6 w-6" />
          <h1 className="text-3xl font-bold">Settings</h1>
        </div>
        <div className="mt-6 text-muted-foreground">Loading settings...</div>
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-8">
        <div className="flex items-center gap-2">
          <Settings className="h-6 w-6" />
          <h1 className="text-3xl font-bold">Settings</h1>
        </div>
        <p className="mt-2 text-muted-foreground">Manage your preferences and custom domains</p>
      </div>

      {error && (
        <div className="mb-6 rounded-lg bg-destructive/10 p-4 text-sm text-destructive flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      <div className="max-w-2xl space-y-8">
        {/* Default Preferences */}
        <section className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-6 flex items-center gap-2 text-lg font-semibold">
            <Globe className="h-5 w-5" />
            Default Preferences
          </h2>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="default-domain">Default Domain</Label>
              <select
                id="default-domain"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                value={preferences.default_domain}
                onChange={(e) => setPreferences({ ...preferences, default_domain: e.target.value })}
              >
                {DOMAINS.map((d) => (
                  <option key={d.id} value={d.id}>{d.label}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="default-days">Default Time Range</Label>
              <select
                id="default-days"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                value={preferences.default_days}
                onChange={(e) => setPreferences({ ...preferences, default_days: parseInt(e.target.value) })}
              >
                <option value="7">7 days</option>
                <option value="14">14 days</option>
                <option value="29">29 days</option>
              </select>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Daily Digest</Label>
                <p className="text-sm text-muted-foreground">
                  Receive a daily briefing in your inbox
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={preferences.daily_digest_enabled}
                onClick={() => setPreferences({ ...preferences, daily_digest_enabled: !preferences.daily_digest_enabled })}
                className={cn(
                  "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                  preferences.daily_digest_enabled ? "bg-primary" : "bg-secondary"
                )}
              >
                <span
                  className={cn(
                    "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                    preferences.daily_digest_enabled ? "translate-x-6" : "translate-x-1"
                  )}
                />
              </button>
            </div>

            {preferences.daily_digest_enabled && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="digest-time">Digest Time</Label>
                  <Input
                    id="digest-time"
                    type="time"
                    value={preferences.daily_digest_time}
                    onChange={(e) => setPreferences({ ...preferences, daily_digest_time: e.target.value })}
                    className="w-40"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="digest-domain">Digest Domain</Label>
                  <select
                    id="digest-domain"
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                    value={preferences.daily_digest_domain}
                    onChange={(e) => setPreferences({ ...preferences, daily_digest_domain: e.target.value })}
                  >
                    {DOMAINS.map((d) => (
                      <option key={d.id} value={d.id}>{d.label}</option>
                    ))}
                    {customDomains.map((d) => (
                      <option key={d.id} value={d.name}>{d.name} (Custom)</option>
                    ))}
                  </select>
                </div>
              </>
            )}

            <div className="pt-4">
              <Button onClick={handleSavePreferences} disabled={isSaving}>
                {saved ? (
                  <>
                    <Check className="mr-2 h-4 w-4" />
                    Saved
                  </>
                ) : isSaving ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Bell className="mr-2 h-4 w-4" />
                    Save Preferences
                  </>
                )}
              </Button>
            </div>
          </div>
        </section>

        {/* Custom Domains */}
        <section className="rounded-xl border border-border bg-card p-6">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <Globe className="h-5 w-5" />
              Custom Domains
            </h2>
            <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
              <DialogTrigger asChild>
                <Button size="sm" className="gap-2">
                  <Plus className="h-4 w-4" />
                  Add Domain
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>Add Custom Domain</DialogTitle>
                  <DialogDescription>
                    Create a custom domain to track specific topics
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="domain-name">Domain Name *</Label>
                    <Input
                      id="domain-name"
                      placeholder="e.g., Quantum Computing, Green Tech"
                      value={newDomainName}
                      onChange={(e) => setNewDomainName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="domain-keywords">Keywords</Label>
                    <Input
                      id="domain-keywords"
                      placeholder="quantum, computing, qubits (comma-separated)"
                      value={newDomainKeywords}
                      onChange={(e) => setNewDomainKeywords(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Leave empty to use domain name as keywords
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="domain-description">Description (optional)</Label>
                    <Input
                      id="domain-description"
                      placeholder="Brief description of the domain"
                      value={newDomainDescription}
                      onChange={(e) => setNewDomainDescription(e.target.value)}
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-3">
                  <Button variant="outline" onClick={() => setShowAddDialog(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleAddCustomDomain} disabled={isAddingDomain}>
                    {isAddingDomain ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        Adding...
                      </>
                    ) : (
                      'Add Domain'
                    )}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>

          {customDomains.length > 0 ? (
            <div className="space-y-3">
              {customDomains.map((domain) => (
                <div
                  key={domain.id}
                  className="flex items-center justify-between rounded-lg border border-border bg-secondary/20 p-4"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium">{domain.name}</h3>
                      <Badge variant="secondary" className="text-xs">Custom</Badge>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Keywords: {domain.keywords}
                    </p>
                    {domain.description && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        {domain.description}
                      </p>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteDomain(domain.id)}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-border p-8 text-center">
              <Globe className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-2 text-sm text-muted-foreground">
                No custom domains yet. Add one to track specific topics.
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

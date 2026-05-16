'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Zap, ArrowRight, ArrowLeft, Check, Brain, TrendingUp, HeartPulse, Leaf, Bitcoin, Scale, Landmark, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

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
  { value: 7, label: '7 days' },
  { value: 30, label: '30 days' },
  { value: 90, label: '90 days' },
]

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [selectedDomains, setSelectedDomains] = useState<string[]>(['ai'])
  const [timeRange, setTimeRange] = useState(7)
  const [isLoading, setIsLoading] = useState(false)

  const toggleDomain = (domainId: string) => {
    setSelectedDomains(prev => 
      prev.includes(domainId)
        ? prev.filter(d => d !== domainId)
        : [...prev, domainId]
    )
  }

  const handleNext = () => {
    if (step < 2) {
      setStep(step + 1)
    } else {
      handleComplete()
    }
  }

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1)
    }
  }

  const handleComplete = async () => {
    setIsLoading(true)
    // Simulate saving preferences
    await new Promise(resolve => setTimeout(resolve, 1000))
    router.push('/dashboard')
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      {/* Background gradient */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-1/4 h-[400px] w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/10 blur-3xl" />
      </div>

      <div className="relative w-full max-w-lg">
        {/* Logo */}
        <div className="mb-8 flex justify-center">
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <Zap className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-semibold">{"What's New?"}</span>
          </div>
        </div>

        {/* Progress indicator */}
        <div className="mb-8 flex items-center justify-center gap-2">
          {[1, 2].map((s) => (
            <div
              key={s}
              className={cn(
                "h-2 rounded-full transition-all",
                s === step ? "w-8 bg-primary" : s < step ? "w-2 bg-primary" : "w-2 bg-border"
              )}
            />
          ))}
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-border bg-card p-8">
          {/* Step 1: Domain selection */}
          {step === 1 && (
            <div className="space-y-6">
              <div className="text-center">
                <h1 className="text-2xl font-bold">What domains do you follow?</h1>
                <p className="mt-2 text-sm text-muted-foreground">
                  Select the domains you want to track. You can change these anytime.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {DOMAINS.map((domain) => {
                  const Icon = domain.icon
                  const isSelected = selectedDomains.includes(domain.id)
                  return (
                    <button
                      key={domain.id}
                      onClick={() => toggleDomain(domain.id)}
                      className={cn(
                        "flex items-center gap-3 rounded-xl border p-4 text-left transition-all",
                        isSelected
                          ? "border-primary bg-primary/10"
                          : "border-border hover:border-primary/50"
                      )}
                    >
                      <div className={cn(
                        "flex h-10 w-10 items-center justify-center rounded-lg",
                        isSelected ? "bg-primary/20" : "bg-secondary"
                      )}>
                        <Icon className={cn("h-5 w-5", isSelected ? "text-primary" : "text-muted-foreground")} />
                      </div>
                      <span className="font-medium">{domain.label}</span>
                      {isSelected && (
                        <Check className="ml-auto h-4 w-4 text-primary" />
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* Step 2: Time range */}
          {step === 2 && (
            <div className="space-y-6">
              <div className="text-center">
                <h1 className="text-2xl font-bold">How far back should we look?</h1>
                <p className="mt-2 text-sm text-muted-foreground">
                  Choose your default time range for news analysis.
                </p>
              </div>

              <div className="flex flex-col gap-3">
                {TIME_RANGES.map((range) => (
                  <button
                    key={range.value}
                    onClick={() => setTimeRange(range.value)}
                    className={cn(
                      "flex items-center justify-between rounded-xl border p-4 transition-all",
                      timeRange === range.value
                        ? "border-primary bg-primary/10"
                        : "border-border hover:border-primary/50"
                    )}
                  >
                    <span className="font-medium">{range.label}</span>
                    {timeRange === range.value && (
                      <Check className="h-4 w-4 text-primary" />
                    )}
                  </button>
                ))}
              </div>

              <p className="text-center text-sm text-muted-foreground">
                Tip: 7 days is best for staying current. 30+ days helps spot emerging patterns.
              </p>
            </div>
          )}



          {/* Navigation */}
          <div className="mt-8 flex items-center justify-between">
            <Button
              variant="ghost"
              onClick={handleBack}
              disabled={step === 1}
              className={step === 1 ? 'invisible' : ''}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>

            <Button onClick={handleNext} disabled={isLoading || (step === 1 && selectedDomains.length === 0)}>
              {step === 2 ? (
                isLoading ? 'Setting up...' : 'Start exploring'
              ) : (
                'Continue'
              )}
              {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

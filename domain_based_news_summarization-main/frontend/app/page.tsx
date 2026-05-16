'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowRight, Zap, TrendingUp, Shield, Clock, Brain, BarChart3, ChevronRight, Target, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DOMAINS } from '@/lib/types'
import { mockDigest } from '@/lib/mock-data'
import { TrendCard } from '@/components/trend-card'

const domainLabels = DOMAINS.map(d => d.label)

export default function LandingPage() {
  const [activeDomain, setActiveDomain] = useState(0)
  const [activeTrend, setActiveTrend] = useState(0)

  useEffect(() => {
    const domainInterval = setInterval(() => {
      setActiveDomain((prev) => (prev + 1) % domainLabels.length)
    }, 2000)
    return () => clearInterval(domainInterval)
  }, [])

  useEffect(() => {
    const trendInterval = setInterval(() => {
      setActiveTrend((prev) => (prev + 1) % mockDigest.trends.length)
    }, 4000)
    return () => clearInterval(trendInterval)
  }, [])

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Zap className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-lg font-semibold">{"What's New?"}</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost" size="sm">Sign in</Button>
            </Link>
            <Link href="/register">
              <Button size="sm">Get started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden min-h-screen flex flex-col items-center justify-center">
        {/* Background gradient - Multiple animated orbs */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute left-1/2 top-0 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/4 rounded-full bg-primary/20 blur-3xl" />
          <div className="absolute right-0 top-1/2 h-[400px] w-[400px] -translate-y-1/2 rounded-full bg-chart-1/10 blur-2xl" />
          <div className="absolute left-0 bottom-0 h-[500px] w-[500px] rounded-full bg-chart-2/10 blur-2xl" />
          <div className="absolute left-1/3 top-1/3 h-[300px] w-[300px] rounded-full bg-primary/5 blur-3xl" />
        </div>

        <div className="relative mx-auto max-w-7xl px-6 flex flex-col items-center text-center">
          {/* Main headline */}
          <h1 className="max-w-5xl text-5xl font-bold tracking-tight sm:text-6xl md:text-7xl lg:text-8xl leading-tight">
            <span className="text-balance">Your domain.</span>
            <br />
            <span className="text-balance">What changed.</span>
            <br />
            <span className="text-balance">Why it matters.</span>
          </h1>

          {/* Animated domain pills */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-2">
            {domainLabels.map((domain, index) => (
              <span
                key={domain}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition-all duration-500 ${
                  index === activeDomain
                    ? 'bg-primary text-primary-foreground scale-110'
                    : 'bg-secondary text-muted-foreground'
                }`}
              >
                {domain}
              </span>
            ))}
          </div>

          {/* CTA buttons */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-4">
            <Link href="/register">
              <Button size="lg" className="gap-2">
                Start reading smarter
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <ChevronDown className="h-6 w-6 text-primary/50" />
        </div>
      </section>

      {/* Live Demo Section */}
      <section className="border-y border-border bg-card/50 py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold">See it in action</h2>
            <p className="mt-2 text-muted-foreground">Live preview of a real AI & ML digest</p>
          </div>

          <div className="mx-auto max-w-3xl">
            <div className="relative">
              {/* Sample trend card - cycles through trends */}
              <div className="transition-all duration-700">
                <TrendCard 
                  trend={mockDigest.trends[activeTrend]} 
                  isExpanded={false}
                  onToggle={() => {}}
                />
              </div>
              
              {/* Navigation dots */}
              <div className="mt-6 flex justify-center gap-2">
                {mockDigest.trends.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setActiveTrend(index)}
                    className={`h-2 w-2 rounded-full transition-all ${
                      index === activeTrend ? 'w-6 bg-primary' : 'bg-border'
                    }`}
                    aria-label={`View trend ${index + 1}`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold">Built for busy professionals</h2>
            <p className="mt-2 text-muted-foreground">Every feature saves you time and reduces cognitive load</p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={Brain}
              title="6 trends, not 60 articles"
              description="AI clusters news into actionable trends. Read the synthesis, not the noise."
            />
            <FeatureCard
              icon={TrendingUp}
              title="So What? — your implications"
              description="Every trend ends with a specific, domain-relevant implication for your work."
            />
            <FeatureCard
              icon={BarChart3}
              title="Signal score — not all news is equal"
              description="Visual hierarchy shows which trends have the strongest evidence and coverage."
            />
            <FeatureCard
              icon={Clock}
              title="2 minutes per trend"
              description="Reading time estimates help you plan. TL;DR first, expand only what matters."
            />
            <FeatureCard
              icon={Shield}
              title="Contrast detection"
              description="When sources disagree, we tell you. Make decisions with full context."
            />
            <FeatureCard
              icon={Target}
              title="Custom domain tracking"
              description="Create custom domains for any topic. Track exactly what matters to you."
            />
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="border-y border-border bg-card/50 py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold">How it works</h2>
            <p className="mt-2 text-muted-foreground">From raw news to executive briefing in seconds</p>
          </div>

          <div className="grid gap-8 md:grid-cols-4">
            {[
              { step: '01', title: 'Fetch', description: 'We gather 60+ articles from trusted sources' },
              { step: '02', title: 'Cluster', description: 'AI groups articles into related trends' },
              { step: '03', title: 'Synthesize', description: 'Each cluster becomes a narrative summary' },
              { step: '04', title: 'Score', description: 'Signal scores highlight what matters most' },
            ].map((item) => (
              <div key={item.step} className="relative">
                <div className="text-5xl font-bold text-primary/20">{item.step}</div>
                <h3 className="mt-2 text-xl font-semibold">{item.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/20 via-background to-background p-12 text-center">
            <h2 className="text-3xl font-bold sm:text-4xl">Start reading smarter today</h2>
            <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
              Join thousands of professionals who get their domain intelligence in minutes, not hours.
            </p>
            <Link href="/register" className="mt-8 inline-block">
              <Button size="lg" className="gap-2">
                Create free account
                <ChevronRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                <Zap className="h-4 w-4 text-primary-foreground" />
              </div>
              <span className="text-lg font-semibold">{"What's New?"}</span>
            </div>
            <p className="text-sm text-muted-foreground">
              2026 {"What's New?"} — Domain intelligence for professionals
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description: string }) {
  return (
    <div className="rounded-xl border border-border bg-card p-6 transition-colors hover:border-primary/50">
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
        <Icon className="h-5 w-5 text-primary" />
      </div>
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{description}</p>
    </div>
  )
}

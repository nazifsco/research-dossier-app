"use client"

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import {
  MagnifyingGlass,
  FileText,
  Lightning,
  ShieldCheck,
  ChartLineUp,
  UsersThree,
  ArrowRight,
  Sparkle,
  GlobeHemisphereWest,
  LockKey,
  CheckCircle,
  Scroll,
  Brain,
  Newspaper,
  RocketLaunch
} from '@phosphor-icons/react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background gradient-mesh noise-bg overflow-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center shadow-lg shadow-primary/20">
              <Scroll className="h-5 w-5 text-primary-foreground" weight="duotone" />
            </div>
            <span className="font-semibold text-lg tracking-tight">ResearchDossier</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
                Sign In
              </Button>
            </Link>
            <Link href="/register">
              <Button className="gap-2 glow-primary">
                Get Started
                <ArrowRight className="h-4 w-4" weight="bold" />
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 md:pt-40 md:pb-32 relative">
        <div className="container mx-auto px-6">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-border bg-card/50 backdrop-blur-sm mb-8 animate-fade-in-up">
              <Brain className="h-4 w-4 text-accent" weight="duotone" />
              <span className="text-sm text-muted-foreground">AI-Powered Intelligence Reports</span>
            </div>

            {/* Main heading */}
            <h1 className="text-5xl md:text-7xl font-bold mb-6 animate-fade-in-up animate-delay-100 leading-[1.1]">
              Professional Research
              <br />
              <span className="text-gradient">Dossiers</span> in Minutes
            </h1>

            {/* Subheading */}
            <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto mb-10 animate-fade-in-up animate-delay-200 leading-relaxed">
              Transform any company or individual into a comprehensive intelligence report.
              Powered by AI, delivered instantly.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up animate-delay-300">
              <Link href="/register">
                <Button size="lg" className="px-8 h-12 text-base glow-primary gap-2">
                  <RocketLaunch className="h-5 w-5" weight="duotone" />
                  Start Free Trial
                </Button>
              </Link>
              <Link href="#how-it-works">
                <Button size="lg" variant="outline" className="px-8 h-12 text-base">
                  See How It Works
                </Button>
              </Link>
            </div>

            {/* Trust indicators */}
            <div className="flex items-center justify-center gap-8 mt-12 text-sm text-muted-foreground animate-fade-in-up animate-delay-400">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary" weight="duotone" />
                <span>1 Free Credit</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary" weight="duotone" />
                <span>No Credit Card</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary" weight="duotone" />
                <span>Instant Delivery</span>
              </div>
            </div>
          </div>
        </div>

        {/* Decorative elements */}
        <div className="absolute top-1/2 left-0 w-72 h-72 bg-primary/10 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />
        <div className="absolute top-1/3 right-0 w-96 h-96 bg-accent/10 rounded-full blur-3xl translate-x-1/2" />
      </section>

      {/* How it Works */}
      <section id="how-it-works" className="py-24 relative">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-sm font-medium text-primary mb-3 tracking-wider uppercase">Process</p>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">How It Works</h2>
            <p className="text-lg text-muted-foreground max-w-xl mx-auto">
              Three simple steps to comprehensive intelligence
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              {
                step: '01',
                icon: MagnifyingGlass,
                title: 'Enter Your Target',
                description: 'Type in any company name or person. Our system accepts natural language queries.'
              },
              {
                step: '02',
                icon: Lightning,
                title: 'AI Analysis',
                description: 'Our AI searches dozens of sources, cross-references data, and synthesizes insights.'
              },
              {
                step: '03',
                icon: FileText,
                title: 'Get Your Dossier',
                description: 'Receive a professionally formatted report with all the intelligence you need.'
              }
            ].map((item, index) => (
              <div key={item.step} className="relative group">
                <div className="p-8 rounded-2xl border border-border bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300 hover:border-primary/30 h-full">
                  <div className="flex items-center justify-between mb-6">
                    <span className="text-5xl font-bold text-muted-foreground/20">{item.step}</span>
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center group-hover:from-primary/30 group-hover:to-primary/10 transition-all shadow-lg shadow-primary/5">
                      <item.icon className="h-7 w-7 text-primary" weight="duotone" />
                    </div>
                  </div>
                  <h3 className="text-xl font-semibold mb-3 font-sans">{item.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">{item.description}</p>
                </div>
                {index < 2 && (
                  <div className="hidden md:block absolute top-1/2 -right-4 w-8 h-px bg-gradient-to-r from-border to-transparent" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-24 bg-muted/30 relative">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-sm font-medium text-primary mb-3 tracking-wider uppercase">Features</p>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">What You Get</h2>
            <p className="text-lg text-muted-foreground max-w-xl mx-auto">
              Comprehensive intelligence from multiple data sources
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {[
              { icon: ChartLineUp, title: 'Financial Analysis', description: 'Revenue, funding, valuations, and key financial metrics with historical trends', color: 'from-emerald-500/20 to-emerald-500/5' },
              { icon: UsersThree, title: 'Key People', description: 'Leadership profiles, backgrounds, and professional connections mapped out', color: 'from-blue-500/20 to-blue-500/5' },
              { icon: GlobeHemisphereWest, title: 'Market Position', description: 'Competitive landscape, market share, and industry positioning analysis', color: 'from-violet-500/20 to-violet-500/5' },
              { icon: Newspaper, title: 'News & Events', description: 'Recent news, press releases, and significant company events timeline', color: 'from-amber-500/20 to-amber-500/5' },
              { icon: ShieldCheck, title: 'Risk Assessment', description: 'Potential red flags, controversies, and risk factors identified', color: 'from-rose-500/20 to-rose-500/5' },
              { icon: LockKey, title: 'Data Privacy', description: 'Your research stays private. We never share or sell your queries', color: 'from-cyan-500/20 to-cyan-500/5' },
            ].map((feature) => (
              <Card key={feature.title} className="group border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 hover:border-primary/30 transition-all duration-300">
                <CardHeader className="pb-4">
                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-lg`}>
                    <feature.icon className="h-7 w-7 text-primary" weight="duotone" />
                  </div>
                  <h3 className="text-lg font-semibold font-sans">{feature.title}</h3>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-24 relative">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-sm font-medium text-primary mb-3 tracking-wider uppercase">Pricing</p>
            <h2 className="text-4xl md:text-5xl font-bold mb-4">Simple, Transparent Pricing</h2>
            <p className="text-lg text-muted-foreground max-w-xl mx-auto">
              Pay per report. No subscriptions, no hidden fees.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5 max-w-6xl mx-auto">
            {/* Starter */}
            <Card className="border-border/50 bg-card/50 backdrop-blur-sm hover:border-primary/30 transition-all duration-300">
              <CardHeader className="text-center pb-4">
                <p className="text-sm text-muted-foreground mb-2">Starter</p>
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-4xl font-bold">$5</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">1 credit</p>
              </CardHeader>
              <CardContent className="pt-4 border-t border-border/50">
                <ul className="space-y-2.5">
                  {['1 research report', 'All data sources', 'PDF download'].map((item) => (
                    <li key={item} className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-primary shrink-0" weight="duotone" />
                      <span className="text-muted-foreground">{item}</span>
                    </li>
                  ))}
                </ul>
                <Link href="/register" className="block mt-6">
                  <Button variant="outline" className="w-full">Get Started</Button>
                </Link>
              </CardContent>
            </Card>

            {/* Standard */}
            <Card className="border-border/50 bg-card/50 backdrop-blur-sm hover:border-primary/30 transition-all duration-300">
              <CardHeader className="text-center pb-4">
                <p className="text-sm text-muted-foreground mb-2">Standard</p>
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-4xl font-bold">$20</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">5 credits · $4/each</p>
              </CardHeader>
              <CardContent className="pt-4 border-t border-border/50">
                <ul className="space-y-2.5">
                  {['5 research reports', 'All data sources', 'PDF download', '20% savings'].map((item) => (
                    <li key={item} className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-primary shrink-0" weight="duotone" />
                      <span className="text-muted-foreground">{item}</span>
                    </li>
                  ))}
                </ul>
                <Link href="/register" className="block mt-6">
                  <Button variant="outline" className="w-full">Get Started</Button>
                </Link>
              </CardContent>
            </Card>

            {/* Pro - Popular */}
            <Card className="border-primary/50 bg-card/80 backdrop-blur-sm relative shadow-xl shadow-primary/10">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="px-3 py-1 text-xs font-medium bg-gradient-to-r from-primary to-accent text-primary-foreground rounded-full flex items-center gap-1">
                  <Sparkle className="h-3 w-3" weight="fill" />
                  Best Value
                </span>
              </div>
              <CardHeader className="text-center pb-4">
                <p className="text-sm text-muted-foreground mb-2">Pro</p>
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-4xl font-bold">$60</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">20 credits · $3/each</p>
              </CardHeader>
              <CardContent className="pt-4 border-t border-border/50">
                <ul className="space-y-2.5">
                  {['20 research reports', 'All data sources', 'PDF download', 'Priority processing', '40% savings'].map((item) => (
                    <li key={item} className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-primary shrink-0" weight="duotone" />
                      <span className="text-muted-foreground">{item}</span>
                    </li>
                  ))}
                </ul>
                <Link href="/register" className="block mt-6">
                  <Button className="w-full glow-primary">Get Started</Button>
                </Link>
              </CardContent>
            </Card>

            {/* Business */}
            <Card className="border-border/50 bg-card/50 backdrop-blur-sm hover:border-primary/30 transition-all duration-300">
              <CardHeader className="text-center pb-4">
                <p className="text-sm text-muted-foreground mb-2">Business</p>
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-4xl font-bold">$100</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">50 credits · $2/each</p>
              </CardHeader>
              <CardContent className="pt-4 border-t border-border/50">
                <ul className="space-y-2.5">
                  {['50 research reports', 'All data sources', 'PDF download', 'Priority processing', 'Email support', '60% savings'].map((item) => (
                    <li key={item} className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-primary shrink-0" weight="duotone" />
                      <span className="text-muted-foreground">{item}</span>
                    </li>
                  ))}
                </ul>
                <Link href="/register" className="block mt-6">
                  <Button variant="outline" className="w-full">Get Started</Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5" />
        <div className="container mx-auto px-6 relative z-10">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Ready to Get Started?
            </h2>
            <p className="text-xl text-muted-foreground mb-10">
              Create your account today and receive 1 free credit to experience
              the power of AI-driven research intelligence.
            </p>
            <Link href="/register">
              <Button size="lg" className="px-10 h-14 text-lg glow-primary gap-2">
                <RocketLaunch className="h-5 w-5" weight="duotone" />
                Create Free Account
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/50 py-12 bg-card/30">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center">
                <Scroll className="h-4 w-4 text-primary-foreground" weight="duotone" />
              </div>
              <span className="font-semibold">ResearchDossier</span>
            </div>
            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} ResearchDossier. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

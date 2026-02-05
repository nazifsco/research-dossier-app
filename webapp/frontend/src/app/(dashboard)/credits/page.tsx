"use client"

import { useEffect, useState } from 'react'
import { api, PricingTier, Payment } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  CheckCircle, CreditCard, SpinnerGap, Sparkle, Coins, Receipt, Clock
} from '@phosphor-icons/react'
import { formatCurrency, formatDateTime } from '@/lib/utils'

export default function CreditsPage() {
  const [credits, setCredits] = useState<number>(0)
  const [tiers, setTiers] = useState<PricingTier[]>([])
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)
  const [purchasing, setPurchasing] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      api.getCredits(),
      api.getTiers(),
      api.getPaymentHistory()
    ]).then(([creditsData, tiersData, paymentsData]) => {
      setCredits(creditsData.credits || 0)
      setTiers(tiersData.tiers || [])
      setPayments(paymentsData.payments || [])
    }).catch(console.error).finally(() => {
      setLoading(false)
    })
  }, [])

  const handlePurchase = async (tierId: string) => {
    setPurchasing(tierId)
    try {
      const { checkout_url } = await api.createCheckout(tierId)
      window.location.href = checkout_url
    } catch (err) {
      console.error('Checkout error:', err)
      setPurchasing(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-4">
          <SpinnerGap className="h-8 w-8 animate-spin text-primary" weight="bold" />
          <p className="text-muted-foreground">Loading pricing...</p>
        </div>
      </div>
    )
  }

  // Find the "pro" tier to highlight as best value
  const bestValueTierId = "pro"

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fade-in-up">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-1">Credits</h1>
        <p className="text-muted-foreground">Purchase credits to generate research dossiers</p>
      </div>

      {/* Current Balance */}
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">Current Balance</p>
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center shadow-lg shadow-primary/5">
              <Coins className="h-6 w-6 text-primary" weight="duotone" />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-5xl font-bold mb-3">{credits} <span className="text-2xl font-normal text-muted-foreground">credits</span></p>
          <p className="text-sm text-muted-foreground">
            Credits are used to generate research reports. Standard reports cost 1 credit.
          </p>
        </CardContent>
      </Card>

      {/* Pricing Tiers */}
      <div>
        <h2 className="text-xl font-semibold mb-4 font-sans">Buy Credits</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {tiers.map((tier) => {
            const isBestValue = tier.id === bestValueTierId
            const savings = tier.credits > 1
              ? Math.round((1 - (tier.price_cents / tier.credits) / (tiers[0]?.price_cents || 500)) * 100)
              : 0

            return (
              <Card
                key={tier.id}
                className={`relative transition-all duration-300 ${
                  isBestValue
                    ? 'border-primary/50 bg-card/80 shadow-xl shadow-primary/10'
                    : 'border-border/50 bg-card/50 hover:border-primary/30'
                }`}
              >
                {isBestValue && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="px-3 py-1 text-xs font-medium bg-gradient-to-r from-primary to-accent text-primary-foreground rounded-full flex items-center gap-1">
                      <Sparkle className="h-3 w-3" weight="fill" />
                      Best Value
                    </span>
                  </div>
                )}
                <CardHeader className="text-center pb-3">
                  <p className="text-sm text-muted-foreground mb-1">{tier.name}</p>
                  <div className="flex items-baseline justify-center gap-1">
                    <span className="text-3xl font-bold">
                      {formatCurrency(tier.price_cents / 100)}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    {tier.credits} credit{tier.credits > 1 ? 's' : ''}
                    {tier.credits > 1 && (
                      <span className="text-primary"> · ${(tier.price_cents / 100 / tier.credits).toFixed(0)}/each</span>
                    )}
                  </p>
                </CardHeader>
                <CardContent className="space-y-4 pt-3 border-t border-border/50">
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-primary" weight="duotone" />
                      <span className="text-muted-foreground">{tier.credits} research report{tier.credits > 1 ? 's' : ''}</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-primary" weight="duotone" />
                      <span className="text-muted-foreground">All data sources</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-primary" weight="duotone" />
                      <span className="text-muted-foreground">PDF download</span>
                    </li>
                    {tier.credits >= 5 && (
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-primary" weight="duotone" />
                        <span className="text-muted-foreground">Priority processing</span>
                      </li>
                    )}
                    {savings > 0 && (
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-accent" weight="duotone" />
                        <span className="text-accent font-medium">{savings}% savings</span>
                      </li>
                    )}
                  </ul>
                  <Button
                    className={`w-full ${isBestValue ? 'glow-primary' : ''}`}
                    variant={isBestValue ? 'default' : 'outline'}
                    onClick={() => handlePurchase(tier.id)}
                    disabled={purchasing !== null}
                  >
                    {purchasing === tier.id ? (
                      <span className="flex items-center gap-2">
                        <SpinnerGap className="h-4 w-4 animate-spin" weight="bold" />
                        Redirecting...
                      </span>
                    ) : (
                      <span className="flex items-center gap-2">
                        <CreditCard className="h-4 w-4" weight="duotone" />
                        Buy Now
                      </span>
                    )}
                  </Button>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Payment History */}
      {payments.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4 font-sans">Payment History</h2>
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-0">
              <div className="divide-y divide-border/50">
                {payments.map((payment) => (
                  <div key={payment.id} className="flex items-center justify-between p-5">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                        <Receipt className="h-5 w-5 text-primary" weight="duotone" />
                      </div>
                      <div>
                        <p className="font-semibold">
                          {payment.credits_purchased} credit{payment.credits_purchased > 1 ? 's' : ''}
                        </p>
                        <p className="text-sm text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" weight="duotone" />
                          {formatDateTime(payment.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="text-right flex items-center gap-4">
                      <p className="font-semibold">
                        {formatCurrency(payment.amount_cents / 100)}
                      </p>
                      <Badge
                        variant={payment.status === 'completed' ? 'success' : 'secondary'}
                        className="capitalize"
                      >
                        {payment.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

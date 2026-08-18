'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'motion/react'
import { PlusCircle, TrendingUp, AlertTriangle, Activity, Droplet } from 'lucide-react'
import { PageHeading } from '@/components/shell/app-shell'
import { Panel, PanelHeader, Skeleton, AnimatedNumber } from '@/components/ui/panel'
import { StockRing } from '@/components/dashboard/stock-ring'
import { TrendChart } from '@/components/dashboard/trend-chart'
import { RequestCard } from '@/components/requests/request-card'
import { listContainer, listItem, pageVariants, useMotionSafe } from '@/lib/motion'
import { getStock, getTrend, getRequests } from '@/lib/mockApi'
import { buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function DashboardView() {
  const [stock, setStock] = useState<any[] | null>(null)
  const [trend, setTrend] = useState<any[] | null>(null)
  const [requests, setRequests] = useState<any[] | null>(null)
  const variants = useMotionSafe(pageVariants)

  useEffect(() => {
    getStock().then(setStock)
    getTrend(7).then(setTrend)
    getRequests().then(setRequests)
  }, [])

  const lowGroups = stock?.filter((s) => s.units < s.threshold) ?? []
  const activeCount =
    requests?.filter((r) => r.status !== 'Fulfilled').length ?? 0
  const totalUnits = stock?.reduce((a, s) => a + s.units, 0) ?? 0

  return (
    <motion.div variants={variants} initial="hidden" animate="show">
      <motion.div variants={listItem}>
        <PageHeading
          title="Blood Bank Dashboard"
          description="Live stock, active emergency requests, and matching activity across the network."
          action={
            <Link
              href="/requests/new"
              className={cn(buttonVariants({ size: 'lg' }), 'h-11 gap-2 px-5 text-sm')}
            >
              <PlusCircle className="size-4.5" /> New Request
            </Link>
          }
        />
      </motion.div>

      {/* Stat strip */}
      <motion.div
        variants={listContainer}
        initial="hidden"
        animate="show"
        className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4"
      >
        <StatCard icon={Droplet} label="Total units on hand" value={totalUnits} tone="primary" />
        <StatCard icon={Activity} label="Active requests" value={activeCount} tone="routine" />
        <StatCard
          icon={AlertTriangle}
          label="Groups below safe"
          value={lowGroups.length}
          tone={lowGroups.length ? 'critical' : 'success'}
        />
        <StatCard icon={TrendingUp} label="Avg. match time" value={11} suffix=" min" tone="success" />
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Stock rings */}
        <Panel className="lg:col-span-2">
          <PanelHeader
            title="Stock by blood group"
            subtitle="Units on hand vs. safe threshold — critically low groups breathe."
          />
          {stock ? (
            <motion.div
              variants={listContainer}
              initial="hidden"
              animate="show"
              className="grid grid-cols-2 gap-y-6 sm:grid-cols-4"
            >
              {stock.map((s, i) => (
                <motion.div key={s.group} variants={listItem}>
                  <StockRing item={s} delay={i * 0.05} />
                </motion.div>
              ))}
            </motion.div>
          ) : (
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="flex flex-col items-center gap-2">
                  <Skeleton className="size-[92px] rounded-full" />
                  <Skeleton className="h-3 w-14" />
                </div>
              ))}
            </div>
          )}
        </Panel>

        {/* Trend */}
        <Panel>
          <PanelHeader title="Requests · last 7 days" subtitle="Raised vs. fulfilled" />
          {trend ? (
            <TrendChart data={trend} />
          ) : (
            <Skeleton className="h-56 w-full rounded-xl" />
          )}
        </Panel>
      </div>

      {/* Active requests */}
      <Panel className="mt-6" animated={false}>
        <PanelHeader
          title="Active requests"
          subtitle="Live status across all wards"
          action={
            <Link
              href="/requests"
              className="text-xs font-medium text-primary hover:underline"
            >
              View all
            </Link>
          }
        />
        {requests ? (
          <motion.div
            variants={listContainer}
            initial="hidden"
            animate="show"
            className="flex flex-col gap-3"
          >
            {requests.map((r) => (
              <RequestCard key={r.id} req={r} />
            ))}
          </motion.div>
        ) : (
          <div className="flex flex-col gap-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-20 w-full rounded-2xl" />
            ))}
          </div>
        )}
      </Panel>
    </motion.div>
  )
}

function StatCard({
  icon: Icon,
  label,
  value,
  suffix = '',
  tone,
}: {
  icon: typeof Droplet
  label: string
  value: number
  suffix?: string
  tone: 'primary' | 'routine' | 'critical' | 'success'
}) {
  const toneClass = {
    primary: 'text-primary bg-accent',
    routine: 'text-routine bg-routine/10',
    critical: 'text-critical bg-critical/10',
    success: 'text-success bg-success/10',
  }[tone]

  return (
    <motion.div
      variants={listItem}
      className="rounded-2xl border border-border bg-card p-4 shadow-sm shadow-black/[0.02]"
    >
      <span className={`inline-grid size-9 place-items-center rounded-lg ${toneClass}`}>
        <Icon className="size-4.5" />
      </span>
      <div className="mt-3 flex items-baseline gap-1">
        <AnimatedNumber value={value} className="text-2xl font-bold tabular-nums" />
        <span className="text-sm font-medium text-muted-foreground">{suffix}</span>
      </div>
      <p className="mt-0.5 text-xs text-muted-foreground">{label}</p>
    </motion.div>
  )
}

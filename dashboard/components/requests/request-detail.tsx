'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'motion/react'
import { ArrowLeft, Check, Phone, Droplet, MapPin, User, Clock } from 'lucide-react'
import { PageHeading } from '@/components/shell/app-shell'
import { Panel, PanelHeader, Skeleton } from '@/components/ui/panel'
import { UrgencyBadge, StatusBadge } from '@/components/ui/badges'
import { getRequest, getRequestTimeline } from '@/lib/mockApi'
import { pageVariants, spring, useMotionSafe } from '@/lib/motion'
import { cn } from '@/lib/utils'

function fmtTime(ts: number | null) {
  if (!ts) return '—'
  return new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

export function RequestDetail({ id }: { id: string }) {
  const [request, setRequest] = useState<any>(null)
  const [timeline, setTimeline] = useState<any[] | null>(null)
  const variants = useMotionSafe(pageVariants)

  useEffect(() => {
    getRequest(id).then(setRequest)
    getRequestTimeline(id).then(setTimeline)
  }, [id])

  return (
    <motion.div variants={variants} initial="hidden" animate="show">
      <Link
        href="/requests"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-4" /> All requests
      </Link>

      <PageHeading
        title={request ? request.patient : 'Loading request…'}
        description={request ? `Request ${request.id} · ${request.ward ?? 'Ward'}` : undefined}
        action={
          request && (
            <div className="flex items-center gap-2">
              <StatusBadge status={request.status} />
              <UrgencyBadge level={request.urgency} />
            </div>
          )
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_minmax(0,320px)]">
        {/* Timeline */}
        <Panel animated={false}>
          <PanelHeader title="Progress timeline" subtitle="Each step timestamps as it is reached" />
          {timeline ? (
            <ol className="relative ml-1 space-y-6 pl-6">
              <span className="absolute left-[9px] top-1 h-[calc(100%-1rem)] w-px bg-border" />
              {timeline.map((step, i) => (
                <motion.li
                  key={step.key}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ ...spring, delay: i * 0.08 }}
                  className="relative"
                >
                  <span
                    className={cn(
                      'absolute -left-[26px] grid size-[19px] place-items-center rounded-full border-2',
                      step.done
                        ? 'border-success bg-success text-success-foreground'
                        : 'border-border bg-card',
                    )}
                  >
                    {step.done && <Check className="size-3" />}
                  </span>
                  <p className={cn('text-sm font-medium', !step.done && 'text-muted-foreground')}>
                    {step.label}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {step.done ? fmtTime(step.at) : 'Pending'}
                  </p>
                </motion.li>
              ))}
            </ol>
          ) : (
            <div className="space-y-5 pl-6">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-8 w-2/3" />
              ))}
            </div>
          )}
        </Panel>

        {/* Details + confirmed donor */}
        <div className="flex flex-col gap-6">
          <Panel>
            <PanelHeader title="Request details" />
            {request ? (
              <dl className="space-y-3 text-sm">
                <Row icon={Droplet} label="Blood group" value={request.group} />
                <Row icon={Droplet} label="Units needed" value={`${request.units}`} />
                <Row icon={MapPin} label="Ward" value={request.ward ?? '—'} />
                <Row icon={Clock} label="Raised" value={fmtTime(request.createdAt)} />
              </dl>
            ) : (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-5 w-full" />
                ))}
              </div>
            )}
          </Panel>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...spring, delay: 0.2 }}
            className="rounded-2xl border border-success/40 bg-success/8 p-5"
          >
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-success">
              Confirmed donor
            </p>
            <div className="flex items-center gap-3">
              <span className="grid size-11 place-items-center rounded-full bg-success text-success-foreground">
                <User className="size-5" />
              </span>
              <div>
                <p className="text-sm font-semibold">Aarav Sharma</p>
                <p className="text-xs text-muted-foreground">
                  {request?.group ?? 'O-'} · 1.2 km · 6 min ETA
                </p>
              </div>
            </div>
            <a
              href="tel:+10000000000"
              className="mt-4 flex h-10 w-full items-center justify-center gap-2 rounded-xl bg-primary text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
            >
              <Phone className="size-4" /> Call donor
            </a>
          </motion.div>
        </div>
      </div>
    </motion.div>
  )
}

function Row({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Droplet
  label: string
  value: string
}) {
  return (
    <div className="flex items-center justify-between border-b border-border pb-2.5 last:border-0 last:pb-0">
      <dt className="inline-flex items-center gap-2 text-muted-foreground">
        <Icon className="size-4" /> {label}
      </dt>
      <dd className="font-semibold">{value}</dd>
    </div>
  )
}

'use client'

import Link from 'next/link'
import { motion } from 'motion/react'
import { Droplet, Clock, ChevronRight, MapPin } from 'lucide-react'
import { UrgencyBadge, StatusBadge } from '@/components/ui/badges'
import { listItem } from '@/lib/motion'
import { cn } from '@/lib/utils'

export type RequestLike = {
  id: string
  patient: string
  group: string
  units: number
  urgency: string
  status: string
  createdAt: number
  ward?: string
}

function timeAgo(ts: number) {
  const mins = Math.round((Date.now() - ts) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const h = Math.floor(mins / 60)
  return `${h}h ${mins % 60}m ago`
}

export function RequestCard({ req }: { req: RequestLike }) {
  const critical = req.urgency === 'Critical'
  return (
    <motion.div variants={listItem} layout>
      <Link
        href={`/requests/${req.id}`}
        className={cn(
          'group flex items-center gap-4 rounded-2xl border bg-card p-4 shadow-sm shadow-black/[0.02] transition-colors hover:border-primary/40',
          critical ? 'border-critical/40' : 'border-border',
        )}
      >
        <div
          className={cn(
            'grid size-12 shrink-0 place-items-center rounded-xl text-base font-bold',
            critical ? 'bg-critical/10 text-critical' : 'bg-accent text-primary',
          )}
        >
          {req.group}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-semibold">{req.patient}</p>
            <UrgencyBadge level={req.urgency} />
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <Droplet className="size-3.5" /> {req.units} units
            </span>
            {req.ward && (
              <span className="inline-flex items-center gap-1">
                <MapPin className="size-3.5" /> {req.ward}
              </span>
            )}
            <span className="inline-flex items-center gap-1">
              <Clock className="size-3.5" /> {timeAgo(req.createdAt)}
            </span>
            <span className="font-mono text-[11px] text-muted-foreground/70">{req.id}</span>
          </div>
        </div>

        <div className="hidden sm:block">
          <StatusBadge status={req.status} />
        </div>
        <ChevronRight className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
      </Link>
    </motion.div>
  )
}

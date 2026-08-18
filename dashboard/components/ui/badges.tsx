'use client'

import { cn } from '@/lib/utils'
import { motion } from 'motion/react'
import { Activity, AlertTriangle, CheckCircle2, Search, Users } from 'lucide-react'
import { spring } from '@/lib/motion'

const urgencyStyles: Record<string, string> = {
  Critical: 'bg-critical text-critical-foreground',
  Urgent: 'bg-urgent text-urgent-foreground',
  Routine: 'bg-routine text-routine-foreground',
}

export function UrgencyBadge({ level }: { level: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide',
        urgencyStyles[level] ?? 'bg-secondary text-secondary-foreground',
      )}
    >
      {level === 'Critical' && <AlertTriangle className="size-3" />}
      {level}
    </span>
  )
}

const statusMeta: Record<string, { icon: typeof Search; className: string }> = {
  Searching: { icon: Search, className: 'bg-routine/12 text-routine' },
  'Matches Found': { icon: Users, className: 'bg-urgent/15 text-urgent-foreground' },
  'Donor Confirmed': { icon: CheckCircle2, className: 'bg-success/15 text-success' },
  Fulfilled: { icon: CheckCircle2, className: 'bg-success/15 text-success' },
}

export function StatusBadge({ status }: { status: string }) {
  const meta = statusMeta[status] ?? { icon: Activity, className: 'bg-secondary text-secondary-foreground' }
  const Icon = meta.icon
  const pulsing = status === 'Searching'
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
        meta.className,
      )}
    >
      <motion.span
        className="grid place-items-center"
        animate={pulsing ? { opacity: [1, 0.4, 1] } : { opacity: 1 }}
        transition={pulsing ? { duration: 1.4, repeat: Infinity } : spring}
      >
        <Icon className="size-3.5" />
      </motion.span>
      {status}
    </span>
  )
}

const donorStatusStyles: Record<string, string> = {
  Notified: 'bg-routine/12 text-routine',
  Viewing: 'bg-urgent/15 text-urgent-foreground',
  Accepted: 'bg-success/15 text-success',
  Declined: 'bg-muted text-muted-foreground line-through',
}

export function DonorStatusBadge({ status }: { status: string }) {
  return (
    <motion.span
      key={status}
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={spring}
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold',
        donorStatusStyles[status] ?? 'bg-secondary text-secondary-foreground',
      )}
    >
      <span
        className={cn(
          'size-1.5 rounded-full',
          status === 'Accepted' && 'bg-success',
          status === 'Viewing' && 'bg-urgent',
          status === 'Notified' && 'bg-routine',
          status === 'Declined' && 'bg-muted-foreground',
        )}
      />
      {status}
    </motion.span>
  )
}

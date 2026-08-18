'use client'

import { motion } from 'motion/react'
import { MapPin, Timer, Droplet, CalendarClock } from 'lucide-react'
import { DonorStatusBadge } from '@/components/ui/badges'
import { spring } from '@/lib/motion'
import { cn } from '@/lib/utils'

export type Donor = {
  id: string
  name: string
  distanceKm: number
  etaMin: number
  lastDonation: string
  group: string
  status: string
}

export function DonorCard({ donor, onAccept }: { donor: Donor; onAccept?: () => void }) {
  const accepted = donor.status === 'Accepted'
  const declined = donor.status === 'Declined'

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 60, scale: 0.9 }}
      animate={{
        opacity: declined ? 0.55 : 1,
        x: 0,
        scale: accepted ? 1.01 : 1,
        boxShadow: accepted
          ? '0 0 0 2px var(--success), 0 8px 30px -8px color-mix(in oklab, var(--success) 40%, transparent)'
          : '0 1px 2px rgba(0,0,0,0.03)',
      }}
      exit={{ opacity: 0, x: -40, scale: 0.9 }}
      transition={spring}
      className={cn(
        'flex items-center gap-3.5 rounded-2xl border bg-card p-3.5',
        accepted ? 'border-success/50' : 'border-border',
      )}
    >
      <div className="grid size-11 shrink-0 place-items-center rounded-xl bg-accent text-sm font-bold text-primary">
        {donor.group}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-sm font-semibold">{donor.name}</p>
          <DonorStatusBadge status={donor.status} />
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <MapPin className="size-3.5" /> {donor.distanceKm.toFixed(1)} km
          </span>
          <span className="inline-flex items-center gap-1 font-medium text-foreground">
            <Timer className="size-3.5" /> {donor.etaMin} min ETA
          </span>
          <span className="hidden items-center gap-1 sm:inline-flex">
            <CalendarClock className="size-3.5" /> {donor.lastDonation}
          </span>
        </div>
      </div>

      {donor.status === 'Viewing' && onAccept && (
        <button
          type="button"
          onClick={onAccept}
          className="hidden shrink-0 rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-colors hover:bg-primary/90 sm:block"
        >
          Confirm
        </button>
      )}
    </motion.div>
  )
}

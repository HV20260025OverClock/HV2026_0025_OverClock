'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { AnimatePresence, motion } from 'motion/react'
import { CheckCircle2, Phone, Users, Search, ArrowRight } from 'lucide-react'
import { PageHeading } from '@/components/shell/app-shell'
import { Sonar } from '@/components/matching/sonar'
import { DonorCard, type Donor } from '@/components/matching/donor-card'
import { UrgencyBadge } from '@/components/ui/badges'
import {
  getRequest,
  streamDonorMatches,
  simulateDonorProgress,
} from '@/lib/mockApi'
import { pageVariants, spring, useMotionSafe } from '@/lib/motion'
import { buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function MatchingView() {
  const params = useSearchParams()
  const reqId = params.get('req')
  const variants = useMotionSafe(pageVariants)

  const [request, setRequest] = useState<any>(null)
  const [donors, setDonors] = useState<Donor[]>([])
  const [confirmed, setConfirmed] = useState<Donor | null>(null)
  const cleanups = useRef<(() => void)[]>([])

  // Load request (from session first for instant handoff, then mock API).
  useEffect(() => {
    let cancelled = false
    try {
      const cached = sessionStorage.getItem('redaid:activeRequest')
      if (cached) {
        const parsed = JSON.parse(cached)
        if (!reqId || parsed.id === reqId) setRequest(parsed)
      }
    } catch {}
    if (reqId) {
      getRequest(reqId).then((r) => {
        if (!cancelled && r) setRequest((prev: any) => prev ?? r)
      })
    }
    return () => {
      cancelled = true
    }
  }, [reqId])

  // Stream donor matches once we have a request.
  useEffect(() => {
    if (!request) return
    const stop = streamDonorMatches(request, (donor) => {
      setDonors((prev) => {
        if (prev.some((d) => d.id === donor.id)) return prev
        const next = [...prev, donor].sort((a, b) => a.etaMin - b.etaMin)
        return next
      })
      // progress this donor: closest one accepts, others viewing/decline
      const willAccept = donor.id === 'DNR-1000'
      const cleanup = simulateDonorProgress(
        donor,
        (status) => {
          setDonors((prev) =>
            prev.map((d) => (d.id === donor.id ? { ...d, status } : d)),
          )
          if (status === 'Accepted') {
            setDonors((prev) => {
              const found = prev.find((d) => d.id === donor.id)
              if (found) setConfirmed({ ...found, status: 'Accepted' })
              return prev.filter((d) => d.id !== donor.id)
            })
          }
        },
        { accept: willAccept },
      )
      cleanups.current.push(cleanup)
    })
    cleanups.current.push(stop)
    return () => {
      cleanups.current.forEach((c) => c())
      cleanups.current = []
    }
  }, [request])

  function manualConfirm(donor: Donor) {
    setConfirmed({ ...donor, status: 'Accepted' })
    setDonors((prev) => prev.filter((d) => d.id !== donor.id))
  }

  const searching = !confirmed
  const notified = donors.length

  return (
    <motion.div variants={variants} initial="hidden" animate="show">
      <PageHeading
        title="Live donor matching"
        description={
          request
            ? `Searching eligible ${request.group} donors near St. Mary's for ${request.patient}.`
            : 'Waiting for an active request…'
        }
        action={
          request && (
            <div className="flex items-center gap-2">
              <span className="rounded-lg bg-accent px-2.5 py-1 text-sm font-bold text-primary">
                {request.group}
              </span>
              <UrgencyBadge level={request.urgency} />
            </div>
          )
        }
      />

      {!request ? (
        <div className="rounded-3xl border border-border bg-card p-10 text-center">
          <Search className="mx-auto size-8 text-muted-foreground" />
          <p className="mt-3 text-sm text-muted-foreground">
            No active request. Raise one to start matching.
          </p>
          <Link
            href="/requests/new"
            className={cn(buttonVariants(), 'mt-4 h-10 px-4')}
          >
            New request
          </Link>
        </div>
      ) : (
        <>
          {/* Confirmed donor bar */}
          <AnimatePresence>
            {confirmed && (
              <motion.div
                initial={{ opacity: 0, y: -16, height: 0 }}
                animate={{ opacity: 1, y: 0, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={spring}
                className="mb-6 overflow-hidden"
              >
                <div className="flex flex-col gap-3 rounded-2xl border border-success/50 bg-success/8 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-3">
                    <span className="grid size-11 place-items-center rounded-xl bg-success text-success-foreground">
                      <CheckCircle2 className="size-6" />
                    </span>
                    <div>
                      <p className="text-sm font-semibold">
                        Donor confirmed — {confirmed.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {confirmed.distanceKm.toFixed(1)} km away · {confirmed.etaMin} min ETA · {confirmed.group}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <a
                      href="tel:+10000000000"
                      className={cn(buttonVariants({ variant: 'outline' }), 'h-10 gap-1.5 px-3')}
                    >
                      <Phone className="size-4" /> Call
                    </a>
                    {reqId && (
                      <Link
                        href={`/requests/${reqId}`}
                        className={cn(buttonVariants(), 'h-10 gap-1.5 px-3')}
                      >
                        Track <ArrowRight className="size-4" />
                      </Link>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="grid gap-6 lg:grid-cols-[minmax(0,340px)_1fr]">
            {/* Sonar panel */}
            <div className="flex flex-col items-center gap-4 rounded-3xl border border-border bg-card p-6">
              <Sonar active={searching} />
              <div className="text-center">
                <motion.p
                  key={searching ? 'searching' : 'done'}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-sm font-semibold"
                >
                  {searching ? 'Broadcasting to nearby donors' : 'Match secured'}
                </motion.p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {searching
                    ? `${notified} donor${notified === 1 ? '' : 's'} notified`
                    : 'Search wound down'}
                </p>
              </div>
            </div>

            {/* Donor list */}
            <div className="rounded-3xl border border-border bg-card p-4 sm:p-5">
              <div className="mb-3 flex items-center gap-2 px-1">
                <Users className="size-4 text-muted-foreground" />
                <h3 className="text-sm font-semibold">
                  Matched donors {notified > 0 && <span className="text-muted-foreground">· sorted by ETA</span>}
                </h3>
              </div>

              {notified === 0 && searching ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <motion.div
                      key={i}
                      animate={{ opacity: [0.4, 0.7, 0.4] }}
                      transition={{ duration: 1.4, repeat: Infinity, delay: i * 0.2 }}
                      className="h-[68px] rounded-2xl bg-secondary"
                    />
                  ))}
                </div>
              ) : (
                <motion.div layout className="flex flex-col gap-3">
                  <AnimatePresence mode="popLayout">
                    {donors.map((d) => (
                      <DonorCard key={d.id} donor={d} onAccept={() => manualConfirm(d)} />
                    ))}
                  </AnimatePresence>
                  {notified === 0 && !searching && (
                    <p className="py-6 text-center text-sm text-muted-foreground">
                      All matched donors have been resolved.
                    </p>
                  )}
                </motion.div>
              )}
            </div>
          </div>
        </>
      )}
    </motion.div>
  )
}

'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'motion/react'
import { PlusCircle } from 'lucide-react'
import { PageHeading } from '@/components/shell/app-shell'
import { Skeleton } from '@/components/ui/panel'
import { RequestCard } from '@/components/requests/request-card'
import { getRequests } from '@/lib/mockApi'
import { listContainer, pageVariants, useMotionSafe } from '@/lib/motion'
import { buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const FILTERS = ['All', 'Searching', 'Matches Found', 'Donor Confirmed', 'Fulfilled']

export function RequestsList() {
  const [requests, setRequests] = useState<any[] | null>(null)
  const [filter, setFilter] = useState('All')
  const variants = useMotionSafe(pageVariants)

  useEffect(() => {
    getRequests().then(setRequests)
  }, [])

  const filtered =
    requests?.filter((r) => filter === 'All' || r.status === filter) ?? []

  return (
    <motion.div variants={variants} initial="hidden" animate="show">
      <PageHeading
        title="All requests"
        description="Every blood request raised across the hospital, newest first."
        action={
          <Link href="/requests/new" className={cn(buttonVariants({ size: 'lg' }), 'h-11 gap-2 px-5')}>
            <PlusCircle className="size-4.5" /> New Request
          </Link>
        }
      />

      <div className="mb-5 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              'rounded-full px-3.5 py-1.5 text-xs font-medium transition-colors',
              filter === f
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-accent hover:text-primary',
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {requests ? (
        <motion.div
          variants={listContainer}
          initial="hidden"
          animate="show"
          className="flex flex-col gap-3"
        >
          {filtered.length ? (
            filtered.map((r) => <RequestCard key={r.id} req={r} />)
          ) : (
            <p className="rounded-2xl border border-border bg-card py-10 text-center text-sm text-muted-foreground">
              No requests match this filter.
            </p>
          )}
        </motion.div>
      ) : (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-2xl" />
          ))}
        </div>
      )}
    </motion.div>
  )
}

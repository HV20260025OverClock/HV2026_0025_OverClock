'use client'

import { cn } from '@/lib/utils'
import { motion, useReducedMotion, animate } from 'motion/react'
import { useEffect, useRef } from 'react'
import { listItem } from '@/lib/motion'

export function Panel({
  className,
  children,
  animated = true,
}: {
  className?: string
  children: React.ReactNode
  animated?: boolean
}) {
  const Comp: any = animated ? motion.div : 'div'
  return (
    <Comp
      variants={animated ? listItem : undefined}
      className={cn(
        'rounded-2xl border border-border bg-card p-5 shadow-sm shadow-black/[0.02]',
        className,
      )}
    >
      {children}
    </Comp>
  )
}

export function PanelHeader({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle?: string
  action?: React.ReactNode
}) {
  return (
    <div className="mb-4 flex items-start justify-between gap-3">
      <div>
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        {subtitle && <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

/** Animated integer that counts up/rolls when its value changes. */
export function AnimatedNumber({
  value,
  className,
  format = (n: number) => Math.round(n).toString(),
}: {
  value: number
  className?: string
  format?: (n: number) => string
}) {
  const ref = useRef<HTMLSpanElement>(null)
  const reduce = useReducedMotion()
  const prev = useRef(value)

  useEffect(() => {
    const node = ref.current
    if (!node) return
    if (reduce) {
      node.textContent = format(value)
      prev.current = value
      return
    }
    const controls = animate(prev.current, value, {
      duration: 0.7,
      ease: 'easeOut',
      onUpdate: (v) => {
        node.textContent = format(v)
      },
    })
    prev.current = value
    return () => controls.stop()
  }, [value, reduce, format])

  return <span ref={ref} className={className}>{format(value)}</span>
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-secondary', className)}
      aria-hidden="true"
    />
  )
}

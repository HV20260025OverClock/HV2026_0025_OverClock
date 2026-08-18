'use client'

import { motion, useReducedMotion } from 'motion/react'
import { cn } from '@/lib/utils'
import { AnimatedNumber } from '@/components/ui/panel'

type StockItem = {
  group: string
  units: number
  threshold: number
}

/** A single blood-group ring: units on hand vs safe threshold. */
export function StockRing({ item, delay = 0 }: { item: StockItem; delay?: number }) {
  const reduce = useReducedMotion()
  const size = 92
  const stroke = 9
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r

  // Fill relative to 1.5x threshold so a healthy stock roughly fills the ring.
  const cap = item.threshold * 1.5
  const ratio = Math.min(1, item.units / cap)
  const low = item.units < item.threshold

  const ringColor = low ? 'var(--critical)' : 'var(--primary)'

  return (
    <div className="flex flex-col items-center gap-2">
      <motion.div
        className="relative grid place-items-center"
        style={{ width: size, height: size }}
        animate={
          low && !reduce
            ? { scale: [1, 1.04, 1], opacity: [1, 0.82, 1] }
            : { scale: 1, opacity: 1 }
        }
        transition={
          low && !reduce
            ? { duration: 2, repeat: Infinity, ease: 'easeInOut' }
            : { duration: 0.3 }
        }
      >
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke="var(--secondary)"
            strokeWidth={stroke}
          />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={ringColor}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={c}
            initial={{ strokeDashoffset: c }}
            animate={{ strokeDashoffset: c - c * ratio }}
            transition={
              reduce
                ? { duration: 0 }
                : { type: 'spring', stiffness: 90, damping: 18, delay }
            }
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-lg font-bold leading-none">{item.group}</span>
          <AnimatedNumber
            value={item.units}
            className={cn(
              'text-xs font-semibold tabular-nums',
              low ? 'text-critical' : 'text-muted-foreground',
            )}
          />
        </div>
      </motion.div>
      <span
        className={cn(
          'text-[11px] font-medium',
          low ? 'text-critical' : 'text-muted-foreground',
        )}
      >
        {low ? 'Below safe' : `Safe · ${item.threshold}+`}
      </span>
    </div>
  )
}

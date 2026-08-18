'use client'

import { motion, useReducedMotion } from 'motion/react'
import { Building2 } from 'lucide-react'

/** Radial sonar: center pin (hospital) + expanding concentric rings. */
export function Sonar({ active }: { active: boolean }) {
  const reduce = useReducedMotion()
  const rings = [0, 1, 2]

  return (
    <div className="relative grid aspect-square w-full max-w-xs place-items-center">
      {/* static guide rings */}
      {[0.4, 0.7, 1].map((s, i) => (
        <span
          key={`g-${i}`}
          className="absolute rounded-full border border-primary/15"
          style={{ width: `${s * 100}%`, height: `${s * 100}%` }}
        />
      ))}

      {/* pulsing sonar rings */}
      {active &&
        !reduce &&
        rings.map((i) => (
          <motion.span
            key={i}
            className="absolute rounded-full border-2 border-primary/50"
            initial={{ width: '18%', height: '18%', opacity: 0.6 }}
            animate={{ width: '100%', height: '100%', opacity: 0 }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: 'easeOut',
              delay: i * 1,
            }}
          />
        ))}

      {/* sweeping beam */}
      {active && !reduce && (
        <motion.span
          className="absolute size-[70%] rounded-full"
          style={{
            background:
              'conic-gradient(from 0deg, transparent 0deg, color-mix(in oklab, var(--primary) 22%, transparent) 40deg, transparent 60deg)',
          }}
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
        />
      )}

      {/* center pin */}
      <motion.div
        className="relative z-10 grid size-14 place-items-center rounded-full bg-primary text-primary-foreground shadow-lg shadow-primary/30"
        animate={active && !reduce ? { scale: [1, 1.06, 1] } : { scale: 1 }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
      >
        <Building2 className="size-6" />
      </motion.div>
    </div>
  )
}

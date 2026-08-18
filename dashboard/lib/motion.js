'use client'

import { useReducedMotion } from 'motion/react'

/** Shared spring — tactile, not robotic. */
export const spring = { type: 'spring', stiffness: 320, damping: 30, mass: 0.8 }
export const softSpring = { type: 'spring', stiffness: 180, damping: 24 }

/** Page transition: fade + slight vertical slide. */
export const pageVariants = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { ...spring, staggerChildren: 0.06 } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.2 } },
}

/** Stagger container + child item for lists. */
export const listContainer = {
  hidden: { opacity: 1 },
  show: { opacity: 1, transition: { staggerChildren: 0.09, delayChildren: 0.05 } },
}
export const listItem = {
  hidden: { opacity: 0, y: 16, scale: 0.98 },
  show: { opacity: 1, y: 0, scale: 1, transition: spring },
}

/** Hook that returns reduced-motion-aware variants (crossfade only). */
export function useMotionSafe(variants) {
  const reduce = useReducedMotion()
  if (!reduce) return variants
  return {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { duration: 0.25 } },
    exit: { opacity: 0, transition: { duration: 0.2 } },
  }
}

'use client'

import { motion } from 'motion/react'
import { Minus, Plus, AlertTriangle, Zap, Clock3 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { spring } from '@/lib/motion'
import { BLOOD_GROUPS } from '@/lib/mockApi'

/* Blood group picker — tappable grid of 8 chips with spring pop. */
export function BloodGroupGrid({
  value,
  onChange,
}: {
  value: string | null
  onChange: (g: string) => void
}) {
  return (
    <div className="grid grid-cols-4 gap-2.5">
      {BLOOD_GROUPS.map((g) => {
        const selected = value === g
        return (
          <motion.button
            key={g}
            type="button"
            onClick={() => onChange(g)}
            whileTap={{ scale: 0.92 }}
            animate={selected ? { scale: [1, 1.08, 1] } : { scale: 1 }}
            transition={spring}
            className={cn(
              'relative grid h-14 place-items-center rounded-xl border text-base font-bold transition-colors',
              selected
                ? 'border-primary bg-primary text-primary-foreground shadow-sm'
                : 'border-border bg-card text-foreground hover:border-primary/40 hover:bg-accent',
            )}
            aria-pressed={selected}
          >
            {g}
          </motion.button>
        )
      })}
    </div>
  )
}

/* Units stepper — +/- with number, not raw text input. */
export function UnitStepper({
  value,
  onChange,
  min = 1,
  max = 20,
}: {
  value: number
  onChange: (n: number) => void
  min?: number
  max?: number
}) {
  const set = (n: number) => onChange(Math.min(max, Math.max(min, n)))
  return (
    <div className="inline-flex items-center gap-3 rounded-xl border border-border bg-card p-1.5">
      <button
        type="button"
        onClick={() => set(value - 1)}
        disabled={value <= min}
        className="grid size-10 place-items-center rounded-lg bg-secondary text-secondary-foreground transition-colors hover:bg-primary hover:text-primary-foreground disabled:opacity-40 disabled:hover:bg-secondary disabled:hover:text-secondary-foreground"
        aria-label="Decrease units"
      >
        <Minus className="size-4" />
      </button>
      <div className="min-w-16 text-center">
        <motion.span
          key={value}
          initial={{ y: -8, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={spring}
          className="block text-3xl font-bold tabular-nums leading-none"
        >
          {value}
        </motion.span>
        <span className="text-[11px] text-muted-foreground">units</span>
      </div>
      <button
        type="button"
        onClick={() => set(value + 1)}
        disabled={value >= max}
        className="grid size-10 place-items-center rounded-lg bg-secondary text-secondary-foreground transition-colors hover:bg-primary hover:text-primary-foreground disabled:opacity-40"
        aria-label="Increase units"
      >
        <Plus className="size-4" />
      </button>
    </div>
  )
}

const URGENCY = [
  { key: 'Routine', icon: Clock3, className: 'data-[active=true]:bg-routine data-[active=true]:text-routine-foreground' },
  { key: 'Urgent', icon: Zap, className: 'data-[active=true]:bg-urgent data-[active=true]:text-urgent-foreground' },
  { key: 'Critical', icon: AlertTriangle, className: 'data-[active=true]:bg-critical data-[active=true]:text-critical-foreground' },
]

/* 3-state segmented control with animated indicator. */
export function UrgencyControl({
  value,
  onChange,
}: {
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div className="grid grid-cols-3 gap-1.5 rounded-xl border border-border bg-secondary/60 p-1.5">
      {URGENCY.map(({ key, icon: Icon, className }) => {
        const active = value === key
        return (
          <button
            key={key}
            type="button"
            data-active={active}
            onClick={() => onChange(key)}
            className={cn(
              'relative flex items-center justify-center gap-1.5 rounded-lg py-2.5 text-sm font-semibold text-muted-foreground transition-colors',
              className,
            )}
          >
            <Icon className="size-4" />
            {key}
          </button>
        )
      })}
    </div>
  )
}

/* Labeled text field with inline validation. */
export function Field({
  label,
  value,
  onChange,
  placeholder,
  error,
  as = 'input',
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  error?: string | null
  as?: 'input' | 'textarea'
}) {
  const base =
    'w-full rounded-xl border bg-card px-3.5 py-2.5 text-sm outline-none transition-colors placeholder:text-muted-foreground/60 focus:border-primary focus:ring-3 focus:ring-primary/15'
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-muted-foreground">{label}</span>
      {as === 'textarea' ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          rows={3}
          className={cn(base, 'resize-none', error ? 'border-destructive' : 'border-border')}
        />
      ) : (
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={cn(base, error ? 'border-destructive' : 'border-border')}
        />
      )}
      {error && <span className="mt-1 block text-xs text-destructive">{error}</span>}
    </label>
  )
}

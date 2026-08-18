'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { AnimatePresence, motion } from 'motion/react'
import { ChevronDown, Check, Loader2, Radar } from 'lucide-react'
import { PageHeading } from '@/components/shell/app-shell'
import {
  BloodGroupGrid,
  UnitStepper,
  UrgencyControl,
  Field,
} from '@/components/requests/form-controls'
import { createRequest } from '@/lib/mockApi'
import { pageVariants, spring, useMotionSafe } from '@/lib/motion'
import { cn } from '@/lib/utils'

type SectionKey = 'case' | 'requirement' | 'urgency'

function Section({
  index,
  title,
  hint,
  open,
  onToggle,
  complete,
  children,
}: {
  index: number
  title: string
  hint: string
  open: boolean
  onToggle: () => void
  complete: boolean
  children: React.ReactNode
}) {
  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-card">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center gap-3 px-5 py-4 text-left"
      >
        <span
          className={cn(
            'grid size-7 shrink-0 place-items-center rounded-full text-xs font-bold transition-colors',
            complete
              ? 'bg-success text-success-foreground'
              : open
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground',
          )}
        >
          {complete ? <Check className="size-4" /> : index}
        </span>
        <span className="flex-1">
          <span className="block text-sm font-semibold">{title}</span>
          <span className="block text-xs text-muted-foreground">{hint}</span>
        </span>
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={spring}>
          <ChevronDown className="size-4 text-muted-foreground" />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 260, damping: 30 }}
            className="overflow-hidden"
          >
            <div className="border-t border-border px-5 py-5">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export function NewRequestForm() {
  const router = useRouter()
  const variants = useMotionSafe(pageVariants)

  const [open, setOpen] = useState<SectionKey>('case')
  const [patient, setPatient] = useState('')
  const [ward, setWard] = useState('')
  const [group, setGroup] = useState<string | null>(null)
  const [units, setUnits] = useState(2)
  const [urgency, setUrgency] = useState('Urgent')
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const errors = useMemo(() => {
    return {
      patient: patient.trim().length < 3 ? 'Enter a patient or case name' : null,
      group: !group ? 'Select a blood group' : null,
    }
  }, [patient, group])

  const caseComplete = !errors.patient && ward.trim().length > 0
  const reqComplete = !errors.group && units > 0
  const canSubmit = !errors.patient && !errors.group && !submitting

  const critical = urgency === 'Critical'

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!canSubmit) {
      if (errors.patient) setOpen('case')
      else if (errors.group) setOpen('requirement')
      return
    }
    setSubmitting(true)
    const req = await createRequest({ patient, ward, group, units, urgency, notes })
    try {
      sessionStorage.setItem('redaid:activeRequest', JSON.stringify(req))
    } catch {}
    router.push(`/matching?req=${req.id}`)
  }

  return (
    <motion.div variants={variants} initial="hidden" animate="show">
      <PageHeading
        title="Raise a blood request"
        description="One page, no reloads. Fill what you know — matching starts the moment you submit."
      />

      {/* Ambient critical wash */}
      <motion.form
        onSubmit={handleSubmit}
        animate={{
          backgroundColor: critical ? 'color-mix(in oklab, var(--critical) 6%, transparent)' : 'rgba(0,0,0,0)',
          borderColor: critical ? 'color-mix(in oklab, var(--critical) 35%, transparent)' : 'rgba(0,0,0,0)',
        }}
        transition={{ duration: 0.4 }}
        className="mx-auto max-w-2xl space-y-3 rounded-3xl border p-1 sm:p-3"
      >
        <Section
          index={1}
          title="Patient / Case info"
          hint="Who is this for and where?"
          open={open === 'case'}
          onToggle={() => setOpen(open === 'case' ? ('' as SectionKey) : 'case')}
          complete={caseComplete}
        >
          <div className="space-y-4">
            <Field
              label="Patient or case name"
              value={patient}
              onChange={setPatient}
              placeholder="e.g. Trauma — Bay 3"
              error={patient.length > 0 ? errors.patient : null}
            />
            <Field
              label="Ward / department"
              value={ward}
              onChange={setWard}
              placeholder="e.g. Emergency"
            />
          </div>
        </Section>

        <Section
          index={2}
          title="Blood requirement"
          hint={group ? `${group} · ${units} units` : 'Pick group and units'}
          open={open === 'requirement'}
          onToggle={() => setOpen(open === 'requirement' ? ('' as SectionKey) : 'requirement')}
          complete={reqComplete}
        >
          <div className="space-y-5">
            <div>
              <span className="mb-2 block text-xs font-medium text-muted-foreground">
                Blood group
              </span>
              <BloodGroupGrid value={group} onChange={setGroup} />
              {group === null && (
                <span className="mt-2 block text-xs text-muted-foreground">
                  Tap a group to select.
                </span>
              )}
            </div>
            <div>
              <span className="mb-2 block text-xs font-medium text-muted-foreground">
                Units needed
              </span>
              <UnitStepper value={units} onChange={setUnits} />
            </div>
          </div>
        </Section>

        <Section
          index={3}
          title="Urgency & notes"
          hint={urgency}
          open={open === 'urgency'}
          onToggle={() => setOpen(open === 'urgency' ? ('' as SectionKey) : 'urgency')}
          complete
        >
          <div className="space-y-5">
            <div>
              <span className="mb-2 block text-xs font-medium text-muted-foreground">
                Urgency level
              </span>
              <UrgencyControl value={urgency} onChange={setUrgency} />
              <AnimatePresence>
                {critical && (
                  <motion.p
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="mt-2 text-xs font-medium text-critical"
                  >
                    Emergency mode — all eligible donors within range will be notified immediately.
                  </motion.p>
                )}
              </AnimatePresence>
            </div>
            <Field
              label="Notes (optional)"
              value={notes}
              onChange={setNotes}
              placeholder="Cross-match details, contact person, timing…"
              as="textarea"
            />
          </div>
        </Section>

        {/* Submit morph */}
        <div className="px-2 pb-2 pt-1">
          <motion.button
            type="submit"
            disabled={submitting}
            whileTap={{ scale: 0.98 }}
            className={cn(
              'flex h-14 w-full items-center justify-center gap-2.5 rounded-2xl text-base font-semibold text-primary-foreground shadow-sm transition-colors disabled:cursor-default',
              critical ? 'bg-critical' : 'bg-primary',
            )}
          >
            <AnimatePresence mode="wait" initial={false}>
              {submitting ? (
                <motion.span
                  key="searching"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center gap-2.5"
                >
                  <Loader2 className="size-5 animate-spin" />
                  Searching donors…
                </motion.span>
              ) : (
                <motion.span
                  key="idle"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center gap-2.5"
                >
                  <Radar className="size-5" />
                  Submit & find donors
                </motion.span>
              )}
            </AnimatePresence>
          </motion.button>
        </div>
      </motion.form>
    </motion.div>
  )
}

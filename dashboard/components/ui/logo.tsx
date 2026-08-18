import Image from 'next/image'
import { cn } from '@/lib/utils'

export function Logo({
  className,
  showWordmark = true,
  size = 36,
}: {
  className?: string
  showWordmark?: boolean
  size?: number
}) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <span
        className="relative shrink-0 overflow-hidden rounded-lg"
        style={{ width: size, height: size }}
      >
        <Image
          src="/redaid-logo.png"
          alt="RedAid logo — a red blood drop with a medical cross"
          fill
          sizes="48px"
          className="scale-[1.6] object-contain"
          priority
        />
      </span>
      {showWordmark && (
        <span className="text-lg font-bold tracking-tight leading-none">
          <span className="text-primary">RED</span>
          <span className="text-foreground">AID</span>
        </span>
      )}
    </div>
  )
}

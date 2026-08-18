'use client'

import { Area, AreaChart, CartesianGrid, XAxis } from 'recharts'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'

const chartConfig = {
  requests: { label: 'Requests', color: 'var(--chart-1)' },
  fulfilled: { label: 'Fulfilled', color: 'var(--chart-4)' },
} satisfies ChartConfig

export function TrendChart({
  data,
}: {
  data: { date: string; requests: number; fulfilled: number }[]
}) {
  return (
    <ChartContainer config={chartConfig} className="h-56 w-full">
      <AreaChart data={data} margin={{ left: 4, right: 8, top: 8 }}>
        <defs>
          <linearGradient id="fillRequests" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-requests)" stopOpacity={0.35} />
            <stop offset="100%" stopColor="var(--color-requests)" stopOpacity={0.02} />
          </linearGradient>
          <linearGradient id="fillFulfilled" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-fulfilled)" stopOpacity={0.28} />
            <stop offset="100%" stopColor="var(--color-fulfilled)" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis
          dataKey="date"
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          minTickGap={24}
          className="text-[11px]"
        />
        <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
        <Area
          type="monotone"
          dataKey="fulfilled"
          stroke="var(--color-fulfilled)"
          fill="url(#fillFulfilled)"
          strokeWidth={2}
        />
        <Area
          type="monotone"
          dataKey="requests"
          stroke="var(--color-requests)"
          fill="url(#fillRequests)"
          strokeWidth={2.2}
        />
      </AreaChart>
    </ChartContainer>
  )
}

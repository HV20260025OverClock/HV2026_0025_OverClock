import { Suspense } from 'react'
import { MatchingView } from '@/components/matching/matching-view'

export default function Page() {
  return (
    <Suspense fallback={null}>
      <MatchingView />
    </Suspense>
  )
}

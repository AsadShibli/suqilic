import { useIsFetching } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import { Spinner } from './ui'

/** Free hosting sleeps when idle; if requests hang, explain the wait instead of showing silent skeletons. */
const SLOW_AFTER_MS = 3000

export function ServerWakeBanner() {
  const fetching = useIsFetching() > 0
  const [slow, setSlow] = useState(false)

  useEffect(() => {
    if (!fetching) return
    const timer = setTimeout(() => setSlow(true), SLOW_AFTER_MS)
    return () => {
      clearTimeout(timer)
      setSlow(false)
    }
  }, [fetching])

  if (!fetching || !slow) return null
  return (
    <div
      role="status"
      className="fixed inset-x-0 bottom-0 z-50 flex items-center justify-center gap-3 border-t border-border bg-surface/95 px-4 py-3 text-sm backdrop-blur"
    >
      <Spinner className="size-4 shrink-0" />
      <span>
        <strong className="text-text">Waking the server…</strong>{' '}
        <span className="text-muted">This demo runs on free hosting that sleeps when idle. It can take up to a minute.</span>
      </span>
    </div>
  )
}

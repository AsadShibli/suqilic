import clsx from 'clsx'
import DOMPurify from 'dompurify'
import { Loader2 } from 'lucide-react'
import type { ReactNode } from 'react'

import { useSettings } from '@/api/storefront'

/** Page <title>/<meta>; React 19 hoists these into <head>. */
export function Seo({ title, description }: { title?: string; description?: string }) {
  const { data } = useSettings()
  const store = data?.store_name ?? 'Suqilic'
  const fullTitle = title ? `${title} | ${store}` : data?.seo_default_title || store
  return (
    <>
      <title>{fullTitle}</title>
      <meta name="description" content={description || data?.seo_default_description || ''} />
    </>
  )
}

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={clsx('animate-spin text-muted', className ?? 'size-6')} aria-label="Loading" />
}

export function PageLoader() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <Spinner className="size-8" />
    </div>
  )
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx('animate-pulse rounded-sm bg-surface-2', className)} />
}

export function RichText({ html, className }: { html: string; className?: string }) {
  return (
    <div
      className={clsx('prose prose-invert max-w-none prose-a:text-accent prose-img:rounded-sm', className)}
      dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }}
    />
  )
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-4 py-20 text-center">
      <p className="font-display text-3xl tracking-wide uppercase">{title}</p>
      {children}
    </div>
  )
}

export function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
      {error && <span className="mt-1 block text-xs text-danger">{error}</span>}
    </label>
  )
}

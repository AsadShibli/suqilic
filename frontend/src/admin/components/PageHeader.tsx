import type { ReactNode } from 'react'

export function PageHeader({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 className="text-2xl font-bold">{title}</h1>
      {children && <div className="flex flex-wrap gap-2">{children}</div>}
    </div>
  )
}

export function StatusPill({ value }: { value: string | boolean }) {
  const text = typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value
  const tone =
    value === true || ['active', 'delivered', 'confirmed', 'shipped'].includes(String(value))
      ? 'border-success/40 text-success'
      : value === false || ['archived', 'cancelled'].includes(String(value))
        ? 'border-danger/40 text-danger'
        : 'border-border text-muted'
  return <span className={`rounded-sm border px-2 py-0.5 text-xs font-semibold uppercase ${tone}`}>{text}</span>
}

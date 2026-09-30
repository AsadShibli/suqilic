import clsx from 'clsx'
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight } from 'lucide-react'
import type { ReactNode } from 'react'

import { Spinner } from '@/components/ui'

import type { Row } from '../api'

export type Column<T> = { key: string; label: string; render?: (row: T) => ReactNode; sortable?: boolean; className?: string }

type Props<T extends Row> = {
  rows: T[]
  columns: Column<T>[]
  loading?: boolean
  selected?: number[]
  onSelect?: (ids: number[]) => void
  onRowClick?: (row: T) => void
  ordering?: string
  onOrder?: (ordering: string) => void
  page?: number
  pageCount?: number
  onPage?: (page: number) => void
  actions?: (row: T) => ReactNode
}

export function DataTable<T extends Row>(props: Props<T>) {
  const { rows, columns, loading, selected, onSelect, onRowClick, ordering, onOrder, page = 1, pageCount = 1, onPage, actions } = props
  const allSelected = Boolean(rows.length) && rows.every((r) => selected?.includes(r.id))

  const toggle = (id: number) => onSelect?.(selected?.includes(id) ? selected.filter((x) => x !== id) : [...(selected ?? []), id])

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border text-xs tracking-wider text-muted uppercase">
            <tr>
              {onSelect && (
                <th className="w-10 p-3">
                  <input
                    type="checkbox"
                    className="accent-white"
                    checked={allSelected}
                    onChange={() => onSelect(allSelected ? [] : rows.map((r) => r.id))}
                    aria-label="Select all"
                  />
                </th>
              )}
              {columns.map((c) => (
                <th key={c.key} className={clsx('p-3 font-medium', c.className)}>
                  {c.sortable && onOrder ? (
                    <button
                      className="inline-flex items-center gap-1 uppercase hover:text-text"
                      onClick={() => onOrder(ordering === c.key ? `-${c.key}` : c.key)}
                    >
                      {c.label}
                      {ordering === c.key && <ArrowUp className="size-3" />}
                      {ordering === `-${c.key}` && <ArrowDown className="size-3" />}
                    </button>
                  ) : (
                    c.label
                  )}
                </th>
              ))}
              {actions && <th className="p-3" />}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((row) => (
              <tr
                key={row.id}
                onClick={() => onRowClick?.(row)}
                className={clsx(onRowClick && 'cursor-pointer hover:bg-surface-2')}
              >
                {onSelect && (
                  <td className="p-3" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      className="accent-white"
                      checked={selected?.includes(row.id)}
                      onChange={() => toggle(row.id)}
                      aria-label={`Select row ${row.id}`}
                    />
                  </td>
                )}
                {columns.map((c) => (
                  <td key={c.key} className={clsx('p-3', c.className)}>
                    {c.render ? c.render(row) : String(row[c.key] ?? '—')}
                  </td>
                ))}
                {actions && (
                  <td className="p-3 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                    {actions(row)}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {loading && (
        <div className="flex justify-center p-6">
          <Spinner />
        </div>
      )}
      {!loading && !rows.length && <p className="p-8 text-center text-muted">Nothing here yet.</p>}
      {onPage && pageCount > 1 && (
        <div className="flex items-center justify-end gap-3 border-t border-border p-3 text-sm text-muted">
          <button className="p-1 disabled:opacity-40" disabled={page <= 1} onClick={() => onPage(page - 1)} aria-label="Previous page">
            <ChevronLeft className="size-4" />
          </button>
          {page} / {pageCount}
          <button
            className="p-1 disabled:opacity-40"
            disabled={page >= pageCount}
            onClick={() => onPage(page + 1)}
            aria-label="Next page"
          >
            <ChevronRight className="size-4" />
          </button>
        </div>
      )}
    </div>
  )
}

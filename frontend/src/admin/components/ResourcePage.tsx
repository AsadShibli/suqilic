import { ArrowDown, ArrowUp, Download, Pencil, Plus, Trash2 } from 'lucide-react'
import { useDeferredValue, useState, type ReactNode } from 'react'

import { Drawer } from '@/components/Drawer'

import { downloadCsv, useAdminAction, useAdminList, type ListParams, type Row } from '../api'
import { confirm } from './ConfirmDialog'
import { DataTable, type Column } from './DataTable'
import type { FieldConfig } from './FormFields'
import { PageHeader } from './PageHeader'
import { RecordForm } from './RecordForm'

export type ResourcePageProps = {
  title: string
  resource: string
  columns: Column<Row>[]
  fields?: FieldConfig[]
  params?: ListParams
  defaults?: Record<string, unknown>
  searchable?: boolean
  reorderable?: boolean
  exportable?: boolean
  canCreate?: boolean
  canDelete?: boolean
  filters?: ReactNode
  rowActions?: (row: Row) => ReactNode
  onRowClick?: (row: Row) => void
  singular?: string
}

/** Generic list + create/edit drawer for a staff CRUD resource. */
export function ResourcePage(props: ResourcePageProps) {
  const { title, resource, columns, fields, params, defaults, searchable, reorderable, exportable, filters, rowActions } = props
  const canCreate = props.canCreate ?? Boolean(fields)
  const canDelete = props.canDelete ?? true
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [ordering, setOrdering] = useState<string>()
  const [selected, setSelected] = useState<number[]>([])
  const [editing, setEditing] = useState<Row | 'new' | null>(null)
  const deferredSearch = useDeferredValue(search)

  const query = { ...params, page, ordering, search: deferredSearch || undefined }
  const { data, isFetching } = useAdminList(resource, query)
  const action = useAdminAction(resource)
  const rows = data?.results ?? []
  const pageCount = Math.max(1, Math.ceil((data?.count ?? 0) / 24))

  const remove = async (ids: number[]) => {
    if (!(await confirm(`Delete ${ids.length} item${ids.length > 1 ? 's' : ''}? This cannot be undone.`))) return
    await action.mutateAsync({ path: 'bulk-delete/', body: { ids } })
    setSelected([])
  }

  const move = (index: number, delta: number) => {
    const ids = rows.map((r) => r.id)
    const [id] = ids.splice(index, 1)
    ids.splice(index + delta, 0, id)
    action.mutate({ path: 'reorder/', body: { ids } })
  }

  return (
    <>
      <PageHeader title={title}>
        {exportable && (
          <button className="btn-outline" onClick={() => downloadCsv(resource, params)}>
            <Download className="size-4" /> Export CSV
          </button>
        )}
        {canCreate && (
          <button className="btn-primary" onClick={() => setEditing('new')}>
            <Plus className="size-4" /> Add {props.singular ?? ''}
          </button>
        )}
      </PageHeader>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        {searchable && (
          <input
            className="input max-w-xs"
            placeholder="Search…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
            aria-label="Search"
          />
        )}
        {filters}
        {selected.length > 0 && (
          <button className="btn-danger ml-auto" onClick={() => remove(selected)}>
            <Trash2 className="size-4" /> Delete {selected.length}
          </button>
        )}
      </div>

      <DataTable
        rows={rows}
        columns={columns}
        loading={isFetching && !rows.length}
        selected={selected}
        onSelect={canDelete ? setSelected : undefined}
        ordering={ordering}
        onOrder={setOrdering}
        page={page}
        pageCount={pageCount}
        onPage={setPage}
        onRowClick={props.onRowClick ?? (fields ? (row) => setEditing(row) : undefined)}
        actions={(row) => (
          <div className="inline-flex items-center gap-1">
            {rowActions?.(row)}
            {reorderable && (
              <>
                <IconButton label="Move up" disabled={rows[0]?.id === row.id} onClick={() => move(rows.indexOf(row), -1)}>
                  <ArrowUp className="size-4" />
                </IconButton>
                <IconButton label="Move down" disabled={rows.at(-1)?.id === row.id} onClick={() => move(rows.indexOf(row), 1)}>
                  <ArrowDown className="size-4" />
                </IconButton>
              </>
            )}
            {fields && (
              <IconButton label="Edit" onClick={() => setEditing(row)}>
                <Pencil className="size-4" />
              </IconButton>
            )}
            {canDelete && (
              <IconButton label="Delete" onClick={() => remove([row.id])} danger>
                <Trash2 className="size-4" />
              </IconButton>
            )}
          </div>
        )}
      />

      {fields && (
        <Drawer open={editing !== null} onClose={() => setEditing(null)} title={editing === 'new' ? `New ${props.singular ?? 'item'}` : `Edit ${props.singular ?? 'item'}`}>
          <div className="p-5">
            <RecordForm
              resource={resource}
              fields={fields}
              defaults={defaults}
              record={editing === 'new' ? null : editing}
              onSaved={() => setEditing(null)}
            />
          </div>
        </Drawer>
      )}
    </>
  )
}

export function IconButton(props: { label: string; onClick: () => void; children: ReactNode; disabled?: boolean; danger?: boolean }) {
  return (
    <button
      type="button"
      title={props.label}
      aria-label={props.label}
      disabled={props.disabled}
      onClick={props.onClick}
      className={`rounded-sm p-1.5 text-muted disabled:opacity-30 ${props.danger ? 'hover:text-danger' : 'hover:text-text'}`}
    >
      {props.children}
    </button>
  )
}

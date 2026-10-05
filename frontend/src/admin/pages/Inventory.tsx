import { ArrowLeft, PackageCheck, Plus, Send, SlidersHorizontal, Trash2, XCircle } from 'lucide-react'
import { useDeferredValue, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { Drawer } from '@/components/Drawer'
import { PageLoader } from '@/components/ui'
import { api, errorMessage } from '@/lib/api'
import { formatDate, money } from '@/lib/format'

import { useAdminAction, useAdminList, useAdminRecord, useInvalidateAdmin, type Row } from '../api'
import { confirm } from '../components/ConfirmDialog'
import { PageHeader, StatusPill } from '../components/PageHeader'
import { ResourcePage } from '../components/ResourcePage'

const date = (key: string) => (r: Row) => (r[key] ? formatDate(String(r[key])) : '—')
const label = (s: string) => s.replace(/_/g, ' ')

export function Suppliers() {
  return (
    <ResourcePage
      title="Suppliers"
      singular="supplier"
      resource="suppliers"
      searchable
      columns={[
        { key: 'name', label: 'Name', sortable: true },
        { key: 'contact_name', label: 'Contact' },
        { key: 'phone', label: 'Phone' },
        { key: 'email', label: 'Email' },
        { key: 'open_purchase_orders', label: 'Open POs' },
        { key: 'is_active', label: 'Active', render: (r) => <StatusPill value={Boolean(r.is_active)} /> },
      ]}
      defaults={{ is_active: true }}
      fields={[
        { name: 'name', label: 'Name', type: 'text', required: true },
        { name: 'contact_name', label: 'Contact person', type: 'text' },
        { name: 'phone', label: 'Phone', type: 'text' },
        { name: 'email', label: 'Email', type: 'email' },
        { name: 'address', label: 'Address', type: 'textarea' },
        { name: 'notes', label: 'Notes', type: 'textarea' },
        { name: 'is_active', label: 'Active', type: 'checkbox' },
      ]}
    />
  )
}

/* ---------- Stock ledger ---------- */

const REASONS = ['sale', 'order_cancelled', 'purchase_received', 'adjustment']

type VariantOption = { id: number; label: string; sku: string | null; stock_quantity: number }

/** Search-as-you-type variant picker backed by /admin/variants/. */
function VariantPicker({ onPick, exclude = [] }: { onPick: (v: VariantOption) => void; exclude?: number[] }) {
  const [search, setSearch] = useState('')
  const deferred = useDeferredValue(search)
  const { data } = useAdminList<VariantOption & Row>('variants', { search: deferred, page_size: 8 }, deferred.length >= 2)
  const options = (data?.results ?? []).filter((v) => !exclude.includes(v.id))
  return (
    <div className="relative">
      <input className="input" placeholder="Search products or SKU…" value={search} onChange={(e) => setSearch(e.target.value)} />
      {deferred.length >= 2 && options.length > 0 && (
        <ul className="card absolute inset-x-0 top-full z-10 mt-1 max-h-64 overflow-y-auto">
          {options.map((v) => (
            <li key={v.id}>
              <button
                type="button"
                className="flex w-full justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-surface-2"
                onClick={() => {
                  onPick(v)
                  setSearch('')
                }}
              >
                <span>{v.label}</span>
                <span className="text-muted">{v.stock_quantity} in stock</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function AdjustStockForm({ onDone }: { onDone: () => void }) {
  const [variant, setVariant] = useState<VariantOption | null>(null)
  const [change, setChange] = useState('')
  const [note, setNote] = useState('')
  const adjust = useAdminAction('stock-movements')
  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!variant) return
    adjust.mutate(
      { path: 'adjust/', body: { variant: variant.id, quantity_change: Number(change), note } },
      {
        onSuccess: () => {
          toast.success('Stock adjusted')
          onDone()
        },
      },
    )
  }
  return (
    <form onSubmit={submit} className="space-y-4 p-5">
      {variant ? (
        <p className="flex items-center justify-between text-sm">
          <span>
            {variant.label} <span className="text-muted">({variant.stock_quantity} in stock)</span>
          </span>
          <button type="button" className="text-muted hover:text-text" onClick={() => setVariant(null)}>
            Change
          </button>
        </p>
      ) : (
        <VariantPicker onPick={setVariant} />
      )}
      <label className="block">
        <span className="label">Change (use a minus sign to remove stock)</span>
        <input className="input" type="number" required value={change} onChange={(e) => setChange(e.target.value)} />
      </label>
      <label className="block">
        <span className="label">Reason</span>
        <input className="input" required placeholder="e.g. Damaged in transit, stock count" value={note} onChange={(e) => setNote(e.target.value)} />
      </label>
      <button className="btn-primary w-full" disabled={!variant || !change || adjust.isPending}>
        Record adjustment
      </button>
    </form>
  )
}

export function StockMovements() {
  const [reason, setReason] = useState('')
  const [adjusting, setAdjusting] = useState(false)
  return (
    <>
      <ResourcePage
        title="Stock movements"
        resource="stock-movements"
        searchable
        exportable
        canCreate={false}
        canDelete={false}
        params={{ reason: reason || undefined }}
        filters={
          <>
            <select className="input max-w-48" value={reason} onChange={(e) => setReason(e.target.value)} aria-label="Reason">
              <option value="">All reasons</option>
              {REASONS.map((r) => (
                <option key={r} value={r}>
                  {label(r)}
                </option>
              ))}
            </select>
            <button className="btn-outline ml-auto" onClick={() => setAdjusting(true)}>
              <SlidersHorizontal className="size-4" /> Adjust stock
            </button>
          </>
        }
        columns={[
          { key: 'created_at', label: 'Date', sortable: true, render: (r) => new Date(String(r.created_at)).toLocaleString() },
          { key: 'variant_label', label: 'Product' },
          {
            key: 'quantity_change',
            label: 'Change',
            render: (r) => {
              const n = Number(r.quantity_change)
              return <span className={n > 0 ? 'text-success' : 'text-danger'}>{n > 0 ? `+${n}` : n}</span>
            },
          },
          { key: 'balance_after', label: 'Balance' },
          { key: 'reason', label: 'Reason', render: (r) => <StatusPill value={label(String(r.reason))} /> },
          {
            key: 'ref',
            label: 'Reference',
            render: (r) => String(r.order_number ?? r.purchase_order_number ?? r.note ?? '') || '—',
          },
          { key: 'created_by', label: 'By', render: (r) => String(r.created_by ?? 'System') },
        ]}
      />
      <Drawer open={adjusting} onClose={() => setAdjusting(false)} title="Adjust stock">
        {adjusting && <AdjustStockForm onDone={() => setAdjusting(false)} />}
      </Drawer>
    </>
  )
}

/* ---------- Purchase orders ---------- */

const PO_STATUSES = ['draft', 'ordered', 'partially_received', 'received', 'cancelled']

export function PurchaseOrders() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('')
  return (
    <>
      <ResourcePage
        title="Purchase orders"
        resource="purchase-orders"
        searchable
        canDelete={false}
        params={{ status: status || undefined }}
        onRowClick={(r) => navigate(String(r.id))}
        filters={
          <>
            <select className="input max-w-48" value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Status">
              <option value="">All statuses</option>
              {PO_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {label(s)}
                </option>
              ))}
            </select>
            <Link to="new" className="btn-primary ml-auto">
              <Plus className="size-4" /> New purchase order
            </Link>
          </>
        }
        columns={[
          { key: 'number', label: 'Number', sortable: true },
          { key: 'supplier_name', label: 'Supplier' },
          { key: 'status', label: 'Status', render: (r) => <StatusPill value={label(String(r.status))} /> },
          { key: 'line_count', label: 'Lines' },
          { key: 'total_cost', label: 'Total', render: (r) => money(r.total_cost as string) },
          { key: 'expected_date', label: 'Expected', sortable: true, render: date('expected_date') },
          { key: 'created_at', label: 'Created', sortable: true, render: date('created_at') },
        ]}
      />
    </>
  )
}

type PoLine = {
  id?: number
  variant: number
  variant_label: string
  sku?: string | null
  quantity_ordered: number
  quantity_received: number
  quantity_outstanding: number
  unit_cost: string
}
type PurchaseOrder = {
  id: number
  number: string
  supplier: number
  supplier_name: string
  status: string
  expected_date: string | null
  notes: string
  lines: PoLine[]
  total_cost: string
  created_by: string | null
  ordered_at: string | null
  received_at: string | null
  updated_at: string
}

export function PurchaseOrderDetail() {
  const { id } = useParams()
  const isNew = id === 'new'
  const { data: po, isLoading } = useAdminRecord<PurchaseOrder>('purchase-orders', id)
  if (!isNew && (isLoading || !po)) return <PageLoader />
  // Remount the editor whenever the server copy changes, so local edits start from fresh data.
  return <PurchaseOrderEditor key={po?.updated_at ?? 'new'} po={isNew ? undefined : po} />
}

function PurchaseOrderEditor({ po }: { po?: PurchaseOrder }) {
  const isNew = !po
  const id = po?.id
  const navigate = useNavigate()
  const invalidate = useInvalidateAdmin()
  const { data: suppliers } = useAdminList('suppliers', { page_size: 100, is_active: true })
  const action = useAdminAction<PurchaseOrder>('purchase-orders')

  const [supplier, setSupplier] = useState(po ? String(po.supplier) : '')
  const [expected, setExpected] = useState(po?.expected_date ?? '')
  const [notes, setNotes] = useState(po?.notes ?? '')
  const [lines, setLines] = useState<PoLine[]>(po?.lines ?? [])
  const [receiving, setReceiving] = useState<Record<number, string>>({})
  const [saving, setSaving] = useState(false)

  const editable = isNew || po?.status === 'draft'
  const receivable = po && ['ordered', 'partially_received'].includes(po.status)
  const total = lines.reduce((sum, l) => sum + l.quantity_ordered * Number(l.unit_cost || 0), 0)

  const updateLine = (i: number, patch: Partial<PoLine>) => setLines((ls) => ls.map((l, j) => (j === i ? { ...l, ...patch } : l)))

  const save = async () => {
    setSaving(true)
    const body = {
      supplier: Number(supplier),
      expected_date: expected || null,
      notes,
      ...(editable && {
        lines: lines.map((l) => ({ variant: l.variant, quantity_ordered: l.quantity_ordered, unit_cost: l.unit_cost })),
      }),
    }
    try {
      const { data } = isNew
        ? await api.post<PurchaseOrder>('/admin/purchase-orders/', body)
        : await api.patch<PurchaseOrder>(`/admin/purchase-orders/${id}/`, body)
      invalidate('purchase-orders')
      toast.success('Saved')
      if (isNew) navigate(`../${data.id}`, { relative: 'path', replace: true })
    } catch (e) {
      toast.error(errorMessage(e))
    } finally {
      setSaving(false)
    }
  }

  const run = (path: string, body?: unknown, message = 'Updated') =>
    action.mutate({ path: `${id}/${path}`, body }, { onSuccess: () => toast.success(message) })

  const receive = () => {
    const rows = Object.entries(receiving)
      .map(([line, qty]) => ({ line: Number(line), quantity: Number(qty) || 0 }))
      .filter((r) => r.quantity > 0)
    if (!rows.length) return toast.error('Enter a received quantity for at least one line.')
    run('receive/', { lines: rows }, 'Stock received')
  }

  return (
    <>
      <Link to=".." relative="path" className="mb-4 inline-flex items-center gap-2 text-sm text-muted hover:text-text">
        <ArrowLeft className="size-4" /> Purchase orders
      </Link>
      <PageHeader title={po ? po.number : 'New purchase order'}>
        {po && <StatusPill value={label(po.status)} />}
        {po?.status === 'draft' && (
          <button className="btn-outline" onClick={() => run('mark-ordered/', undefined, 'Marked as ordered')}>
            <Send className="size-4" /> Mark as ordered
          </button>
        )}
        {po && ['draft', 'ordered'].includes(po.status) && (
          <button
            className="btn-outline"
            onClick={async () => (await confirm(`Cancel ${po.number}?`)) && run('cancel/', undefined, 'Cancelled')}
          >
            <XCircle className="size-4" /> Cancel
          </button>
        )}
      </PageHeader>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <section className="card space-y-4 p-5">
          <h2 className="label">Lines</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-muted uppercase">
                <tr>
                  <th className="py-2">Product</th>
                  <th className="py-2">Qty</th>
                  <th className="py-2">Unit cost</th>
                  {!editable && <th className="py-2">Received</th>}
                  {receivable && <th className="py-2">Receive now</th>}
                  <th />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {lines.map((l, i) => (
                  <tr key={l.variant}>
                    <td className="py-2 pr-3">
                      {l.variant_label}
                      {l.sku && <span className="block text-xs text-muted">SKU {l.sku}</span>}
                    </td>
                    <td className="py-2 pr-3">
                      {editable ? (
                        <input
                          className="input w-20"
                          type="number"
                          min={1}
                          value={l.quantity_ordered}
                          onChange={(e) => updateLine(i, { quantity_ordered: Number(e.target.value) })}
                        />
                      ) : (
                        l.quantity_ordered
                      )}
                    </td>
                    <td className="py-2 pr-3">
                      {editable ? (
                        <input
                          className="input w-28"
                          type="number"
                          min={0}
                          step="0.01"
                          value={l.unit_cost}
                          onChange={(e) => updateLine(i, { unit_cost: e.target.value })}
                        />
                      ) : (
                        money(l.unit_cost)
                      )}
                    </td>
                    {!editable && (
                      <td className="py-2 pr-3">
                        {l.quantity_received} / {l.quantity_ordered}
                      </td>
                    )}
                    {receivable && (
                      <td className="py-2 pr-3">
                        {l.quantity_outstanding > 0 ? (
                          <input
                            className="input w-20"
                            type="number"
                            min={0}
                            max={l.quantity_outstanding}
                            placeholder={String(l.quantity_outstanding)}
                            value={receiving[l.id!] ?? ''}
                            onChange={(e) => setReceiving((r) => ({ ...r, [l.id!]: e.target.value }))}
                          />
                        ) : (
                          <span className="text-success">Done</span>
                        )}
                      </td>
                    )}
                    <td className="py-2 text-right">
                      {editable && (
                        <button
                          className="p-1.5 text-muted hover:text-danger"
                          aria-label="Remove line"
                          onClick={() => setLines((ls) => ls.filter((_, j) => j !== i))}
                        >
                          <Trash2 className="size-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!lines.length && <p className="text-sm text-muted">No lines yet. Search for a product below to add one.</p>}
          {editable && (
            <VariantPicker
              exclude={lines.map((l) => l.variant)}
              onPick={(v) =>
                setLines((ls) => [
                  ...ls,
                  { variant: v.id, variant_label: v.label, sku: v.sku, quantity_ordered: 1, quantity_received: 0, quantity_outstanding: 1, unit_cost: '0.00' },
                ])
              }
            />
          )}
          <p className="flex justify-between border-t border-border pt-3 font-semibold">
            <span>Total cost</span>
            <span>{money(total)}</span>
          </p>
          {receivable && (
            <button className="btn-primary" onClick={receive} disabled={action.isPending}>
              <PackageCheck className="size-4" /> Receive into stock
            </button>
          )}
        </section>

        <aside className="card h-fit space-y-4 p-5">
          <label className="block">
            <span className="label">Supplier</span>
            <select className="input" value={supplier} disabled={!editable} onChange={(e) => setSupplier(e.target.value)}>
              <option value="">Choose…</option>
              {suppliers?.results.map((s) => (
                <option key={s.id} value={s.id}>
                  {String(s.name)}
                </option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="label">Expected delivery</span>
            <input className="input" type="date" value={expected} onChange={(e) => setExpected(e.target.value)} />
          </label>
          <label className="block">
            <span className="label">Notes</span>
            <textarea className="input" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
          </label>
          <button className="btn-primary w-full" onClick={save} disabled={saving || !supplier || (editable && !lines.length)}>
            {saving ? 'Saving…' : 'Save'}
          </button>
          {po && (
            <dl className="space-y-1 text-xs text-muted">
              {po.created_by && <div>Created by {po.created_by}</div>}
              {po.ordered_at && <div>Ordered {formatDate(po.ordered_at)}</div>}
              {po.received_at && <div>Fully received {formatDate(po.received_at)}</div>}
            </dl>
          )}
        </aside>
      </div>
    </>
  )
}

import { ArrowLeft, ExternalLink, Star, Trash2, Wand2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { PageLoader, Spinner } from '@/components/ui'
import { api, errorMessage } from '@/lib/api'

import { useAdminAction, useAdminRecord, useInvalidateAdmin, type Row } from '../api'
import { confirm } from '../components/ConfirmDialog'
import type { FieldConfig } from '../components/FormFields'
import { PageHeader } from '../components/PageHeader'
import { RecordForm } from '../components/RecordForm'
import { IconButton } from '../components/ResourcePage'

type Image = { id: number; image: string; thumbnail: string; is_main: boolean }
type Option = { id: number; name: string; values: { id: number; value: string }[] }
type Variant = { id: number; title: string; sku: string | null; price: string; stock_quantity: number; is_active: boolean }
type AdminProduct = Row & { title: string; slug: string; status: string; images: Image[]; options: Option[]; variants: Variant[] }

const FIELDS: FieldConfig[] = [
  { name: 'title', label: 'Title', type: 'text', required: true, wide: true },
  { name: 'slug', label: 'Slug', type: 'text', help: 'Leave blank to generate from the title.' },
  {
    name: 'status',
    label: 'Status',
    type: 'select',
    options: [
      { value: 'draft', label: 'Draft' },
      { value: 'active', label: 'Active' },
      { value: 'archived', label: 'Archived' },
    ],
  },
  { name: 'base_price', label: 'Base price', type: 'number', required: true, help: 'Default price for new variants.' },
  { name: 'compare_at_price', label: 'Compare-at price', type: 'number' },
  { name: 'description', label: 'Description', type: 'richtext' },
  { name: 'collection_ids', label: 'Collections', type: 'relations', resource: 'collections', labelKey: 'title' },
  { name: 'tag_ids', label: 'Tags', type: 'relations', resource: 'tags', labelKey: 'name' },
  { name: 'video_url', label: 'How-to video URL', type: 'url', wide: true },
  { name: 'seo_title', label: 'SEO title', type: 'text' },
  { name: 'seo_description', label: 'SEO description', type: 'text' },
]

function Images({ product }: { product: AdminProduct }) {
  const resource = `products/${product.id}/images`
  const action = useAdminAction(resource)
  const invalidate = useInvalidateAdmin()
  const [uploading, setUploading] = useState(false)

  const upload = async (files: FileList | null) => {
    if (!files?.length) return
    setUploading(true)
    try {
      for (const [i, file] of [...files].entries()) {
        const form = new FormData()
        form.append('image', file)
        form.append('alt_text', product.title)
        form.append('position', String(product.images.length + i))
        if (!product.images.length && i === 0) form.append('is_main', 'true')
        await api.post(`/admin/${resource}/`, form)
      }
    } catch (e) {
      toast.error(errorMessage(e))
    } finally {
      setUploading(false)
      invalidate('products')
    }
  }

  return (
    <section className="card p-5">
      <h2 className="label">Images</h2>
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-5">
        {product.images.map((img) => (
          <div key={img.id} className="group relative aspect-square overflow-hidden rounded-sm border border-border">
            <img src={img.thumbnail || img.image} alt="" className="size-full object-cover" />
            <div className="absolute inset-x-0 bottom-0 flex justify-between bg-bg/80 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
              <IconButton label={img.is_main ? 'Main image' : 'Set as main'} onClick={() => action.mutate({ path: `${img.id}/set-main/` })}>
                <Star className={`size-4 ${img.is_main ? 'fill-current text-accent' : ''}`} />
              </IconButton>
              <IconButton
                label="Delete image"
                danger
                onClick={async () => (await confirm('Delete this image?')) && action.mutate({ path: `${img.id}/`, method: 'delete' })}
              >
                <Trash2 className="size-4" />
              </IconButton>
            </div>
            {img.is_main && <span className="absolute top-1 left-1 rounded-sm bg-accent px-1 text-[10px] font-bold text-bg">MAIN</span>}
          </div>
        ))}
        <label className="flex aspect-square cursor-pointer items-center justify-center rounded-sm border border-dashed border-border text-sm text-muted hover:border-accent">
          {uploading ? <Spinner /> : '+ Upload'}
          <input type="file" accept="image/*" multiple className="sr-only" onChange={(e) => upload(e.target.files)} />
        </label>
      </div>
    </section>
  )
}

function Options({ product }: { product: AdminProduct }) {
  const options = useAdminAction(`products/${product.id}/options`)
  const variants = useAdminAction<{ created: number }>(`products/${product.id}/variants`)

  const saveOption = (option: { id?: number; name: string; values: string[] }) =>
    options.mutate({
      path: option.id ? `${option.id}/` : '',
      method: option.id ? 'patch' : 'post',
      body: { name: option.name, values: option.values },
    })

  return (
    <section className="card space-y-4 p-5">
      <div className="flex items-center justify-between">
        <h2 className="label mb-0">Options</h2>
        <button
          className="btn-outline py-1.5"
          disabled={!product.options.length || variants.isPending}
          onClick={() => variants.mutate({ path: 'generate/' }, { onSuccess: (r) => toast.success(`${r.created} variants created`) })}
        >
          <Wand2 className="size-4" /> Generate variants
        </button>
      </div>
      {[...product.options, null].map((option) => (
        <form
          key={option?.id ?? 'new'}
          className="grid gap-2 sm:grid-cols-[160px_1fr_auto_auto]"
          onSubmit={(e) => {
            e.preventDefault()
            const form = new FormData(e.currentTarget)
            const values = String(form.get('values')).split(',').map((v) => v.trim()).filter(Boolean)
            saveOption({ id: option?.id, name: String(form.get('name')).trim(), values })
            if (!option) e.currentTarget.reset()
          }}
        >
          <input name="name" required className="input" placeholder="Option (e.g. Size)" defaultValue={option?.name} aria-label="Option name" />
          <input
            name="values"
            required
            className="input"
            placeholder="Values, comma separated (e.g. Small, Large)"
            defaultValue={option?.values.map((v) => v.value).join(', ')}
            aria-label="Option values"
          />
          <button className="btn-outline py-2">{option ? 'Save' : 'Add'}</button>
          {option ? (
            <IconButton
              label="Delete option"
              danger
              onClick={async () => (await confirm(`Delete option “${option.name}”?`)) && options.mutate({ path: `${option.id}/`, method: 'delete' })}
            >
              <Trash2 className="size-4" />
            </IconButton>
          ) : (
            <span />
          )}
        </form>
      ))}
    </section>
  )
}

function Variants({ product }: { product: AdminProduct }) {
  const action = useAdminAction(`products/${product.id}/variants`)
  const save = (variant: Variant, patch: Partial<Variant>) =>
    action.mutate({ path: `${variant.id}/`, method: 'patch', body: patch }, { onSuccess: () => toast.success('Variant saved') })

  return (
    <section className="card p-5">
      <h2 className="label">Variants</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-sm">
          <thead className="text-left text-xs text-muted uppercase">
            <tr>
              <th className="p-2">Title</th>
              <th className="p-2">SKU</th>
              <th className="p-2">Price</th>
              <th className="p-2">Stock</th>
              <th className="p-2">Active</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {product.variants.map((v) => (
              <tr key={v.id} className="border-t border-border">
                <td className="p-2">
                  <input className="input py-1.5" defaultValue={v.title} onBlur={(e) => e.target.value !== v.title && save(v, { title: e.target.value })} aria-label="Variant title" />
                </td>
                <td className="p-2">
                  <input className="input py-1.5" defaultValue={v.sku ?? ''} onBlur={(e) => e.target.value !== (v.sku ?? '') && save(v, { sku: e.target.value || null })} aria-label="SKU" />
                </td>
                <td className="p-2">
                  <input type="number" step="0.01" min={0} className="input w-24 py-1.5" defaultValue={v.price} onBlur={(e) => e.target.value !== v.price && save(v, { price: e.target.value })} aria-label="Price" />
                </td>
                <td className="p-2">
                  <input
                    type="number"
                    min={0}
                    className="input w-20 py-1.5"
                    defaultValue={v.stock_quantity}
                    onBlur={(e) => Number(e.target.value) !== v.stock_quantity && save(v, { stock_quantity: Number(e.target.value) })}
                    aria-label="Stock"
                  />
                </td>
                <td className="p-2">
                  <input type="checkbox" className="accent-white" checked={v.is_active} onChange={(e) => save(v, { is_active: e.target.checked })} aria-label="Active" />
                </td>
                <td className="p-2 text-right">
                  <IconButton
                    label="Delete variant"
                    danger
                    disabled={product.variants.length <= 1}
                    onClick={async () => (await confirm('Delete this variant?')) && action.mutate({ path: `${v.id}/`, method: 'delete' })}
                  >
                    <Trash2 className="size-4" />
                  </IconButton>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default function ProductEdit() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isNew = id === 'new'
  const { data: product, isLoading } = useAdminRecord<AdminProduct>('products', isNew ? undefined : id)

  if (!isNew && (isLoading || !product)) return <PageLoader />

  return (
    <div className="max-w-5xl">
      <Link to=".." relative="path" className="mb-4 inline-flex items-center gap-2 text-sm text-muted hover:text-text">
        <ArrowLeft className="size-4" /> Products
      </Link>
      <PageHeader title={isNew ? 'New product' : product!.title}>
        {product?.status === 'active' && (
          <a href={`/products/${product.slug}`} target="_blank" rel="noreferrer" className="btn-outline">
            <ExternalLink className="size-4" /> View
          </a>
        )}
      </PageHeader>
      <div className="space-y-6">
        <section className="card p-5">
          <RecordForm
            resource="products"
            fields={FIELDS}
            record={product}
            defaults={isNew ? { status: 'draft' } : undefined}
            submitLabel={isNew ? 'Create product' : 'Save'}
            onSaved={(row) => isNew && navigate(`../${row.id}`, { relative: 'path', replace: true })}
          />
        </section>
        {product && (
          <>
            <Images product={product} />
            <Options product={product} />
            <Variants product={product} />
          </>
        )}
      </div>
    </div>
  )
}

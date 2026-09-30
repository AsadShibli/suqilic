import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'

import { applyFieldErrors, errorMessage } from '@/lib/api'

import { useAdminSave, type Row } from '../api'
import { FormFields, type FieldConfig } from './FormFields'

type Props = {
  resource: string
  fields: FieldConfig[]
  record?: Row | null
  defaults?: Record<string, unknown>
  onSaved?: (row: Row) => void
  submitLabel?: string
}

/** Create/edit form for one record of an admin resource, driven by a field config. */
export function RecordForm({ resource, fields, record, defaults = {}, onSaved, submitLabel = 'Save' }: Props) {
  const save = useAdminSave(resource)
  const initial = () => Object.fromEntries(fields.map((f) => [f.name, record?.[f.name] ?? defaults[f.name] ?? emptyValue(f)]))
  const { register, control, handleSubmit, reset, setError, formState } = useForm<Record<string, unknown>>({
    defaultValues: initial(),
  })

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => reset(initial()), [record?.id])

  const onSubmit = handleSubmit((values) => {
    const body = { ...defaults, ...normalize(values, fields) }
    save.mutate(
      { id: record?.id, values: body },
      {
        onSuccess: (row) => onSaved?.(row),
        onError: (e) => {
          applyFieldErrors(e, setError as never)
          toast.error(errorMessage(e))
        },
      },
    )
  })

  return (
    <form onSubmit={onSubmit} className="space-y-6" noValidate>
      <FormFields fields={fields} register={register} control={control} errors={formState.errors} />
      <button className="btn-primary" disabled={save.isPending}>
        {save.isPending ? 'Saving…' : submitLabel}
      </button>
    </form>
  )
}

function emptyValue(f: FieldConfig) {
  if (f.type === 'checkbox') return false
  if (f.type === 'relations') return []
  if (f.type === 'relation' || f.type === 'image') return null
  if (f.type === 'select') return f.nullable ? '' : f.options[0]?.value
  return ''
}

/** Coerce form values to API shapes: numbers, nulls for empty optional values. */
function normalize(values: Record<string, unknown>, fields: FieldConfig[]) {
  const out: Record<string, unknown> = {}
  for (const f of fields) {
    let v = values[f.name]
    if (f.type === 'number') v = v === '' || v === null ? null : Number(v)
    if (f.type === 'select' && f.nullable && v === '') v = null
    if (f.type === 'image' && typeof v === 'string') continue // unchanged URL
    if (f.type === 'image' && v === null) continue // clearing images isn't supported via JSON; replace instead
    out[f.name] = v
  }
  return out
}

import { Controller, type Control, type FieldErrors, type UseFormRegister } from 'react-hook-form'

import { useAdminList } from '../api'
import { ImageInput } from './ImageInput'
import { RichTextEditor } from './RichTextEditor'

type Base = { name: string; label: string; help?: string; wide?: boolean; required?: boolean }

export type FieldConfig = Base &
  (
    | { type: 'text' | 'email' | 'url' | 'password' | 'number' | 'textarea' | 'checkbox' | 'image' | 'richtext' }
    | { type: 'select'; options: { value: string; label: string }[]; nullable?: boolean }
    | { type: 'relation' | 'relations'; resource: string; labelKey: string; params?: Record<string, string> }
  )

function RelationOptions({ resource, labelKey, params }: { resource: string; labelKey: string; params?: Record<string, string> }) {
  const { data } = useAdminList(resource, { page_size: 100, ...params })
  return (
    <>
      {data?.results.map((r) => (
        <option key={r.id} value={r.id}>
          {String(r[labelKey])}
        </option>
      ))}
    </>
  )
}

type Props = {
  fields: FieldConfig[]
  register: UseFormRegister<Record<string, unknown>>
  control: Control<Record<string, unknown>>
  errors: FieldErrors<Record<string, unknown>>
}

/** Render a config-driven form body. Values are plain JSON; images are File | URL string. */
export function FormFields({ fields, register, control, errors }: Props) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {fields.map((f) => {
        const error = errors[f.name]?.message as string | undefined
        const wide = f.wide || ['textarea', 'richtext', 'relations', 'image'].includes(f.type)
        const rules = f.required ? { required: `${f.label} is required` } : {}
        let input: React.ReactNode

        switch (f.type) {
          case 'checkbox':
            input = (
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" className="size-4 accent-white" {...register(f.name)} /> {f.label}
              </label>
            )
            break
          case 'textarea':
            input = <textarea rows={4} className="input" {...register(f.name, rules)} />
            break
          case 'select':
            input = (
              <select className="input" {...register(f.name, rules)}>
                {f.nullable && <option value="">—</option>}
                {f.options.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            )
            break
          case 'relation':
            input = (
              <Controller
                name={f.name}
                control={control}
                rules={rules}
                render={({ field }) => (
                  <select
                    className="input"
                    value={(field.value as number | null) ?? ''}
                    onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                  >
                    <option value="">—</option>
                    <RelationOptions resource={f.resource} labelKey={f.labelKey} params={f.params} />
                  </select>
                )}
              />
            )
            break
          case 'relations':
            input = (
              <Controller
                name={f.name}
                control={control}
                render={({ field }) => (
                  <select
                    multiple
                    className="input h-40"
                    value={((field.value as number[]) ?? []).map(String)}
                    onChange={(e) => field.onChange([...e.target.selectedOptions].map((o) => Number(o.value)))}
                  >
                    <RelationOptions resource={f.resource} labelKey={f.labelKey} params={f.params} />
                  </select>
                )}
              />
            )
            break
          case 'image':
            input = (
              <Controller
                name={f.name}
                control={control}
                rules={rules}
                render={({ field }) => <ImageInput value={field.value as string | File | null} onChange={field.onChange} />}
              />
            )
            break
          case 'richtext':
            input = (
              <Controller
                name={f.name}
                control={control}
                render={({ field }) => <RichTextEditor value={(field.value as string) ?? ''} onChange={field.onChange} />}
              />
            )
            break
          default:
            input = (
              <input
                type={f.type}
                step={f.type === 'number' ? 'any' : undefined}
                className="input"
                {...register(f.name, rules)}
              />
            )
        }

        return (
          <div key={f.name} className={wide ? 'sm:col-span-2' : undefined}>
            {f.type !== 'checkbox' && <span className="label">{f.label}</span>}
            {input}
            {f.help && <p className="mt-1 text-xs text-muted">{f.help}</p>}
            {error && <p className="mt-1 text-xs text-danger">{error}</p>}
          </div>
        )
      })}
    </div>
  )
}

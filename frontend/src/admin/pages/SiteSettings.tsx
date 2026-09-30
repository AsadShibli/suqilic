import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'

import { PageLoader } from '@/components/ui'
import { api, errorMessage } from '@/lib/api'

import { toBody } from '../api'
import { FormFields, type FieldConfig } from '../components/FormFields'
import { PageHeader } from '../components/PageHeader'

const FIELDS: FieldConfig[] = [
  { name: 'store_name', label: 'Store name', type: 'text', required: true },
  { name: 'contact_email', label: 'Contact email', type: 'email' },
  { name: 'announcement_text', label: 'Announcement bar text', type: 'text' },
  { name: 'announcement_link', label: 'Announcement link', type: 'text' },
  { name: 'announcement_active', label: 'Show announcement bar', type: 'checkbox', wide: true },
  { name: 'currency_symbol', label: 'Currency symbol', type: 'text' },
  { name: 'currency_code', label: 'Currency code', type: 'text' },
  { name: 'instagram_url', label: 'Instagram URL', type: 'url' },
  { name: 'tiktok_url', label: 'TikTok URL', type: 'url' },
  { name: 'seo_default_title', label: 'Default SEO title', type: 'text' },
  { name: 'seo_default_description', label: 'Default SEO description', type: 'text' },
  { name: 'logo', label: 'Logo', type: 'image' },
  { name: 'favicon', label: 'Favicon', type: 'image' },
]

function SettingsForm({ initial }: { initial: Record<string, unknown> }) {
  const qc = useQueryClient()
  const { register, control, handleSubmit, formState } = useForm<Record<string, unknown>>({ defaultValues: initial })

  const onSubmit = handleSubmit(async (values) => {
    const changed = Object.fromEntries(Object.entries(values).filter(([k, v]) => !(k === 'logo' || k === 'favicon') || v instanceof File))
    try {
      await api.patch('/admin/settings/', toBody(changed))
      await qc.invalidateQueries({ queryKey: ['settings'] })
      toast.success('Settings saved')
    } catch (e) {
      toast.error(errorMessage(e))
    }
  })

  return (
    <form onSubmit={onSubmit} className="card max-w-3xl space-y-6 p-6">
      <FormFields fields={FIELDS} register={register} control={control} errors={formState.errors} />
      <button className="btn-primary" disabled={formState.isSubmitting}>
        Save settings
      </button>
    </form>
  )
}

export default function SiteSettings() {
  const { data } = useQuery({
    queryKey: ['admin', 'settings'],
    queryFn: () => api.get<Record<string, unknown>>('/admin/settings/').then((r) => r.data),
  })
  return (
    <>
      <PageHeader title="Settings" />
      {data ? <SettingsForm initial={data} /> : <PageLoader />}
    </>
  )
}

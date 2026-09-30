import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { api, errorMessage } from '@/lib/api'
import type { Paginated } from '@/lib/types'

export type Row = { id: number } & Record<string, unknown>
export type ListParams = Record<string, string | number | boolean | undefined>

const base = (resource: string) => `/admin/${resource}/`

/** Build a request body: multipart when any value is a File (or explicit null for a cleared file), else JSON. */
export function toBody(values: Record<string, unknown>): FormData | Record<string, unknown> {
  const hasFile = Object.values(values).some((v) => v instanceof File)
  if (!hasFile) {
    // Image fields that weren't changed come back as URLs; don't send them in JSON.
    return Object.fromEntries(Object.entries(values).filter(([, v]) => !(typeof v === 'string' && v.startsWith('http'))))
  }
  const form = new FormData()
  for (const [key, value] of Object.entries(values)) {
    if (value === undefined || (typeof value === 'string' && value.startsWith('http'))) continue
    if (Array.isArray(value)) value.forEach((v) => form.append(key, String(v)))
    else if (value instanceof File) form.append(key, value)
    else form.append(key, value === null ? '' : String(value))
  }
  return form
}

export function useAdminList<T = Row>(resource: string, params: ListParams = {}, enabled = true) {
  return useQuery({
    queryKey: ['admin', resource, params],
    queryFn: () => api.get<Paginated<T> | T[]>(base(resource), { params }).then((r) => r.data),
    placeholderData: keepPreviousData,
    enabled,
    select: (data) => (Array.isArray(data) ? { count: data.length, next: null, previous: null, results: data } : data),
  })
}

export function useAdminRecord<T = Row>(resource: string, id: number | string | undefined) {
  return useQuery({
    queryKey: ['admin', resource, 'detail', id],
    queryFn: () => api.get<T>(`${base(resource)}${id}/`).then((r) => r.data),
    enabled: id !== undefined && id !== 'new',
  })
}

export function useInvalidateAdmin() {
  const qc = useQueryClient()
  return (resource?: string) => qc.invalidateQueries({ queryKey: resource ? ['admin', resource] : ['admin'] })
}

export function useAdminSave<T = Row>(resource: string) {
  const invalidate = useInvalidateAdmin()
  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: Record<string, unknown> }) =>
      (id ? api.patch<T>(`${base(resource)}${id}/`, toBody(values)) : api.post<T>(base(resource), toBody(values))).then(
        (r) => r.data,
      ),
    onSuccess: () => {
      invalidate(resource.split('/')[0])
      toast.success('Saved')
    },
  })
}

export function useAdminAction<T = unknown>(resource: string) {
  const invalidate = useInvalidateAdmin()
  return useMutation({
    mutationFn: ({ path, body, method = 'post' }: { path: string; body?: unknown; method?: 'post' | 'delete' | 'patch' }) =>
      api.request<T>({ url: `${base(resource)}${path}`, method, data: body }).then((r) => r.data),
    onSuccess: () => invalidate(resource.split('/')[0]),
    onError: (e) => toast.error(errorMessage(e)),
  })
}

export async function downloadCsv(resource: string, params: ListParams = {}) {
  const res = await api.get(`${base(resource)}export/`, { params, responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = Object.assign(document.createElement('a'), { href: url, download: `${resource}.csv` })
  a.click()
  URL.revokeObjectURL(url)
}

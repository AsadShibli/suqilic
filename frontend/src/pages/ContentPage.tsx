import { useMutation } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePage, useVideos } from '@/api/storefront'
import { PageLoader, RichText, Seo } from '@/components/ui'
import { VideoEmbed } from '@/components/VideoEmbed'
import { api, errorMessage } from '@/lib/api'

import NotFound from './NotFound'

function ContactForm() {
  const send = useMutation({
    mutationFn: (body: Record<string, FormDataEntryValue>) => api.post('/contact/', body),
    onSuccess: () => toast.success('Message sent — we’ll get back to you soon.'),
    onError: (e) => toast.error(errorMessage(e)),
  })
  return (
    <form
      className="mt-10 grid gap-4 sm:grid-cols-2"
      onSubmit={(e) => {
        e.preventDefault()
        const form = e.currentTarget
        send.mutate(Object.fromEntries(new FormData(form)), { onSuccess: () => form.reset() })
      }}
    >
      <input name="name" required className="input" placeholder="Name" aria-label="Name" />
      <input name="email" type="email" required className="input" placeholder="Email" aria-label="Email" />
      <input name="phone" className="input sm:col-span-2" placeholder="Phone (optional)" aria-label="Phone" />
      <textarea name="message" required rows={5} className="input sm:col-span-2" placeholder="Message" aria-label="Message" />
      <button className="btn-primary sm:col-span-2" disabled={send.isPending}>
        {send.isPending ? 'Sending…' : 'Send'}
      </button>
    </form>
  )
}

function Videos() {
  const { data: videos = [] } = useVideos()
  return (
    <div className="mt-10 grid gap-10 md:grid-cols-2">
      {videos.map((v) => (
        <div key={v.id}>
          <VideoEmbed url={v.video_url} title={v.title} />
          <p className="mt-3 font-semibold uppercase">{v.title}</p>
        </div>
      ))}
    </div>
  )
}

export default function ContentPage({ kind = 'pages' }: { kind?: 'pages' | 'policies' }) {
  const { slug = '' } = useParams()
  const { data: page, isLoading, isError } = usePage(kind, slug)
  const isVideos = slug === 'how-to-videos'

  if (isLoading && !isVideos) return <PageLoader />
  if (isError && !isVideos) return <NotFound />

  const title = page?.title ?? 'How-To Videos'
  return (
    <div className="container-page max-w-4xl py-12">
      <Seo title={title} />
      <h1 className="section-title mb-8 text-center">{title}</h1>
      {page?.body && <RichText html={page.body} />}
      {slug === 'contact-us' && <ContactForm />}
      {isVideos && <Videos />}
    </div>
  )
}

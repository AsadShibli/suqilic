/** Turn a YouTube/TikTok share URL into an embeddable one; fall back to a plain link. */
function toEmbedUrl(url: string): string | null {
  try {
    const u = new URL(url)
    if (u.hostname.includes('youtu.be')) return `https://www.youtube-nocookie.com/embed${u.pathname}`
    if (u.hostname.includes('youtube.com')) {
      const id = u.searchParams.get('v') ?? u.pathname.split('/').pop()
      return id ? `https://www.youtube-nocookie.com/embed/${id}` : null
    }
    if (u.hostname.includes('tiktok.com')) {
      const id = u.pathname.match(/video\/(\d+)/)?.[1]
      return id ? `https://www.tiktok.com/embed/v2/${id}` : null
    }
  } catch {
    return null
  }
  return null
}

export function VideoEmbed({ url, title }: { url: string; title: string }) {
  const src = toEmbedUrl(url)
  if (!src) {
    return (
      <a href={url} target="_blank" rel="noreferrer" className="btn-outline">
        Watch video
      </a>
    )
  }
  const vertical = src.includes('tiktok')
  return (
    <div className={vertical ? 'mx-auto aspect-[9/16] max-w-sm' : 'aspect-video'}>
      <iframe
        src={src}
        title={title}
        loading="lazy"
        allow="accelerometer; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
        className="card size-full"
      />
    </div>
  )
}

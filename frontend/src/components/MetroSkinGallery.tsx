import { Link } from 'react-router-dom'

const TOTAL = 47
const images = Array.from({ length: TOTAL }, (_, i) => `/metro-skin/${String(i + 1).padStart(2, '0')}.webp`)

export function MetroSkinGallery({ preview = false }: { preview?: boolean }) {
  const shown = preview ? images.slice(0, 12) : images
  return (
    <section className="container-page py-10" aria-label="Metro Skin">
      <div className="mb-6 flex items-end justify-between gap-4">
        <h2 className="section-title">Metro Skin</h2>
        {preview && (
          <Link to="/metro-skin" className="text-sm font-semibold tracking-wide uppercase underline-offset-4 hover:underline">
            View all
          </Link>
        )}
      </div>
      <ul className="columns-2 gap-3 sm:columns-3 lg:columns-4">
        {shown.map((src, i) => (
          <li key={src} className="mb-3 break-inside-avoid overflow-hidden rounded-xl border border-border">
            <img src={src} alt={`Metro skin design ${i + 1}`} loading="lazy" className="w-full" />
          </li>
        ))}
      </ul>
    </section>
  )
}

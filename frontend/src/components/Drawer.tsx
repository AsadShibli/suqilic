import clsx from 'clsx'
import { X } from 'lucide-react'
import { useEffect, type ReactNode } from 'react'
import { createPortal } from 'react-dom'

type Props = {
  open: boolean
  onClose: () => void
  title: string
  side?: 'left' | 'right' | 'top'
  children: ReactNode
  footer?: ReactNode
}

export function Drawer({ open, onClose, title, side = 'right', children, footer }: Props) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  return createPortal(
    <div className={clsx('fixed inset-0 z-50 overflow-hidden', !open && 'pointer-events-none')} aria-hidden={!open}>
      <div
        className={clsx('absolute inset-0 bg-black/70 transition-opacity', open ? 'opacity-100' : 'opacity-0')}
        onClick={onClose}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={clsx(
          'absolute flex flex-col border-border bg-surface transition-transform duration-300',
          side === 'top' && 'inset-x-0 top-0 max-h-[85vh] border-b',
          side === 'right' && 'inset-y-0 right-0 w-full max-w-md border-l',
          side === 'left' && 'inset-y-0 left-0 w-full max-w-sm border-r',
          !open && { right: 'translate-x-full', left: '-translate-x-full', top: '-translate-y-full' }[side],
        )}
      >
        <header className="flex items-center justify-between border-b border-border px-5 py-4">
          <h2 className="text-sm font-semibold tracking-widest uppercase">{title}</h2>
          <button onClick={onClose} aria-label="Close" className="p-1 text-muted hover:text-text">
            <X className="size-5" />
          </button>
        </header>
        <div className="flex-1 overflow-y-auto">{open && children}</div>
        {footer && <footer className="border-t border-border p-5">{footer}</footer>}
      </aside>
    </div>,
    document.body,
  )
}

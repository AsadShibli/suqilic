import { useEffect, useRef, useState } from 'react'

type Pending = { message: string; resolve: (ok: boolean) => void }
let open: ((p: Pending) => void) | null = null

/** Promise-based confirm: `if (await confirm('Delete?')) ...`. Render <ConfirmHost/> once. */
export const confirm = (message: string) => new Promise<boolean>((resolve) => open?.({ message, resolve }))

export function ConfirmHost() {
  const [pending, setPending] = useState<Pending | null>(null)
  const dialog = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    open = setPending
    return () => {
      open = null
    }
  }, [])

  useEffect(() => {
    if (pending) dialog.current?.showModal()
  }, [pending])

  const close = (ok: boolean) => {
    pending?.resolve(ok)
    dialog.current?.close()
    setPending(null)
  }

  return (
    <dialog
      ref={dialog}
      onCancel={() => close(false)}
      className="m-auto w-full max-w-sm rounded-sm border border-border bg-surface p-6 text-text backdrop:bg-black/70"
    >
      <p className="mb-6">{pending?.message}</p>
      <div className="flex justify-end gap-3">
        <button className="btn-outline" onClick={() => close(false)}>
          Cancel
        </button>
        <button className="btn-danger" onClick={() => close(true)} autoFocus>
          Confirm
        </button>
      </div>
    </dialog>
  )
}

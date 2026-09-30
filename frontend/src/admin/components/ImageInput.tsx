import { ImagePlus, X } from 'lucide-react'
import { useEffect, useState } from 'react'

type Props = { value: string | File | null | undefined; onChange: (v: File | null) => void; multiple?: false }

/** Click or drag-and-drop an image; shows a preview of the current URL or selected file. */
export function ImageInput({ value, onChange }: Props) {
  const [preview, setPreview] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)

  useEffect(() => {
    if (value instanceof File) {
      const url = URL.createObjectURL(value)
      setPreview(url)
      return () => URL.revokeObjectURL(url)
    }
    setPreview(value || null)
  }, [value])

  const pick = (files: FileList | null) => {
    const file = files?.[0]
    if (file?.type.startsWith('image/')) onChange(file)
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        pick(e.dataTransfer.files)
      }}
      className={`relative flex min-h-32 items-center justify-center rounded-sm border border-dashed ${dragging ? 'border-accent' : 'border-border'} bg-surface-2`}
    >
      {preview ? (
        <>
          <img src={preview} alt="" className="max-h-48 object-contain" />
          <button
            type="button"
            onClick={() => onChange(null)}
            className="absolute top-2 right-2 rounded-sm bg-bg/80 p-1"
            aria-label="Remove image"
          >
            <X className="size-4" />
          </button>
        </>
      ) : (
        <label className="flex cursor-pointer flex-col items-center gap-2 p-6 text-sm text-muted">
          <ImagePlus className="size-6" />
          Drop an image or click to upload
          <input type="file" accept="image/*" className="sr-only" onChange={(e) => pick(e.target.files)} />
        </label>
      )}
    </div>
  )
}

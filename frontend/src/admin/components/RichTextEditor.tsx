import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import { EditorContent, useEditor, type Editor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import clsx from 'clsx'
import { Bold, Heading2, ImagePlus, Italic, Link2, List, ListOrdered, Quote, Redo, Undo } from 'lucide-react'
import { useEffect } from 'react'
import { toast } from 'sonner'

import { api, errorMessage } from '@/lib/api'

async function uploadImage(editor: Editor) {
  const input = Object.assign(document.createElement('input'), { type: 'file', accept: 'image/*' })
  input.onchange = async () => {
    const file = input.files?.[0]
    if (!file) return
    const form = new FormData()
    form.append('file', file)
    try {
      const { data } = await api.post<{ url: string }>('/admin/uploads/', form)
      editor.chain().focus().setImage({ src: data.url }).run()
    } catch (e) {
      toast.error(errorMessage(e))
    }
  }
  input.click()
}

export function RichTextEditor({ value, onChange }: { value: string; onChange: (html: string) => void }) {
  const editor = useEditor({
    extensions: [StarterKit, Link.configure({ openOnClick: false }), Image],
    content: value,
    editorProps: { attributes: { class: 'prose prose-invert max-w-none min-h-40 p-3 focus:outline-none' } },
    onUpdate: ({ editor }) => onChange(editor.getHTML()),
  })

  useEffect(() => {
    if (editor && value !== editor.getHTML()) editor.commands.setContent(value, { emitUpdate: false })
  }, [editor, value])

  if (!editor) return null

  const tools = [
    { icon: Bold, label: 'Bold', run: () => editor.chain().focus().toggleBold().run(), active: editor.isActive('bold') },
    { icon: Italic, label: 'Italic', run: () => editor.chain().focus().toggleItalic().run(), active: editor.isActive('italic') },
    { icon: Heading2, label: 'Heading', run: () => editor.chain().focus().toggleHeading({ level: 2 }).run(), active: editor.isActive('heading') },
    { icon: List, label: 'Bullet list', run: () => editor.chain().focus().toggleBulletList().run(), active: editor.isActive('bulletList') },
    { icon: ListOrdered, label: 'Numbered list', run: () => editor.chain().focus().toggleOrderedList().run(), active: editor.isActive('orderedList') },
    { icon: Quote, label: 'Quote', run: () => editor.chain().focus().toggleBlockquote().run(), active: editor.isActive('blockquote') },
    {
      icon: Link2,
      label: 'Link',
      active: editor.isActive('link'),
      run: () => {
        const href = window.prompt('Link URL', editor.getAttributes('link').href ?? 'https://')
        if (href === null) return
        if (href) editor.chain().focus().extendMarkRange('link').setLink({ href }).run()
        else editor.chain().focus().unsetLink().run()
      },
    },
    { icon: ImagePlus, label: 'Image', run: () => uploadImage(editor), active: false },
    { icon: Undo, label: 'Undo', run: () => editor.chain().focus().undo().run(), active: false },
    { icon: Redo, label: 'Redo', run: () => editor.chain().focus().redo().run(), active: false },
  ]

  return (
    <div className="rounded-sm border border-border bg-surface-2 focus-within:border-accent">
      <div className="flex flex-wrap gap-1 border-b border-border p-1">
        {tools.map(({ icon: Icon, label, run, active }) => (
          <button
            key={label}
            type="button"
            title={label}
            aria-label={label}
            onClick={run}
            className={clsx('rounded-sm p-1.5 hover:bg-surface', active && 'bg-accent text-bg hover:bg-accent')}
          >
            <Icon className="size-4" />
          </button>
        ))}
      </div>
      <EditorContent editor={editor} />
    </div>
  )
}

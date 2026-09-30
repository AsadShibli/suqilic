import { KeyRound, MailOpen, UserCheck, UserX } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { Drawer } from '@/components/Drawer'
import { formatDate, money } from '@/lib/format'

import { useAdminAction, type Row } from '../api'
import { StatusPill } from '../components/PageHeader'
import { IconButton, ResourcePage } from '../components/ResourcePage'

const date = (key: string) => (r: Row) => (r[key] ? formatDate(String(r[key])) : '—')

export function Customers() {
  const action = useAdminAction('customers')
  return (
    <ResourcePage
      title="Customers"
      resource="customers"
      searchable
      canDelete={false}
      columns={[
        { key: 'email', label: 'Email' },
        { key: 'name', label: 'Name', render: (r) => `${r.first_name} ${r.last_name}`.trim() || '—' },
        { key: 'order_count', label: 'Orders', sortable: true },
        { key: 'total_spent', label: 'Spent', sortable: true, render: (r) => money(r.total_spent as string) },
        { key: 'date_joined', label: 'Joined', sortable: true, render: date('date_joined') },
        { key: 'is_active', label: 'Active', render: (r) => <StatusPill value={Boolean(r.is_active)} /> },
      ]}
      rowActions={(row) => (
        <IconButton
          label={row.is_active ? 'Deactivate' : 'Activate'}
          onClick={() => action.mutate({ path: `${row.id}/`, method: 'patch', body: { is_active: !row.is_active } })}
        >
          {row.is_active ? <UserX className="size-4" /> : <UserCheck className="size-4" />}
        </IconButton>
      )}
    />
  )
}

export function Messages() {
  const [open, setOpen] = useState<Row | null>(null)
  const action = useAdminAction('messages')
  const view = (row: Row) => {
    setOpen(row)
    if (!row.is_read) action.mutate({ path: `${row.id}/mark-read/` })
  }
  return (
    <>
      <ResourcePage
        title="Messages"
        resource="messages"
        searchable
        onRowClick={view}
        columns={[
          { key: 'is_read', label: '', render: (r) => (r.is_read ? '' : <span className="block size-2 rounded-full bg-accent" />) },
          { key: 'name', label: 'From' },
          { key: 'email', label: 'Email' },
          { key: 'message', label: 'Message', render: (r) => <span className="line-clamp-1 max-w-md">{String(r.message)}</span> },
          { key: 'created_at', label: 'Received', render: date('created_at') },
        ]}
        rowActions={(row) => (
          <IconButton label="Open" onClick={() => view(row)}>
            <MailOpen className="size-4" />
          </IconButton>
        )}
      />
      <Drawer open={Boolean(open)} onClose={() => setOpen(null)} title="Message">
        {open && (
          <div className="space-y-4 p-5">
            <p className="font-semibold">{String(open.name)}</p>
            <p className="text-sm text-muted">
              {String(open.email)} {open.phone ? `· ${open.phone}` : ''}
            </p>
            <p className="whitespace-pre-wrap">{String(open.message)}</p>
            <a href={`mailto:${open.email}`} className="btn-primary">
              Reply by email
            </a>
          </div>
        )}
      </Drawer>
    </>
  )
}

export function Subscribers() {
  return (
    <ResourcePage
      title="Newsletter subscribers"
      resource="subscribers"
      searchable
      exportable
      columns={[
        { key: 'email', label: 'Email' },
        { key: 'is_active', label: 'Active', render: (r) => <StatusPill value={Boolean(r.is_active)} /> },
        { key: 'subscribed_at', label: 'Subscribed', render: date('subscribed_at') },
      ]}
    />
  )
}

export function Staff() {
  const action = useAdminAction('staff')
  const resetPassword = (row: Row) => {
    const new_password = window.prompt(`New password for ${row.email}`)
    if (new_password)
      action.mutate(
        { path: `${row.id}/reset-password/`, body: { new_password } },
        { onSuccess: () => toast.success('Password updated') },
      )
  }
  return (
    <ResourcePage
      title="Staff"
      singular="staff member"
      resource="staff"
      searchable
      defaults={{ is_active: true }}
      columns={[
        { key: 'email', label: 'Email' },
        { key: 'name', label: 'Name', render: (r) => `${r.first_name} ${r.last_name}`.trim() || '—' },
        { key: 'is_superuser', label: 'Superuser', render: (r) => <StatusPill value={Boolean(r.is_superuser)} /> },
        { key: 'last_login', label: 'Last login', render: date('last_login') },
      ]}
      rowActions={(row) => (
        <IconButton label="Reset password" onClick={() => resetPassword(row)}>
          <KeyRound className="size-4" />
        </IconButton>
      )}
      fields={[
        { name: 'email', label: 'Email', type: 'email', required: true },
        { name: 'password', label: 'Password', type: 'password', help: 'Required for new staff; leave blank to keep.' },
        { name: 'first_name', label: 'First name', type: 'text' },
        { name: 'last_name', label: 'Last name', type: 'text' },
        { name: 'is_active', label: 'Active', type: 'checkbox' },
        { name: 'is_superuser', label: 'Superuser (can manage staff)', type: 'checkbox' },
      ]}
    />
  )
}

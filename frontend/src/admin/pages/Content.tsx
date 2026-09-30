import { Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'

import { useAdminAction, type Row } from '../api'
import type { FieldConfig } from '../components/FormFields'
import { StatusPill } from '../components/PageHeader'
import { IconButton, ResourcePage } from '../components/ResourcePage'

const thumb = (key: string) => (row: Row) =>
  row[key] ? <img src={String(row[key])} alt="" className="h-10 w-16 rounded-sm object-cover" /> : '—'

export function Tags() {
  return (
    <ResourcePage
      title="Tags"
      singular="tag"
      resource="tags"
      searchable
      columns={[{ key: 'name', label: 'Name' }, { key: 'slug', label: 'Slug' }]}
      fields={[
        { name: 'name', label: 'Name', type: 'text', required: true },
        { name: 'slug', label: 'Slug', type: 'text', help: 'Leave blank to generate.' },
      ]}
    />
  )
}

export function HomeSections() {
  const action = useAdminAction('home-sections')
  return (
    <ResourcePage
      title="Home page sections"
      singular="section"
      resource="home-sections"
      reorderable
      columns={[
        { key: 'title', label: 'Title', render: (r) => String(r.title || '(hero)') },
        { key: 'type', label: 'Type' },
        { key: 'collection_title', label: 'Collection' },
        { key: 'is_visible', label: 'Visible', render: (r) => <StatusPill value={Boolean(r.is_visible)} /> },
      ]}
      rowActions={(row) => (
        <IconButton label="Toggle visibility" onClick={() => action.mutate({ path: `${row.id}/toggle-visibility/` })}>
          {row.is_visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
        </IconButton>
      )}
      fields={[
        {
          name: 'type',
          label: 'Type',
          type: 'select',
          options: [
            { value: 'product_carousel', label: 'Product carousel' },
            { value: 'hero', label: 'Hero banner' },
          ],
        },
        { name: 'title', label: 'Title', type: 'text', help: 'e.g. TRENDiNG' },
        { name: 'collection', label: 'Collection', type: 'relation', resource: 'collections', labelKey: 'title' },
        { name: 'max_products', label: 'Max products', type: 'number' },
        { name: 'view_all_link', label: '“View all” link', type: 'text', help: 'Defaults to the collection page.', wide: true },
        { name: 'is_visible', label: 'Visible', type: 'checkbox' },
      ]}
      defaults={{ max_products: 25, is_visible: true }}
    />
  )
}

export function Banners() {
  return (
    <ResourcePage
      title="Hero banners"
      singular="banner"
      resource="hero-banners"
      reorderable
      columns={[
        { key: 'image_desktop', label: 'Image', render: thumb('image_desktop') },
        { key: 'heading', label: 'Heading' },
        { key: 'button_link', label: 'Link' },
        { key: 'is_active', label: 'Active', render: (r) => <StatusPill value={Boolean(r.is_active)} /> },
      ]}
      fields={[
        { name: 'section', label: 'Home section', type: 'relation', resource: 'home-sections', labelKey: 'type', required: true },
        { name: 'image_desktop', label: 'Desktop image', type: 'image' },
        { name: 'image_mobile', label: 'Mobile image (optional)', type: 'image' },
        { name: 'heading', label: 'Heading', type: 'text' },
        { name: 'subheading', label: 'Subheading', type: 'text' },
        { name: 'button_text', label: 'Button text', type: 'text' },
        { name: 'button_link', label: 'Button link', type: 'text' },
        { name: 'is_active', label: 'Active', type: 'checkbox' },
      ]}
      defaults={{ is_active: true }}
    />
  )
}

const MENUS = [
  { value: 'header', label: 'Header' },
  { value: 'footer', label: 'Footer' },
  { value: 'policies', label: 'Policies (footer)' },
]

export function Menus() {
  const [menu, setMenu] = useState('header')
  return (
    <ResourcePage
      key={menu}
      title="Menus"
      singular="link"
      resource="menu-items"
      params={{ menu }}
      defaults={{ menu, is_active: true }}
      filters={
        <select className="input w-auto" value={menu} onChange={(e) => setMenu(e.target.value)} aria-label="Menu">
          {MENUS.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
      }
      columns={[
        { key: 'label', label: 'Label' },
        { key: 'url', label: 'URL' },
        { key: 'is_active', label: 'Active', render: (r) => <StatusPill value={Boolean(r.is_active)} /> },
      ]}
      fields={[
        { name: 'label', label: 'Label', type: 'text', required: true },
        { name: 'url', label: 'URL', type: 'text', required: true, help: 'e.g. /collections/card-skins' },
        { name: 'parent', label: 'Parent (optional)', type: 'relation', resource: 'menu-items', labelKey: 'label', params: { menu } },
        { name: 'position', label: 'Position', type: 'number' },
        { name: 'is_active', label: 'Active', type: 'checkbox' },
      ]}
    />
  )
}

const PAGE_FIELDS: FieldConfig[] = [
  { name: 'title', label: 'Title', type: 'text', required: true },
  { name: 'slug', label: 'Slug', type: 'text', help: 'Leave blank to generate.' },
  {
    name: 'page_type',
    label: 'Type',
    type: 'select',
    options: [
      { value: 'page', label: 'Page (/pages/…)' },
      { value: 'policy', label: 'Policy (/policies/…)' },
    ],
  },
  { name: 'is_published', label: 'Published', type: 'checkbox' },
  { name: 'body', label: 'Content', type: 'richtext' },
]

export function Pages() {
  return (
    <ResourcePage
      title="Pages & policies"
      singular="page"
      resource="pages"
      searchable
      defaults={{ is_published: true }}
      columns={[
        { key: 'title', label: 'Title' },
        { key: 'slug', label: 'Slug' },
        { key: 'page_type', label: 'Type' },
        { key: 'is_published', label: 'Published', render: (r) => <StatusPill value={Boolean(r.is_published)} /> },
      ]}
      fields={PAGE_FIELDS}
    />
  )
}

export function Videos() {
  return (
    <ResourcePage
      title="How-to videos"
      singular="video"
      resource="videos"
      reorderable
      defaults={{ is_active: true }}
      columns={[
        { key: 'thumbnail', label: 'Thumb', render: thumb('thumbnail') },
        { key: 'title', label: 'Title' },
        { key: 'video_url', label: 'URL' },
        { key: 'is_active', label: 'Active', render: (r) => <StatusPill value={Boolean(r.is_active)} /> },
      ]}
      fields={[
        { name: 'title', label: 'Title', type: 'text', required: true },
        { name: 'video_url', label: 'YouTube or TikTok URL', type: 'url', required: true, wide: true },
        { name: 'product', label: 'Product (optional)', type: 'relation', resource: 'products', labelKey: 'title' },
        { name: 'is_active', label: 'Active', type: 'checkbox' },
        { name: 'thumbnail', label: 'Thumbnail', type: 'image' },
      ]}
    />
  )
}

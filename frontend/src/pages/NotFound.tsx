import { Link } from 'react-router-dom'

import { EmptyState, Seo } from '@/components/ui'

export default function NotFound() {
  return (
    <div className="smoke container-page">
      <Seo title="Not found" />
      <EmptyState title="Page not found">
        <p className="text-muted">The page you’re looking for doesn’t exist.</p>
        <Link to="/" className="btn-primary">
          Back home
        </Link>
      </EmptyState>
    </div>
  )
}

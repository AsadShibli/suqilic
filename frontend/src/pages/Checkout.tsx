import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { z } from 'zod'

import { useMyAddresses } from '@/api/account'
import { useCart, usePlaceOrder } from '@/api/cart'
import { useMoney } from '@/api/storefront'
import { EmptyState, Field, PageLoader, Seo } from '@/components/ui'
import { applyFieldErrors, errorMessage } from '@/lib/api'
import { useAuth } from '@/stores/auth'

const schema = z.object({
  full_name: z.string().trim().min(2, 'Enter your full name'),
  email: z.email('Enter a valid email'),
  phone: z.string().trim().min(5, 'Enter a phone number'),
  line1: z.string().trim().min(3, 'Enter your address'),
  line2: z.string().trim(),
  city: z.string().trim().min(2, 'Enter your city'),
  region: z.string().trim(),
  postal_code: z.string().trim(),
  country: z.string().trim().min(2, 'Enter your country'),
  customer_note: z.string().trim().max(1000),
})
type FormValues = z.infer<typeof schema>

const EMPTY: FormValues = {
  full_name: '', email: '', phone: '', line1: '', line2: '', city: '', region: '', postal_code: '', country: '',
  customer_note: '',
}

export default function Checkout() {
  const user = useAuth((s) => s.user)
  const { data: cart, isLoading } = useCart()
  const { data: addresses } = useMyAddresses()
  const placeOrder = usePlaceOrder()
  const navigate = useNavigate()
  const money = useMoney()
  const { register, handleSubmit, reset, setError, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: EMPTY,
  })

  useEffect(() => {
    if (!user) return
    const saved = addresses?.find((a) => a.is_default) ?? addresses?.[0]
    reset({
      ...EMPTY,
      full_name: `${user.first_name} ${user.last_name}`.trim(),
      email: user.email,
      phone: user.phone,
      ...(saved && { ...saved, id: undefined, is_default: undefined }),
    })
  }, [user, addresses, reset])

  const onSubmit = handleSubmit((values) =>
    placeOrder.mutate(values, {
      onSuccess: (order) => navigate(`/orders/${order.order_number}/confirmation`, { state: { order }, replace: true }),
      onError: (e) => {
        applyFieldErrors(e, setError)
        toast.error(errorMessage(e))
      },
    }),
  )

  if (isLoading) return <PageLoader />
  if (!cart?.items.length) {
    return (
      <EmptyState title="Your cart is empty">
        <Link to="/" className="btn-primary">
          Continue shopping
        </Link>
      </EmptyState>
    )
  }

  const field = (name: keyof FormValues) => ({ ...register(name), className: 'input', 'aria-invalid': Boolean(errors[name]) })

  return (
    <div className="container-page grid gap-10 py-10 lg:grid-cols-[1fr_380px]">
      <Seo title="Checkout" />
      <form onSubmit={onSubmit} className="space-y-6" noValidate>
        <div>
          <h1 className="section-title">Order request</h1>
          <p className="mt-2 text-sm text-muted">
            No online payment. Send your request and we’ll contact you to confirm and arrange delivery.
            {!user && (
              <>
                {' '}
                <Link to="/account/login?next=/checkout" className="text-text underline">
                  Log in
                </Link>{' '}
                to use saved details.
              </>
            )}
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Full name" error={errors.full_name?.message}>
            <input {...field('full_name')} autoComplete="name" />
          </Field>
          <Field label="Phone" error={errors.phone?.message}>
            <input {...field('phone')} type="tel" autoComplete="tel" />
          </Field>
          <div className="sm:col-span-2">
            <Field label="Email" error={errors.email?.message}>
              <input {...field('email')} type="email" autoComplete="email" />
            </Field>
          </div>
          <div className="sm:col-span-2">
            <Field label="Address" error={errors.line1?.message}>
              <input {...field('line1')} autoComplete="address-line1" />
            </Field>
          </div>
          <div className="sm:col-span-2">
            <Field label="Apartment, suite, etc. (optional)" error={errors.line2?.message}>
              <input {...field('line2')} autoComplete="address-line2" />
            </Field>
          </div>
          <Field label="City" error={errors.city?.message}>
            <input {...field('city')} autoComplete="address-level2" />
          </Field>
          <Field label="State / Region" error={errors.region?.message}>
            <input {...field('region')} autoComplete="address-level1" />
          </Field>
          <Field label="Postal code" error={errors.postal_code?.message}>
            <input {...field('postal_code')} autoComplete="postal-code" />
          </Field>
          <Field label="Country" error={errors.country?.message}>
            <input {...field('country')} autoComplete="country-name" />
          </Field>
          <div className="sm:col-span-2">
            <Field label="Note (optional)" error={errors.customer_note?.message}>
              <textarea {...field('customer_note')} rows={3} />
            </Field>
          </div>
        </div>
        <button className="btn-primary w-full py-4" disabled={placeOrder.isPending}>
          {placeOrder.isPending ? 'Sending…' : 'Send order request'}
        </button>
      </form>

      <aside className="card h-fit p-6">
        <h2 className="mb-4 text-sm font-semibold tracking-widest uppercase">Summary</h2>
        <ul className="space-y-3 text-sm">
          {cart.items.map((i) => (
            <li key={i.id} className="flex justify-between gap-4">
              <span className="text-muted">
                {i.quantity} × {i.product_title}
                {i.variant_title !== 'Default' && ` (${i.variant_title})`}
              </span>
              <span>{money(i.line_total)}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 flex justify-between border-t border-border pt-4 font-semibold">
          <span>Subtotal</span>
          <span>{money(cart.subtotal)}</span>
        </p>
      </aside>
    </div>
  )
}

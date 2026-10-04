import { lazy } from 'react'
import { createBrowserRouter } from 'react-router-dom'

import { ADMIN_PATH } from '@/lib/config'
import { StoreLayout } from '@/components/layout/StoreLayout'
import Home from '@/pages/Home'
import NotFound from '@/pages/NotFound'

const Collection = lazy(() => import('@/pages/Collection'))
const Product = lazy(() => import('@/pages/Product'))
const MetroSkin = lazy(() => import('@/pages/MetroSkin'))
const Search = lazy(() => import('@/pages/Search'))
const Cart = lazy(() => import('@/pages/Cart'))
const Checkout = lazy(() => import('@/pages/Checkout'))
const OrderConfirmation = lazy(() => import('@/pages/OrderConfirmation'))
const TrackOrder = lazy(() => import('@/pages/TrackOrder'))
const ContentPage = lazy(() => import('@/pages/ContentPage'))
const Account = lazy(() => import('@/pages/account/Account'))
const auth = () => import('@/pages/account/AuthPages')
const Login = lazy(() => auth().then((m) => ({ default: m.Login })))
const Register = lazy(() => auth().then((m) => ({ default: m.Register })))
const ForgotPassword = lazy(() => auth().then((m) => ({ default: m.ForgotPassword })))
const ResetPassword = lazy(() => auth().then((m) => ({ default: m.ResetPassword })))

export const router = createBrowserRouter([
  {
    element: <StoreLayout />,
    children: [
      { index: true, element: <Home /> },
      { path: 'collections/:slug', element: <Collection /> },
      { path: 'products/:slug', element: <Product /> },
      { path: 'metro-skin', element: <MetroSkin /> },
      { path: 'search', element: <Search /> },
      { path: 'cart', element: <Cart /> },
      { path: 'checkout', element: <Checkout /> },
      { path: 'orders/track', element: <TrackOrder /> },
      { path: 'orders/:number/confirmation', element: <OrderConfirmation /> },
      { path: 'pages/:slug', element: <ContentPage /> },
      { path: 'policies/:slug', element: <ContentPage kind="policies" /> },
      { path: 'account', element: <Account /> },
      { path: 'account/login', element: <Login /> },
      { path: 'account/register', element: <Register /> },
      { path: 'account/forgot-password', element: <ForgotPassword /> },
      { path: 'account/reset-password', element: <ResetPassword /> },
      { path: '*', element: <NotFound /> },
    ],
  },
  {
    path: `${ADMIN_PATH}/*`,
    lazy: () => import('@/admin/AdminApp').then((m) => ({ Component: m.default })),
  },
])

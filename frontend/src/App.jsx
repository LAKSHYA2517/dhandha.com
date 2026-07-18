import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute, AdminRoute } from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Company from './pages/Company'
import Upload from './pages/Upload'
import Rci from './pages/Rci'
import Matches from './pages/Matches'
import Admin from './pages/Admin'
import Products from './pages/Products'
import Marketplace from './pages/Marketplace'
import Orders from './pages/Orders'
import Cart from './pages/Cart'
import Checkout from './pages/Checkout'
import AuthCallback from './pages/AuthCallback'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/auth/callback" element={<AuthCallback />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/company" element={<Company />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/rci" element={<Rci />} />
          <Route path="/matches" element={<Matches />} />
          <Route path="/products" element={<Products />} />
          <Route path="/marketplace" element={<Marketplace />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route element={<AdminRoute />}>
            <Route path="/admin" element={<Admin />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

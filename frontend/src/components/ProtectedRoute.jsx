import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export function ProtectedRoute() {
  const token = useAuthStore((s) => s.token)
  return token ? <Outlet /> : <Navigate to="/login" replace />
}

export function AdminRoute() {
  const user = useAuthStore((s) => s.user)
  return user?.role === 'admin' ? <Outlet /> : <Navigate to="/dashboard" replace />
}

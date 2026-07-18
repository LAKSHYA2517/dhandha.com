import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { useAuthStore } from '../store/authStore'
import { useCartStore } from '../store/cartStore'

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/company', label: 'Company' },
  { to: '/upload', label: 'Upload' },
  { to: '/rci', label: 'RCI' },
  { to: '/matches', label: 'Matches' },
  { to: '/products', label: 'My Products' },
  { to: '/marketplace', label: 'Marketplace' },
  { to: '/orders', label: 'Orders' },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const itemCount = useCartStore((s) => s.itemCount())
  const location = useLocation()
  const navigate = useNavigate()

  async function handleLogout() {
    await supabase.auth.signOut()
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.08),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(168,85,247,0.12),_transparent_22%),linear-gradient(to_bottom,_#050505,_#0b0b0d_55%,_#050505)] text-gray-100">
      <header className="sticky top-0 z-30 border-b border-white/10 bg-black/25 backdrop-blur-2xl">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <div className="flex h-16 items-center gap-4 rounded-full border border-white/10 bg-white/5 px-4 shadow-[0_8px_30px_rgba(0,0,0,0.35)] backdrop-blur-2xl">
            <div className="flex shrink-0 items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/10 text-sm font-black text-white">
                D
              </div>
              <div className="hidden md:block leading-tight">
                <div className="text-xs uppercase tracking-[0.35em] text-gray-300">
                  Dhandha.com
                </div>
                <div className="text-sm text-gray-400">Business dashboard</div>
              </div>
            </div>

            <nav className="flex min-w-0 flex-1 flex-nowrap items-center gap-0.5 overflow-x-auto rounded-full bg-white/5 px-2 py-1 scrollbar-none">
              {navItems.map((item) => (
                <TopNavLink
                  key={item.to}
                  to={item.to}
                  isActive={matchesRoute(location.pathname, item.to)}
                >
                  {item.label}
                </TopNavLink>
              ))}

              {user?.role === 'admin' && (
                <TopNavLink to="/admin" isActive={matchesRoute(location.pathname, '/admin')}>
                  Admin
                </TopNavLink>
              )}

              <TopNavLink to="/cart" isActive={matchesRoute(location.pathname, '/cart')}>
                Cart{itemCount > 0 ? ` (${itemCount})` : ''}
              </TopNavLink>
            </nav>

            <div className="flex shrink-0 items-center gap-3">
              <span className="hidden xl:inline text-sm text-gray-400">
                {user?.name}
              </span>
              <button
                onClick={handleLogout}
                className="inline-flex items-center justify-center rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm font-medium text-white transition-all duration-300 hover:-translate-y-0.5 hover:bg-white/15 hover:shadow-md"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}

function TopNavLink({ to, isActive, children }) {
  return (
    <NavLink
      to={to}
      className={`shrink-0 rounded-full px-3 py-2 text-[13px] font-medium whitespace-nowrap transition-all duration-300 ease-out ${
        isActive
          ? 'bg-white/15 text-white shadow-lg shadow-black/20'
          : 'text-gray-300 hover:bg-white/10 hover:text-white'
      }`}
    >
      {children}
    </NavLink>
  )
}

function matchesRoute(pathname, target) {
  if (target === '/dashboard') return pathname === '/dashboard' || pathname === '/'
  return pathname === target || pathname.startsWith(`${target}/`)
}

import { useState, type ReactNode } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { notifications } from '../bankData';
import { VeriPayMark } from './VeriPayMark';

const navigation = [
  ['Dashboard', '/fi-ops', '▦'],
  ['Transactions', '/bank/transactions', '↔'],
  ['Customers', '/bank/customers', '♙'],
  ['Fraud & Alerts', '/bank/alerts', '!'],
  ['Risk Analytics', '/bank/analytics', '◒'],
];

export function BankLayout({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  const unread = notifications.filter(
    (notification) => notification.unread
  ).length;

  return (
    <div className="min-h-screen bg-[#f7fbff] text-slate-900">

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-[#29265f] text-white transition-transform lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Logo */}
        <div className="flex h-20 items-center justify-between border-b border-white/10 px-6">
          <VeriPayMark compact />

          <button
            className="text-[#fffed0] lg:hidden"
            onClick={() => setOpen(false)}
            aria-label="Close navigation"
          >
            X
          </button>
        </div>

        {/* Sidebar heading */}
        <div className="px-5 pt-6">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#fac180]">
            Financial intelligence
          </p>

          <p className="mt-1 text-sm text-[#d9ffef]">
            Bank operations
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-5">
          {navigation.map(([label, href, icon]) => (
            <NavLink
              key={href}
              to={href}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition ${
                  isActive
                    ? 'bg-[#43cddd] text-[#29265f] shadow-sm'
                    : 'text-[#e7f5ff] hover:bg-white/10 hover:text-white'
                }`
              }
            >
              <span className="grid h-7 w-7 place-items-center rounded-md bg-white/10 text-xs font-bold">
                {icon}
              </span>

              {label}
            </NavLink>
          ))}
        </nav>

        {/* Sidebar bottom */}
        <div className="border-t border-white/10 p-4">

          <Link
            to="/bank/settings"
            className="mb-4 flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-[#e7f5ff] hover:bg-white/10"
          >
            <span>⚙</span>
            Settings
          </Link>

          <div className="mb-4 flex items-center gap-2 text-xs text-[#fffed0]">
            <span className="h-2 w-2 rounded-full bg-[#43cddd]" />
            System operational
          </div>

          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-full bg-[#43cddd] font-bold text-[#29265f]">
              AM
            </div>

            <div>
              <p className="text-sm font-semibold">
                Avery Morgan
              </p>

              <p className="text-xs text-[#cbeeff]">
                Risk Manager
              </p>
            </div>
          </div>

          <button
            onClick={() => navigate('/login')}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-[#43cddd] px-3 py-2.5 text-sm font-bold text-[#29265f] shadow-sm transition hover:bg-[#6edbea]"
          >
            <span aria-hidden="true">↪</span>
            Log out
          </button>
        </div>
      </aside>

      {/* Mobile overlay */}
      {open && (
        <button
          className="fixed inset-0 z-20 bg-slate-950/40 lg:hidden"
          onClick={() => setOpen(false)}
          aria-label="Close navigation overlay"
        />
      )}

      {/* Main area */}
      <div className="lg:pl-64">

        {/* Header */}
        <header className="sticky top-0 z-10 flex h-[72px] items-center justify-between border-b border-[#43cddd]/35 bg-white/95 px-5 backdrop-blur md:px-8">

          {/* Search */}
          <div className="flex items-center gap-4">

            <button
              className="rounded-md border border-[#007064]/25 bg-white px-3 py-2 text-sm lg:hidden"
              onClick={() => setOpen(true)}
              aria-label="Open navigation"
            >
              Menu
            </button>

            {searchOpen ? (
              <div className="flex items-center gap-2">

                <input
                  autoFocus
                  className="w-52 rounded-md border border-[#007064]/30 bg-white px-3 py-2 text-sm outline-none focus:border-[#00a79d] md:w-80"
                  placeholder="Search transactions..."
                />

                <button
                  className="text-sm font-semibold text-[#007064]"
                  onClick={() => setSearchOpen(false)}
                >
                  Close
                </button>

              </div>
            ) : (
              <button
                className="rounded-md border border-[#007064]/25 bg-white px-3 py-2 text-sm font-semibold text-[#007064] hover:bg-[#fffed0]"
                onClick={() => setSearchOpen(true)}
              >
                Search
              </button>
            )}
          </div>

          {/* User area */}
          <div className="flex items-center gap-3 text-sm">

            <Link
              to="/bank/notifications"
              aria-label={`${unread} unread notifications`}
              className="relative grid h-10 w-10 place-items-center rounded-full border border-[#2e2c83]/20 bg-white text-[#2e2c83] hover:bg-[#43cddd]/15"
            >
              <span aria-hidden="true" className="text-lg">
                🔔
              </span>

              {unread > 0 && (
                <span className="absolute -right-1 -top-1 grid h-5 min-w-5 place-items-center rounded-full bg-[#fac180] px-1 text-[10px] font-bold text-[#29265f]">
                  {unread}
                </span>
              )}
            </Link>

            <div className="hidden h-6 w-px bg-[#fac180] md:block" />

            <div className="hidden text-right md:block">
              <p className="font-semibold">
                Avery Morgan
              </p>

              <p className="text-xs text-slate-500">
                Risk Manager
              </p>
            </div>

            <div className="grid h-9 w-9 place-items-center rounded-full bg-[#2e2c83] text-xs font-bold text-white">
              AM
            </div>

          </div>
        </header>

        {/* Page content */}
        {children}

      </div>
    </div>
  );
}
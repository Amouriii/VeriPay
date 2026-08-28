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
    <div className="min-h-screen bg-[#f5f6fb] text-slate-900">

      {/* Sidebar — dark ops console, deliberately unlike the light customer portal */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-[224px] flex-col bg-[#1b1a3d] text-white transition-transform lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand accent strip: indigo -> amber marks this as the ops console */}
        <div className="h-1 w-full shrink-0 bg-gradient-to-r from-[#8b8ff2] via-[#43cddd] to-[#fac180]" />

        {/* Logo */}
        <div className="flex h-[71px] items-center justify-between border-b border-white/10 px-6">
          <VeriPayMark compact variant="indigo" />

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
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#fac180]">
            FI Operations Console
          </span>

          <p className="mt-2 text-sm text-[#cdd0ff]">
            Institutional risk &amp; fraud monitoring
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-3">
          {navigation.map(([label, href, icon]) => (
            <NavLink
              key={href}
              to={href}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? 'bg-[#8b8ff2] text-[#1b1a3d] shadow-sm'
                    : 'text-[#dfe1ff] hover:bg-white/10 hover:text-white'
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
<div className="shrink-0 border-t border-white/10 bg-[#1b1a3d] px-3 py-1.5">
  <Link
    to="/bank/settings"
    className="mb-2 flex items-center gap-3 rounded-md px-2 py-1.5 text-sm text-[#dfe1ff] hover:bg-white/10"
  >
    <span>⚙</span>
    Settings
  </Link>

  <div className="mb-2 flex items-center gap-2 px-2 text-[11px] text-[#fac180]">
    <span className="h-2 w-2 rounded-full bg-[#43cddd]" />
    System operational
  </div>

  <Link
    to="/bank/profile"
    className="mb-2 flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-white/10"
  >
    <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[#8b8ff2] text-xs font-bold text-[#1b1a3d]">
      AM
    </div>

    <div className="min-w-0">
      <p className="truncate text-xs font-semibold text-white">
        Avery Morgan
      </p>
      <p className="truncate text-[10px] text-[#cdd0ff]">
        Risk Manager
      </p>
    </div>
  </Link>

  <button
    type="button"
    onClick={() => navigate('/login', { replace: true })}
    className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#8b8ff2] px-3 py-2 text-sm font-bold text-[#1b1a3d] transition hover:bg-[#a5a8f7]"
  >
    <span aria-hidden="true">↪</span>
    <span>Log out</span>
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
      <div className="lg:pl-[224px]">

        {/* Header — solid dark ops bar, unlike the customer portal's light translucent header */}
        <header className="sticky top-0 z-10 flex h-[72px] items-center justify-between border-b border-black/10 bg-[#242154] px-5 text-white md:px-8">

          {/* Search */}
          <div className="flex items-center gap-4">

            <button
              className="rounded-md border border-white/20 bg-white/5 px-3 py-2 text-sm lg:hidden"
              onClick={() => setOpen(true)}
              aria-label="Open navigation"
            >
              Menu
            </button>

            {searchOpen ? (
              <div className="flex items-center gap-2">

                <input
                  autoFocus
                  className="w-52 rounded-md border border-white/20 bg-white/10 px-3 py-2 text-sm text-white outline-none placeholder:text-white/50 focus:border-[#43cddd] md:w-80"
                  placeholder="Search transactions..."
                />

                <button
                  className="text-sm font-semibold text-[#43cddd]"
                  onClick={() => setSearchOpen(false)}
                >
                  Close
                </button>

              </div>
            ) : (
              <button
                className="rounded-md border border-white/20 bg-white/5 px-3 py-2 text-sm font-semibold text-[#e7f5ff] hover:bg-white/10"
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
              className="relative grid h-10 w-10 place-items-center rounded-full border border-white/15 bg-white/5 text-white hover:bg-white/10"
            >
              <span aria-hidden="true" className="text-lg">
                🔔
              </span>

              {unread > 0 && (
                <span className="absolute -right-1 -top-1 grid h-5 min-w-5 place-items-center rounded-full bg-[#fac180] px-1 text-[10px] font-bold text-[#1b1a3d]">
                  {unread}
                </span>
              )}
            </Link>

            <div className="hidden h-6 w-px bg-white/15 md:block" />

            <div className="hidden text-right md:block">
              <p className="font-semibold">
                Avery Morgan
              </p>

              <p className="text-xs text-[#cdd0ff]">
                Risk Manager
              </p>
            </div>

            <div className="grid h-9 w-9 place-items-center rounded-full bg-[#8b8ff2] text-xs font-bold text-[#1b1a3d]">
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
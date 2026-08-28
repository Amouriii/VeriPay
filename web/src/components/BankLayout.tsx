import { useEffect, useState, type ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { notifications } from '../bankData';

const navigation = [
  ['Dashboard', '/fi-ops'], ['Transactions', '/bank/transactions'], ['Fraud & Alerts', '/bank/alerts'],
  ['Risk Analytics', '/bank/analytics'], ['Customers', '/bank/customers'], ['Merchants', '/bank/merchants'],
  ['Fraud Policies', '/bank/policies'], ['AI Models', '/bank/models'], ['Reports', '/bank/reports'],
  ['Audit Logs', '/bank/audit'], ['Settings', '/bank/settings'],
] as const;

type ThemeMode = 'light' | 'dark';

function initialTheme(): ThemeMode {
  if (typeof window === 'undefined') return 'light';
  const stored = window.localStorage.getItem('veripay-theme');
  if (stored === 'light' || stored === 'dark') return stored;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function SunIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="4.5" />
      <path d="M12 2.5v2.4M12 19.1v2.4M2.5 12h2.4M19.1 12h2.4M5.2 5.2l1.7 1.7M17.1 17.1l1.7 1.7M18.8 5.2l-1.7 1.7M6.9 17.1l-1.7 1.7" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20.6 14.6A8.6 8.6 0 0 1 9.4 3.4a.7.7 0 0 0-.9-.9 9.9 9.9 0 1 0 13 13 .7.7 0 0 0-.9-.9Z" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.8-3.8" />
    </svg>
  );
}

function BellIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 8-3 8h18s-3-1-3-8" />
      <path d="M13.7 20a2 2 0 0 1-3.4 0" />
    </svg>
  );
}

export function BankLayout({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [theme, setTheme] = useState<ThemeMode>(initialTheme);
  const unread = notifications.filter((notification) => notification.unread).length;

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    try {
      window.localStorage.setItem('veripay-theme', theme);
    } catch {
      // Storage may be unavailable (private mode); theme still applies for the session.
    }
  }, [theme]);

  return (
    <div className="min-h-screen text-ink">
      <aside
        className={`glass-chrome fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-chrome-hairline transition-transform duration-300 lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex h-16 items-center gap-3 border-b border-separator px-5">
          <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-violet-600 text-sm font-bold text-white shadow-[0_4px_14px_rgb(79_70_229/0.4)]">V</div>
          <div>
            <p className="text-[17px] font-semibold tracking-tight">VeriPay</p>
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-ink-subtle">Bank Console</p>
          </div>
          <button className="glass-field ml-auto grid h-8 w-8 place-items-center rounded-full text-ink-muted lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation">✕</button>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {navigation.map(([label, href]) => (
            <NavLink
              key={href}
              to={href}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `block rounded-lg px-3 py-2 text-[13px] font-medium transition ${isActive ? 'bg-accent text-white shadow-[0_6px_18px_rgb(var(--accent)/0.35)]' : 'text-ink-muted hover:bg-ink/5 hover:text-ink dark:hover:bg-white/10'}`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-separator p-4">
          <div className="mb-4 flex items-center gap-2 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />System status: Operational
          </div>
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 text-xs font-semibold text-white ring-2 ring-white/70 dark:ring-white/10">AM</div>
            <div>
              <p className="text-[13px] font-semibold">Avery Morgan</p>
              <p className="text-xs text-ink-subtle">Risk Manager</p>
            </div>
          </div>
          <button className="glass-field mt-4 w-full rounded-lg py-2 text-center text-xs font-medium text-ink-muted hover:text-ink">Log out</button>
        </div>
      </aside>
      {open && <button className="fixed inset-0 z-20 bg-slate-950/30 backdrop-blur-sm lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation overlay" />}
      <div className="lg:pl-64">
        <header className="glass-chrome sticky top-0 z-20 border-b border-chrome-hairline">
          <div className="flex h-16 items-center justify-between px-5 md:px-8">
            <div className="flex items-center gap-4">
              <button className="glass-field grid h-9 w-9 place-items-center rounded-full text-ink-muted lg:hidden" onClick={() => setOpen(true)} aria-label="Open navigation">☰</button>
              {searchOpen ? (
                <input
                  autoFocus
                  className="glass-field w-52 rounded-full px-4 py-2 text-sm md:w-80"
                  placeholder="Search transactions, customers..."
                  onBlur={() => setSearchOpen(false)}
                />
              ) : (
                <button className="glass-field flex items-center gap-2 rounded-full px-3.5 py-2 text-sm text-ink-muted transition hover:text-ink" onClick={() => setSearchOpen(true)}>
                  <SearchIcon />
                  <span className="hidden sm:inline">Search</span>
                  <span className="hidden rounded-full bg-ink/[0.06] px-2 py-0.5 text-[10px] font-semibold text-ink-subtle dark:bg-white/10 sm:inline">⌘K</span>
                </button>
              )}
            </div>
            <div className="flex items-center gap-3 text-sm">
              <button
                className="glass-field grid h-9 w-9 place-items-center rounded-full text-ink-muted transition hover:text-ink"
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} appearance`}
                title={theme === 'dark' ? 'Switch to light appearance' : 'Switch to dark appearance'}
              >
                {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
              </button>
              <button className="glass-field relative grid h-9 w-9 place-items-center rounded-full text-ink-muted transition hover:text-ink" aria-label={`${unread} unread notifications`}>
                <BellIcon />
                {unread > 0 && <span className="absolute -right-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white shadow-sm">{unread}</span>}
              </button>
              <button className="hidden text-[13px] font-medium text-ink-muted transition hover:text-ink md:block">Help</button>
              <div className="hidden h-6 w-px bg-separator md:block" />
              <div className="hidden text-right md:block">
                <p className="text-[13px] font-semibold leading-4">Avery Morgan</p>
                <p className="text-xs text-ink-subtle">Risk Manager</p>
              </div>
              <div className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 text-xs font-semibold text-white ring-2 ring-white/70 dark:ring-white/10">AM</div>
            </div>
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}

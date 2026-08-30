import { type ReactNode } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { useHealth } from '../api/analyst';
import { VeriPayMark } from './VeriPayMark';

const navigation = [
  ['Alert Queue', '/analyst', '⚠'],
  ['System Performance', '/analyst/performance', '◒'],
  ['Model Info', '/analyst/models', '◆'],
] as const;

export function AnalystLayout({ children }: { children: ReactNode }) {
  const { data: health } = useHealth();
  const operational = health?.status === 'ok';

  return (
    <div className="min-h-screen bg-[#f7fbff] text-slate-900">
      <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-[#201b4b] text-white">
        <div className="flex h-20 items-center border-b border-white/10 px-5">
          <VeriPayMark compact />
        </div>

        <div className="px-5 pt-6">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#43cddd]">
            Fraud Operations
          </p>
          <p className="mt-1 text-sm text-[#d9ffef]">Risk analyst</p>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-5">
          {navigation.map(([label, href, icon]) => (
            <NavLink
              key={href}
              to={href}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition ${
                  isActive
                    ? 'bg-[#43cddd] text-[#201b4b] shadow-sm'
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

        <div className="border-t border-white/10 p-4">
          <Link
            to="/fi-ops"
            className="mb-3 block rounded-lg px-3 py-2 text-sm text-[#e7f5ff] hover:bg-white/10"
          >
            ← Back to bank console
          </Link>
          <div className="flex items-center gap-2 text-xs text-[#fffed0]">
            <span
              className={`h-2 w-2 rounded-full ${operational ? 'bg-emerald-400' : 'bg-red-400'}`}
            />
            {operational
              ? 'All models loaded'
              : 'Checking system health…'}
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </div>
    </div>
  );
}
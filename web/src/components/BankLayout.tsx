import { useState, type ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import { notifications } from '../bankData';

const navigation = [
  ['Dashboard', '/fi-ops'], ['Transactions', '/bank/transactions'], ['Fraud & Alerts', '/bank/alerts'],
  ['Risk Analytics', '/bank/analytics'], ['Customers', '/bank/customers'], ['Merchants', '/bank/merchants'],
  ['Fraud Policies', '/bank/policies'], ['AI Models', '/bank/models'], ['Reports', '/bank/reports'],
  ['Audit Logs', '/bank/audit'], ['Settings', '/bank/settings'],
];

export function BankLayout({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const unread = notifications.filter((notification) => notification.unread).length;
  return (
    <div className="min-h-screen bg-[#f4f7f6] text-slate-900">
      <aside className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-[#102a2a] text-white transition-transform lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex h-20 items-center justify-between border-b border-white/10 px-6"><div><p className="text-xl font-semibold tracking-tight">VeriPay</p><p className="text-[10px] font-bold uppercase tracking-[0.2em] text-teal-300">Bank Console</p></div><button className="text-teal-200 lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation">X</button></div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">{navigation.map(([label, href]) => <NavLink key={href} to={href} onClick={() => setOpen(false)} className={({ isActive }) => `block rounded-md px-3 py-2.5 text-sm font-medium transition ${isActive ? 'bg-teal-400/15 text-teal-200' : 'text-slate-300 hover:bg-white/5 hover:text-white'}`}>{label}</NavLink>)}</nav>
        <div className="border-t border-white/10 p-4"><div className="mb-4 flex items-center gap-2 text-xs text-emerald-300"><span className="h-2 w-2 rounded-full bg-emerald-400" />System status: Operational</div><div className="flex items-center gap-3"><div className="grid h-9 w-9 place-items-center rounded-full bg-teal-300 font-bold text-[#102a2a]">AM</div><div><p className="text-sm font-semibold">Avery Morgan</p><p className="text-xs text-slate-400">Risk Manager</p></div></div><button className="mt-4 w-full rounded-md border border-white/10 py-2 text-left text-xs text-slate-400 hover:border-white/30 hover:text-white">Log out</button></div>
      </aside>
      {open && <button className="fixed inset-0 z-20 bg-slate-950/40 lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation overlay" />}
      <div className="lg:pl-64"><header className="sticky top-0 z-10 flex h-20 items-center justify-between border-b border-slate-200 bg-[#f4f7f6]/95 px-5 backdrop-blur md:px-8"><div className="flex items-center gap-4"><button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm lg:hidden" onClick={() => setOpen(true)} aria-label="Open navigation">Menu</button>{searchOpen ? <input autoFocus className="w-52 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-teal-600 md:w-80" placeholder="Search transactions, customers..." onBlur={() => setSearchOpen(false)} /> : <button className="text-sm text-slate-500 hover:text-slate-900" onClick={() => setSearchOpen(true)}>Search <span className="ml-2 rounded border border-slate-300 bg-white px-1.5 py-0.5 text-xs">Ctrl K</span></button>}</div><div className="flex items-center gap-5 text-sm"><button className="relative text-slate-500 hover:text-slate-900" aria-label={`${unread} unread notifications`}>Notifications{unread > 0 && <span className="absolute -right-2 -top-2 grid h-4 min-w-4 place-items-center rounded-full bg-red-600 px-1 text-[10px] text-white">{unread}</span>}</button><button className="hidden text-slate-500 hover:text-slate-900 md:block">Help</button><div className="hidden h-6 w-px bg-slate-300 md:block" /><div className="text-right"><p className="font-semibold">Avery Morgan</p><p className="text-xs text-slate-500">Risk Manager</p></div><div className="grid h-9 w-9 place-items-center rounded-full bg-[#102a2a] text-xs font-bold text-teal-200">AM</div></div></header>{children}</div>
    </div>
  );
}

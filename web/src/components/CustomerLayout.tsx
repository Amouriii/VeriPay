import { type ReactNode, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { VeriPayMark } from './VeriPayMark';

const links = [
  ['Home', '/customer'],
  ['Accounts', '/customer/accounts'],
  ['Transactions', '/customer/transactions'],
  ['Normal Activity', '/customer/normal-activity'],
  ['Security', '/customer/security'],
  ['Report Fraud', '/customer/report-fraud'],
];

function NavIcon({ label }: { label: string }) {
  const common = {
    width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none',
    stroke: 'currentColor', strokeWidth: 1.8,
    strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const,
    'aria-hidden': true,
  };
  if (label === 'Home') return <svg {...common}><path d="M3 10.5 12 3l9 7.5" /><path d="M5 9.5V21h14V9.5" /><path d="M9 21v-6h6v6" /></svg>;
  if (label === 'Accounts') return <svg {...common}><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 10h18M7 15h3" /></svg>;
  if (label === 'Transactions') return <svg {...common}><path d="M4 7h16M4 12h16M4 17h16" /><path d="m17 5 3 2-3 2M7 10l-3 2 3 2M17 15l3 2-3 2" /></svg>;
  if (label === 'Normal Activity') return <svg {...common}><path d="M4 19V5M4 19h16" /><path d="m7 15 3-4 3 2 4-6" /></svg>;
  if (label === 'Security') return <svg {...common}><path d="M12 3 20 6v5c0 5-3.3 8.3-8 10-4.7-1.7-8-5-8-10V6l8-3Z" /><path d="m9.5 12 1.7 1.7 3.5-3.7" /></svg>;
  return <svg {...common}><path d="M12 3 21 20H3L12 3Z" /><path d="M12 9v4M12 16h.01" /></svg>;
}

function LogoutIcon() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M10 17l5-5-5-5" /><path d="M15 12H3" /><path d="M21 19V5a2 2 0 0 0-2-2h-5" /></svg>;
}

function ChevronIcon() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6" /></svg>;
}

export function CustomerLayout({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  function handleLogout() {
    setOpen(false);
    navigate('/customer/login', { replace: true });
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#EEF5FF] via-[#F1EEFF] to-[#EAF7FA] text-[#263B5A]">
      <aside className={`fixed inset-y-0 left-0 z-40 flex h-screen w-[224px] flex-col overflow-hidden border-r border-[#AFC7E6] bg-[#C9DCF3] transition-transform lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="h-1 w-full shrink-0 bg-gradient-to-r from-[#5268D8] via-[#43CDDD] to-[#8B7ED8]" />

        <div className="flex h-[60px] shrink-0 items-center border-b border-[#AFC7E6] bg-[#C5DAF2] px-4">
          <VeriPayMark />
          <button type="button" className="ml-auto rounded-lg p-2 text-[#526B8A] hover:bg-[#B8D0EC] lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation"><span className="text-lg">×</span></button>
        </div>

        <div className="shrink-0 border-b border-[#AFC7E6] bg-gradient-to-r from-[#C0D8F1] to-[#D8D1F1] px-3 py-2.5">
          <div className="flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-[#5268D8] text-white shadow-sm"><span className="text-[10px] font-black">C</span></span>
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.18em] text-[#5263B5]">Customer portal</p>
              <p className="mt-0.5 text-xs font-medium text-[#526B8A]">Personal banking</p>
            </div>
          </div>
        </div>

        <nav className="min-h-0 flex-1 overflow-y-auto px-3 py-4 vp-scrollbar">
          <p className="px-2 pb-1.5 text-[9px] font-black uppercase tracking-[0.18em] text-[#647A99]">Your banking</p>
          <div className="space-y-0.5">
            {links.map(([label, href]) => (
              <NavLink key={href} to={href} end={href === '/customer'} onClick={() => setOpen(false)} className={({ isActive }) => `group relative flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-semibold transition ${isActive ? 'bg-[#B9D1F0] text-[#4F63B8] shadow-sm' : 'text-[#526B8A] hover:bg-[#BFD6EF] hover:text-[#263B5A]'}`}>
                {({ isActive }) => <>
                  <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-lg transition ${isActive ? 'bg-[#F9FBFF] text-[#5268D8] shadow-sm' : 'bg-[#BCD3EC] text-[#607895] group-hover:bg-[#EDF4FF] group-hover:text-[#5268D8]'}`}><NavIcon label={label} /></span>
                  <span>{label}</span>
                  {isActive && <span className="absolute bottom-2 left-0 top-2 w-1 rounded-r-full bg-[#5268D8]" />}
                </>}
              </NavLink>
            ))}
          </div>
        </nav>

        <div className="shrink-0 border-t border-[#AFC7E6] bg-gradient-to-r from-[#D8D2F0] to-[#C0D8F1] p-2">
          <NavLink to="/customer/profile" onClick={() => setOpen(false)} className="mb-1.5 flex items-center gap-2.5 rounded-lg border border-[#C0D4ED] bg-[#EEF4FF] p-2 shadow-sm transition hover:bg-white hover:shadow-md focus:outline-none focus:ring-4 focus:ring-[#5268D8]/15">
            <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[#5268D8] text-xs font-black text-white">JL</div>
            <div className="min-w-0 flex-1"><p className="truncate text-sm font-bold text-[#263B5A]">Jordan Lee</p><p className="text-[11px] text-[#647A99]">Personal account</p></div>
            <span className="shrink-0 text-[#526B8A]"><ChevronIcon /></span>
          </NavLink>

          <div className="mb-1.5 flex items-center gap-2 px-2 text-[10px] font-semibold text-[#087A5E]"><span className="h-2 w-2 rounded-full bg-[#12A6A0] shadow-[0_0_0_3px_#D9F2EF]" />Account protected</div>

          <button type="button" onClick={handleLogout} className="flex w-full items-center gap-3 rounded-xl border border-[#E7C6D2] bg-[#FFF5F7] px-3 py-2.5 text-left text-sm font-bold text-[#C0395A] transition hover:border-[#C0395A]/40 hover:bg-[#FFECEF] focus:outline-none focus:ring-4 focus:ring-[#C0395A]/10">
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[#FFE8EE] text-[#C0395A]"><LogoutIcon /></span>
            <span>Log out</span><span className="ml-auto text-xs text-[#C0395A]">→</span>
          </button>
        </div>
      </aside>

      {open && <button type="button" className="fixed inset-0 z-30 bg-[#263B5A]/30 lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation overlay" />}

      <div className="lg:pl-[224px]">
        <header className="sticky top-0 z-20 flex h-[68px] items-center justify-between border-b border-[#C7D8F2] bg-[#EEF5FF]/95 px-4 backdrop-blur md:px-6">
          <div className="flex items-center gap-4">
            <button type="button" className="rounded-xl border border-[#C7D8F2] bg-[#E6F1FF] px-3 py-2 text-sm font-bold text-[#526B8A] shadow-sm lg:hidden" onClick={() => setOpen(true)} aria-label="Open navigation">Menu</button>
            <div className="hidden items-center gap-2 md:flex">
              <span className="rounded-full bg-[#DDE7FF] px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.12em] text-[#5263B5]">Customer</span>
              <span className="text-[#7186A3]">/</span>
              <span className="text-sm font-semibold text-[#526B8A]">Personal banking</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block"><p className="text-sm font-bold text-[#263B5A]">Jordan Lee</p><p className="text-xs text-[#647A99]">•••• 4521</p></div>
            <NavLink to="/customer/profile" className="grid h-9 w-9 place-items-center rounded-full bg-[#5268D8] text-[11px] font-black text-white ring-4 ring-[#DCE7FF] transition hover:ring-[#5268D8]/30" aria-label="Open profile">JL</NavLink>
          </div>
        </header>
        <main>{children}</main>
      </div>
    </div>
  );
}

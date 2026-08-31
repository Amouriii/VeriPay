import { Link } from 'react-router-dom';
import { VeriPayMark } from '../components/VeriPayMark';

const accountTypes = [
  {
    href: '/customer/login',
    eyebrow: 'For individuals',
    title: 'Customer account',
    description: 'Manage your personal accounts, review transactions, and keep your payments secure.',
    accent: '#087F7A',
    icon: 'P',
    action: 'Continue as customer',
  },
  {
    href: '/login',
    eyebrow: 'For organizations',
    title: 'Business account',
    description: 'Monitor payment activity, manage risk, and protect your customers from one console.',
    accent: '#7566C9',
    icon: 'B',
    action: 'Continue as business',
  },
] as const;

export function AccountSelection() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#DCEBFF] via-[#E8E7FF] to-[#DDF5F7] px-5 py-12 text-[#17324D]">
      <section className="w-full max-w-4xl">
        <div className="mb-10 flex justify-center">
          <VeriPayMark />
        </div>

        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-[#087F7A]">
            Welcome to VeriPay
          </p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-[#17324D] sm:text-4xl">
            How will you use VeriPay?
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-sm leading-6 text-[#536B8D] sm:text-base">
            Choose the account that fits you best. You can switch between experiences at any time.
          </p>
        </div>

        <div className="mt-10 grid gap-5 md:grid-cols-2">
          {accountTypes.map((account) => (
            <Link
              key={account.href}
              to={account.href}
              className="group rounded-2xl border border-[#BFD0EA] bg-gradient-to-br from-[#EDF4FF] via-[#E9EEFF] to-[#EAE7FF] p-6 shadow-[0_12px_35px_rgba(82,104,216,0.11)] transition hover:-translate-y-1 hover:border-[#8EA4D1] hover:shadow-[0_18px_50px_rgba(82,104,216,0.18)] focus:outline-none focus:ring-4 focus:ring-[#5268D8]/20 sm:p-8"
            >
              <div className="flex items-start justify-between gap-5">
                <span
                  className="grid h-12 w-12 shrink-0 place-items-center rounded-xl text-lg font-black text-white shadow-lg"
                  style={{ backgroundColor: account.accent }}
                  aria-hidden="true"
                >
                  {account.icon}
                </span>
                <span className="text-2xl text-[#8192AA] transition group-hover:translate-x-1 group-hover:text-[#5268D8]" aria-hidden="true">
                  →
                </span>
              </div>

              <p className="mt-8 text-xs font-black uppercase tracking-[0.16em]" style={{ color: account.accent }}>
                {account.eyebrow}
              </p>
              <h2 className="mt-2 text-xl font-semibold text-[#17324D]">
                {account.title}
              </h2>
              <p className="mt-3 min-h-12 text-sm leading-6 text-[#536B8D]">
                {account.description}
              </p>
              <span className="mt-7 inline-flex items-center text-sm font-bold text-[#5268D8]">
                {account.action}
                <span className="ml-2 transition group-hover:translate-x-1" aria-hidden="true">→</span>
              </span>
            </Link>
          ))}
        </div>

        <div className="mx-auto mt-8 flex max-w-2xl items-start gap-3 rounded-xl border border-[#B9DCD9] bg-[#E0F5F4] p-4 text-xs leading-5 text-[#536B8D]">
          <span className="text-base text-[#087A5E]" aria-hidden="true">✓</span>
          <p>
            <strong className="text-[#17324D]">Your security comes first.</strong>{' '}
            VeriPay keeps your account and payment activity protected across every experience.
          </p>
        </div>

        <p className="mt-7 text-center text-xs text-[#536B8D]">
          Need help choosing? Contact your bank or institution administrator.
        </p>
      </section>
    </main>
  );
}

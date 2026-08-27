import { Link, useParams } from 'react-router-dom';
import { customers, bankTransactions } from '../bankData';

export function BankCustomerProfile() {
  const { id } = useParams<{ id: string }>();

  const customer =
    customers.find((item) => item.id === id) ?? customers[0];

  const customerNumber = customer.id.replace('CUS-', 'Customer #');

  const related = bankTransactions.filter(
    (item) => item.customer === customerNumber
  );

  const riskTone =
    customer.risk === 'HIGH'
      ? 'text-red-700'
      : customer.risk === 'MEDIUM'
      ? 'text-orange-700'
      : 'text-emerald-700';

  return (
    <main className="mx-auto max-w-6xl px-6 py-7">
      {/* Back */}
      <Link
        to="/bank/customers"
        className="inline-flex items-center gap-1.5 text-sm font-semibold text-[#29265f] hover:underline"
      >
        <span>←</span>
        <span>Back to customers</span>
      </Link>

      {/* Customer header */}
      <header className="mt-5 flex flex-col justify-between gap-4 border-b border-[#43cddd]/50 pb-5 md:flex-row md:items-end">
        <div>
          <div className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#43cddd]/20 text-[#29265f]">
              <CustomerIcon />
            </span>

            <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#29265f]">
              Customer profile
            </p>
          </div>

          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-[#29265f]">
            {customer.name}
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            {customer.id} · {customer.email}
          </p>
        </div>

        <span className="w-fit rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700">
          Account {customer.account}
        </span>
      </header>

      {/* Customer summary */}
      <section className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Summary
          icon={<CardIcon />}
          label="Masked card"
          value={`•••• ${customer.cardLast4}`}
        />

        <Summary
          icon={<RiskIcon />}
          label="Risk status"
          value={customer.risk}
          valueClass={riskTone}
        />

        <Summary
          icon={<ActivityIcon />}
          label="Transaction volume"
          value={customer.volume}
        />

        <Summary
          icon={<AlertIcon />}
          label="Fraud alerts"
          value={String(customer.alerts)}
          valueClass={
            customer.alerts > 0
              ? 'text-orange-700'
              : 'text-emerald-700'
          }
        />
      </section>

      {/* Normal behavior */}
      <section className="mt-5 overflow-hidden rounded-xl border border-[#f0c96a] bg-[#fffed0]">
        <div className="px-5 py-4">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
            <div>
              <div className="flex items-center gap-2">
                <span className="grid h-7 w-7 place-items-center rounded-full bg-[#f9e8b5] text-[#29265f]">
                  <BaselineIcon />
                </span>

                <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#29265f]">
                  Review guidance
                </p>
              </div>

              <h2 className="mt-2 text-xl font-semibold text-[#29265f]">
                Compare activity with the baseline
              </h2>

              <p className="mt-1 text-sm text-[#42527a]">
                Use these normal patterns to identify unusual customer activity.
              </p>
            </div>

            <span className="w-fit shrink-0 rounded-full bg-[#f9e8b5] px-3 py-1 text-xs font-bold text-[#29265f]">
              Normal behavior
            </span>
          </div>

          {/* Complete behavioral baseline */}
          <div className="mt-4 overflow-hidden rounded-lg border border-[#ead69a] bg-white/30">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">

              <Behavior
                icon={<MoneyIcon />}
                label="Average amount"
                value="$124.50"
              />

              <Behavior
                icon={<RangeIcon />}
                label="Typical amount range"
                value="$35 - $450"
              />

              <Behavior
                icon={<LocationIcon />}
                label="Location"
                value="New York · 82%"
              />

              <Behavior
                icon={<TimeIcon />}
                label="Time"
                value="12 PM - 8 PM"
              />

              <Behavior
                icon={<DeviceIcon />}
                label="Device"
                value="iPhone 15 Pro · 72%"
              />

              <Behavior
                icon={<FrequencyIcon />}
                label="Frequency"
                value="3 - 5 transactions/day"
              />

              <Behavior
                icon={<VelocityIcon />}
                label="Velocity"
                value="1 - 2 transactions/hour"
              />

              <Behavior
                icon={<CategoryIcon />}
                label="Category"
                value="Groceries · 32%"
              />

              <Behavior
                icon={<CurrencyIcon />}
                label="Currency"
                value="USD"
              />

            </div>
          </div>
        </div>
      </section>

      {/* Recent transactions */}
      <section className="mt-5 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-5 py-4">
          <div className="flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center rounded-full bg-[#43cddd]/15 text-[#29265f]">
              <TransactionIcon />
            </span>

            <div>
              <h2 className="font-semibold text-[#29265f]">
                Recent transactions
              </h2>

              <p className="mt-0.5 text-xs text-slate-500">
                Recent activity used to compare against the customer's normal behavior.
              </p>
            </div>
          </div>
        </div>

        <div className="divide-y divide-slate-100">
          {related.length > 0 ? (
            related.map((item) => (
              <Link
  key={item.id}
  to={`/tx/${item.id}`}
  state={{ fromCustomerId: customer.id }}
  className="flex items-center justify-between px-5 py-4 transition hover:bg-slate-50"
>
  <div>
    <p className="font-semibold text-[#29265f]">
      {item.id} · {item.merchant}
    </p>
    <p className="mt-1 text-xs text-slate-500">
      {item.reason}
    </p>
  </div>

  <div className="text-right">
    <p className="text-sm font-semibold text-[#29265f]">
      ${item.amount.toLocaleString()}
    </p>
    <span className="mt-1 inline-block text-xs font-semibold text-[#2e2c83]">
      Review →
    </span>
  </div>
</Link>
            ))
          ) : (
            <p className="px-5 py-8 text-sm text-slate-500">
              No recent transactions are available for this customer.
            </p>
          )}
        </div>
      </section>
    </main>
  );
}

/* ================================================= */
/* Summary card */
/* ================================================= */

function Summary({
  icon,
  label,
  value,
  valueClass = 'text-[#007064]',
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-4">
      <div className="flex items-center gap-2">
        <span className="grid h-7 w-7 place-items-center rounded-md bg-[#43cddd]/10 text-[#29265f]">
          {icon}
        </span>

        <p className="text-xs text-slate-500">
          {label}
        </p>
      </div>

      <p className={`mt-2 font-semibold ${valueClass}`}>
        {value}
      </p>
    </div>
  );
}

/* ================================================= */
/* Behavioral baseline */
/* ================================================= */

function Behavior({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="min-w-0 border-b border-[#ead69a] px-4 py-3.5 sm:[&:nth-child(odd)]:border-r lg:border-b lg:[&:nth-child(4n)]:border-r-0">
      <div className="flex items-center gap-2">
        <span className="shrink-0 text-[#6b6b80]">
          {icon}
        </span>

        <p className="text-[11px] font-bold uppercase tracking-[0.1em] text-slate-500">
          {label}
        </p>
      </div>

      <p className="mt-1.5 break-words text-sm font-semibold leading-5 text-[#29265f]">
        {value}
      </p>
    </div>
  );
}

/* ================================================= */
/* Risk badge */
/* ================================================= */

function RiskBadge({
  level,
}: {
  level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}) {
  const styles =
    level === 'CRITICAL'
      ? 'bg-red-600 text-white'
      : level === 'HIGH'
      ? 'bg-orange-100 text-orange-800'
      : level === 'MEDIUM'
      ? 'bg-amber-100 text-amber-800'
      : 'bg-emerald-100 text-emerald-800';

  return (
    <span
      className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${styles}`}
    >
      {level}
    </span>
  );
}

/* ================================================= */
/* Icons */
/* ================================================= */

function CustomerIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 20c.8-3.5 3.1-5.5 7-5.5s6.2 2 7 5.5" />
    </svg>
  );
}

function CardIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3 10h18M7 15h4" />
    </svg>
  );
}

function RiskIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <path d="M12 3l7 3v5c0 4.7-2.9 8-7 10-4.1-2-7-5.3-7-10V6l7-3z" />
      <path d="M12 8v4M12 15h.01" />
    </svg>
  );
}

function ActivityIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <path d="M4 17V7M10 17V4M16 17v-6M22 17H2" />
    </svg>
  );
}

function AlertIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <path d="M12 4a5 5 0 0 1 5 5v3l2 3H5l2-3V9a5 5 0 0 1 5-5z" />
      <path d="M10 19h4" />
    </svg>
  );
}

function BaselineIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <path d="M4 19V9M10 19V5M16 19v-8M22 19H2" />
    </svg>
  );
}

function TransactionIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3 10h18M7 15h3" />
    </svg>
  );
}

function MoneyIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
      <circle cx="12" cy="12" r="8" />
      <path d="M14.5 9.5c-.5-1-1.4-1.5-2.5-1.5-1.2 0-2 .6-2 1.5s.8 1.3 2 1.6 2 .7 2 1.7-.8 1.7-2 1.7c-1.1 0-2-.5-2.5-1.5" />
      <path d="M12 6.5v11" />
    </svg>
  );
}

function RangeIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
      <path d="M5 8h14M5 16h14" />
      <circle cx="8" cy="8" r="2" />
      <circle cx="16" cy="16" r="2" />
    </svg>
  );
}

function LocationIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
      <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0z" />
      <circle cx="12" cy="10" r="2.5" />
    </svg>
  );
}

function TimeIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
      <circle cx="12" cy="12" r="8" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}

function DeviceIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
      <rect x="7" y="3" width="10" height="18" rx="2" />
      <path d="M10 18h4" />
    </svg>
  );
}

function FrequencyIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
      <path d="M4 17l5-5 3 3 7-8" />
      <path d="M15 7h4v4" />
    </svg>
  );
}

function VelocityIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
      <path d="M4 15l6-6 3 3 7-7" />
      <path d="M16 5h4v4" />
    </svg>
  );
}

function CategoryIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
      <path d="M4 5h7v7H4zM13 5h7v7h-7zM4 14h7v5H4zM13 14h7v5h-7z" />
    </svg>
  );
}

function CurrencyIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
      <circle cx="12" cy="12" r="8" />
      <path d="M9 9h4a2 2 0 1 1 0 4H9a2 2 0 1 0 0 4h5M12 6v12" />
    </svg>
  );
}
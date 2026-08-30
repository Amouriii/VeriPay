import { useMemo, useState, type ReactNode } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import {
  activityEvents,
  customerAccounts,
  customerDevices,
  customerTransactions,
  type CustomerTransaction,
} from '../customerData';

const money = (amount: number) =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(Math.abs(amount));

function Icon({
  name,
  size = 18,
}: {
  name:
    | 'arrow'
    | 'check'
    | 'alert'
    | 'shield'
    | 'card'
    | 'clock'
    | 'location'
    | 'device'
    | 'chart'
    | 'logout';
  size?: number;
}) {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
  };

  const paths: Record<string, ReactNode> = {
    arrow: (
      <>
        <path d="M5 12h14" />
        <path d="m13 6 6 6-6 6" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    alert: (
      <>
        <path d="M12 3 21 20H3L12 3Z" />
        <path d="M12 9v4M12 16h.01" />
      </>
    ),
    shield: (
      <>
        <path d="M12 3 20 6v5c0 5-3.3 8.3-8 10-4.7-1.7-8-5-8-10V6l8-3Z" />
        <path d="m9.5 12 1.7 1.7 3.5-3.7" />
      </>
    ),
    card: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="M3 10h18M7 15h3" />
      </>
    ),
    clock: (
      <>
        <circle cx="12" cy="12" r="8.5" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    location: (
      <>
        <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
        <circle cx="12" cy="10" r="2.5" />
      </>
    ),
    device: (
      <>
        <rect x="6" y="3" width="12" height="18" rx="2" />
        <path d="M10 18h4" />
      </>
    ),
    chart: (
      <>
        <path d="M4 19V5M4 19h16" />
        <path d="m7 15 3-4 3 2 4-6" />
      </>
    ),
    logout: (
      <>
        <path d="M10 17l5-5-5-5" />
        <path d="M15 12H3" />
        <path d="M21 19V5a2 2 0 0 0-2-2h-5" />
      </>
    ),
  };

  return <svg {...common}>{paths[name]}</svg>;
}

function Panel({
  children,
  className = '',
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-2xl border border-[#dce7e9] bg-white shadow-[0_1px_2px_rgba(23,50,77,0.04)] ${className}`}
    >
      {children}
    </section>
  );
}

function Heading({
  label,
  title,
  detail,
}: {
  label: string;
  title: string;
  detail: string;
}) {
  return (
    <div className="mb-6">
      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#087f7a]">
        {label}
      </p>
      <h1 className="mt-2 text-[28px] font-semibold tracking-[-0.025em] text-[#17324d] md:text-[32px]">
        {title}
      </h1>
      <p className="mt-1.5 text-sm text-[#718294]">{detail}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles =
    status === 'Completed' || status === 'Approved' || status === 'Trusted'
      ? 'bg-[#e9f7f1] text-[#087a5e]'
      : status === 'Verification Required' ||
        status === 'Pending' ||
        status === 'New device'
      ? 'bg-[#fff4d9] text-[#9a6700]'
      : status === 'Blocked' ||
        status === 'Denied' ||
        status === 'Failed'
      ? 'bg-[#fff0ee] text-[#b44a43]'
      : 'bg-[#eef3f5] text-[#5e7080]';

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-[10px] font-bold ${styles}`}
    >
      {status}
    </span>
  );
}

function AccountRow({
  account,
}: {
  account: (typeof customerAccounts)[number];
}) {
  return (
    <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 items-center gap-4">
        <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[#edf7f6] text-[#087f7a]">
          <Icon name="card" />
        </div>
        <div className="min-w-0">
          <p className="font-semibold text-[#17324d]">{account.name}</p>
          <p className="mt-1 text-xs text-[#718294]">
            •••• {account.last4} · {account.type}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between gap-6 sm:justify-end">
        <div className="text-left sm:text-right">
          <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#8a99a6]">
            Available
          </p>
          <p className="mt-1 text-xl font-semibold tracking-tight text-[#17324d]">
            {money(account.balance)}
          </p>
        </div>
        <span className="rounded-full bg-[#e9f7f1] px-2.5 py-1 text-[10px] font-bold text-[#087a5e]">
          Active
        </span>
      </div>
    </div>
  );
}

function AttentionTransaction({
  transaction,
  action,
  onApprove,
  onDeny,
}: {
  transaction: CustomerTransaction;
  action?: 'approved' | 'denied';
  onApprove: () => void;
  onDeny: () => void;
}) {
  return (
    <div className="p-5 sm:p-6">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex min-w-0 items-start gap-4">
          <div className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-[#fff2cf] text-sm font-bold text-[#946300]">
            {transaction.merchant.slice(0, 1)}
          </div>

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <p className="font-semibold text-[#17324d]">
                {transaction.merchant}
              </p>
              <StatusBadge
                status={
                  action === 'approved'
                    ? 'Approved'
                    : action === 'denied'
                    ? 'Denied'
                    : transaction.status
                }
              />
            </div>

            <p className="mt-1.5 text-sm text-[#53687b]">
              {transaction.amount > 0 ? '+' : '-'}
              {money(transaction.amount)} · {transaction.date}
            </p>

            <p className="mt-1 text-xs leading-5 text-[#718294]">
              {transaction.securityNote ??
                'This activity is different from your usual pattern.'}
            </p>
          </div>
        </div>

        {!action ? (
          <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
            <button
              type="button"
              onClick={onApprove}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#087f7a] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#066c68] focus:outline-none focus:ring-4 focus:ring-[#087f7a]/15"
            >
              <Icon name="check" size={16} />
              I recognize it
            </button>

            <button
              type="button"
              onClick={onDeny}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#e7b9b4] bg-white px-4 py-2.5 text-sm font-semibold text-[#a9433d] transition hover:bg-[#fff7f6]"
            >
              <Icon name="alert" size={16} />
              I do not recognize it
            </button>
          </div>
        ) : (
          <div
            className={`rounded-xl px-4 py-2.5 text-sm font-semibold ${
              action === 'approved'
                ? 'bg-[#e9f7f1] text-[#087a5e]'
                : 'bg-[#fff0ee] text-[#b44a43]'
            }`}
          >
            {action === 'approved'
              ? 'Transaction approved'
              : 'Transaction rejected'}
          </div>
        )}
      </div>
    </div>
  );
}

function TransactionRow({
  transaction,
  showStatus = false,
  fromDashboard = false,
}: {
  transaction: CustomerTransaction;
  showStatus?: boolean;
  fromDashboard?: boolean;
}) {
  return (
    <Link
      to={`/customer/transactions/${transaction.id}`}
      state={fromDashboard ? { from: 'dashboard' } : undefined}
      className="flex items-center justify-between gap-3 px-4 py-3 transition hover:bg-[#f5fafb]"
    >
      <div className="flex min-w-0 items-center gap-3">
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[#eef3f5] text-xs font-bold text-[#5e7080]">
          {transaction.merchant.slice(0, 1)}
        </div>

        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-[#17324d]">
            {transaction.merchant}
          </p>
          <p className="mt-1 text-xs text-[#718294]">
            {transaction.date} · {transaction.type}
          </p>
        </div>
      </div>

      <div className="shrink-0 text-right">
        <p
          className={`text-sm font-semibold ${
            transaction.amount > 0 ? 'text-[#087a5e]' : 'text-[#17324d]'
          }`}
        >
          {transaction.amount > 0 ? '+' : '-'}
          {money(transaction.amount)}
        </p>
        {showStatus && (
          <div className="mt-1">
            <StatusBadge status={transaction.status} />
          </div>
        )}
      </div>
    </Link>
  );
}

/* -------------------------------------------------------------------------- */
/* Dashboard                                                                  */
/* -------------------------------------------------------------------------- */

export function CustomerDashboard() {
  const [riskStatus, setRiskStatus] = useState<
    Record<string, 'approved' | 'denied'>
  >({});

  const verificationTransactions = customerTransactions.filter(
    (transaction) =>
      transaction.status === 'Verification Required' ||
      transaction.status === 'Blocked'
  );

  const recentTransactions = customerTransactions
    .filter((transaction) => transaction.status !== 'Verification Required')
    .slice(0, 4);

  const approveTransaction = (id: string) => {
    setRiskStatus((current) => ({
      ...current,
      [id]: 'approved',
    }));
  };

  const denyTransaction = (id: string) => {
    setRiskStatus((current) => ({
      ...current,
      [id]: 'denied',
    }));
  };

  const totalBalance = customerAccounts.reduce(
    (total, account) => total + Number(account.balance || 0),
    0
  );

  return (
       <div className="mx-auto max-w-[1200px] px-4 py-4 md:px-6 md:py-5">
      {/* -------------------------------------------------------------- */}
      {/* HEADER                                                         */}
      {/* -------------------------------------------------------------- */}

      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <Heading
          label="Customer portal · Personal banking"
          title="Welcome Back, Jordan"
          detail={
            verificationTransactions.length > 0
              ? 'You have activity that needs your attention.'
              : 'Your account is up to date.'
          }
        />

        <div className="hidden rounded-xl border border-[#dce8ea] bg-white px-4 py-2.5 shadow-sm sm:block">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#7b8b99]">
            Total available
          </p>
          <p className="mt-0.5 text-lg font-bold text-[#102a43]">
            ${totalBalance.toLocaleString()}
          </p>
        </div>
      </div>

      {/* -------------------------------------------------------------- */}
      {/* VERIFICATION / SECURITY STATUS                                 */}
      {/* -------------------------------------------------------------- */}

      {verificationTransactions.length > 0 ? (
        <section className="overflow-hidden rounded-2xl border border-[#f0c8c2] bg-white shadow-sm">
          <div className="border-b border-[#f0d2cd] bg-[#fff5f3] px-4 py-3.5 sm:px-5">
            <div className="flex items-start gap-3">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#ffe1dc] text-[#c0392b]">
                <Icon name="alert" size={17} />
              </span>

              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[#c0392b]">
                    Action required
                  </p>

                  <span className="rounded-full bg-[#c0392b] px-2 py-0.5 text-[10px] font-bold text-white">
                    {verificationTransactions.length}
                  </span>
                </div>

                <h2 className="mt-0.5 text-sm font-bold text-[#3d2522]">
                  Review {verificationTransactions.length === 1
                    ? 'this transaction'
                    : 'these transactions'}
                </h2>

                <p className="mt-1 text-xs leading-5 text-[#765e5a]">
                  Confirm activity you recognize. Reject anything you did not
                  authorize.
                </p>
              </div>
            </div>
          </div>

          <div className="divide-y divide-[#edf0f1]">
            {verificationTransactions.map((transaction) => (
              <AttentionTransaction
                key={transaction.id}
                transaction={transaction}
                action={riskStatus[transaction.id]}
                onApprove={() => approveTransaction(transaction.id)}
                onDeny={() => denyTransaction(transaction.id)}
              />
            ))}
          </div>
        </section>
      ) : (
        <section className="rounded-2xl border border-[#bfe5d8] bg-[#effaf6] px-4 py-3.5 shadow-sm sm:px-5">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-white text-[#087a5e] shadow-sm">
              <Icon name="check" size={17} />
            </span>

            <div>
              <p className="text-sm font-bold text-[#17324d]">
                You are all caught up
              </p>

              <p className="mt-0.5 text-xs text-[#5f756f]">
                No transactions are waiting for verification.
              </p>
            </div>
          </div>
        </section>
      )}

      {/* -------------------------------------------------------------- */}
      {/* ACCOUNT BALANCES                                               */}
      {/* -------------------------------------------------------------- */}

      <section className="mt-4">
        <div className="mb-2.5 flex items-center justify-between">
          <div>
            <p className="vp-section-label">Your money</p>

            <h2 className="mt-0.5 text-base font-bold text-[#102a43]">
              Account balances
            </h2>
          </div>

          <Link
            to="/customer/accounts"
            className="text-xs font-bold text-[#087f7a] transition hover:text-[#05635f]"
          >
            View accounts →
          </Link>
        </div>

        <div className="overflow-hidden rounded-xl border border-[#dfe7ea] bg-white shadow-sm">
          {customerAccounts.map((account) => (
            <AccountRow key={account.last4} account={account} />
          ))}
        </div>
      </section>

      {/* -------------------------------------------------------------- */}
      {/* MAIN GRID                                                       */}
      {/* -------------------------------------------------------------- */}

      <div className="mt-4 grid gap-4 lg:grid-cols-[1.35fr_0.65fr]">
        {/* Recent transactions */}

        <section className="overflow-hidden rounded-xl border border-[#dfe7ea] bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-[#e7edef] px-4 py-3.5">
            <div>
              <h2 className="text-sm font-bold text-[#102a43]">
                Recent transactions
              </h2>

              <p className="mt-0.5 text-[11px] text-[#718294]">
                Latest account activity
              </p>
            </div>

            <Link
              to="/customer/transactions"
              className="text-xs font-bold text-[#087f7a] hover:text-[#05635f]"
            >
              View all →
            </Link>
          </div>

          <div className="divide-y divide-[#edf1f2]">
            {recentTransactions.map((transaction) => (
              <TransactionRow
                key={transaction.id}
                transaction={transaction}
                fromDashboard
              />
            ))}
          </div>
        </section>

        {/* Security */}

        <section className="rounded-xl border border-[#dfe7ea] bg-white p-4 shadow-sm">
          <div className="flex items-start gap-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#e7f7f5] text-[#087f7a]">
              <Icon name="shield" size={17} />
            </span>

            <div>
              <p className="vp-section-label">Security</p>

              <h2 className="mt-0.5 text-sm font-bold text-[#102a43]">
                Account protected
              </h2>

              <p className="mt-1.5 text-xs leading-5 text-[#718294]">
                Two-factor authentication is enabled and there are no urgent
                security issues.
              </p>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3 border-t border-[#e7edef] pt-4">
            <div className="rounded-lg bg-[#f7fafb] p-3">
              <p className="text-[10px] text-[#718294]">
                2-factor authentication
              </p>

              <p className="mt-1 text-xs font-bold text-[#087a5e]">
                Enabled
              </p>
            </div>

            <div className="rounded-lg bg-[#f7fafb] p-3">
              <p className="text-[10px] text-[#718294]">
                Trusted devices
              </p>

              <p className="mt-1 text-xs font-bold text-[#102a43]">
                2 devices
              </p>
            </div>
          </div>

          <Link
            to="/customer/security"
            className="mt-4 inline-flex items-center gap-1 text-xs font-bold text-[#087f7a] hover:text-[#05635f]"
          >
            Security settings
            <Icon name="arrow" size={14} />
          </Link>
        </section>
      </div>

      {/* -------------------------------------------------------------- */}
      {/* QUICK ACTIONS                                                  */}
      {/* -------------------------------------------------------------- */}

{/* -------------------------------------------------------------- */}
{/* QUICK ACTIONS                                                  */}
{/* -------------------------------------------------------------- */}

<section className="mt-5">
  <div className="mb-2.5 flex items-end justify-between">
    <div>
      <p className="vp-section-label">Quick access</p>

      <h2 className="mt-0.5 text-sm font-bold text-[#102a43]">
        Common actions
      </h2>
    </div>
  </div>

  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
    {/* Accounts */}
    <Link
      to="/customer/accounts"
      className="group rounded-xl border border-[#d6e5e8] bg-white p-3 shadow-sm transition hover:-translate-y-0.5 hover:border-[#8ed6d1] hover:shadow-md"
    >
      <div className="mb-2 grid h-8 w-8 place-items-center rounded-lg bg-[#dff4f1] text-[#087f7a]">
        <Icon name="card" size={15} />
      </div>

      <p className="text-xs font-bold text-[#102a43]">
        Accounts
      </p>

      <p className="mt-0.5 text-[10px] text-[#718294]">
        View balances
      </p>
    </Link>

    {/* Transactions */}
    <Link
      to="/customer/transactions"
      className="group rounded-xl border border-[#d6e5e8] bg-white p-3 shadow-sm transition hover:-translate-y-0.5 hover:border-[#a9c5f8] hover:shadow-md"
    >
      <div className="mb-2 grid h-8 w-8 place-items-center rounded-lg bg-[#eaf1ff] text-[#2563eb]">
        <Icon name="arrow" size={15} />
      </div>

      <p className="text-xs font-bold text-[#102a43]">
        Transactions
      </p>

      <p className="mt-0.5 text-[10px] text-[#718294]">
        Review activity
      </p>
    </Link>

    {/* Normal Activity */}
    <Link
      to="/customer/normal-activity"
      className="group rounded-xl border border-[#d6e5e8] bg-white p-3 shadow-sm transition hover:-translate-y-0.5 hover:border-[#c9bff2] hover:shadow-md"
    >
      <div className="mb-2 grid h-8 w-8 place-items-center rounded-lg bg-[#f1edff] text-[#6651b8]">
        <Icon name="chart" size={15} />
      </div>

      <p className="text-xs font-bold text-[#102a43]">
        Normal Activity
      </p>

      <p className="mt-0.5 text-[10px] text-[#718294]">
        View your patterns
      </p>
    </Link>

    {/* Report fraud */}
    <Link
      to="/customer/report-fraud"
      className="group rounded-xl border border-[#f0cbc5] bg-[#fff7f5] p-3 shadow-sm transition hover:-translate-y-0.5 hover:border-[#e5a49c] hover:bg-[#fff1ee] hover:shadow-md"
    >
      <div className="mb-2 grid h-8 w-8 place-items-center rounded-lg bg-[#ffe3de] text-[#c0392b]">
        <Icon name="alert" size={15} />
      </div>

      <p className="text-xs font-bold text-[#102a43]">
        Report fraud
      </p>

      <p className="mt-0.5 text-[10px] text-[#9a6b65]">
        Report suspicious activity
      </p>
    </Link>
  </div>
</section>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Accounts                                                                   */
/* -------------------------------------------------------------------------- */

export function CustomerAccountsPage() {
  return (
    <div className="mx-auto max-w-6xl px-5 py-7 md:px-8 md:py-9">
      <Heading
        label="Money"
        title="Your accounts"
        detail="View your balances and account details."
      />

      <Panel className="divide-y divide-[#e7edef] overflow-hidden">
        {customerAccounts.map((account) => (
          <AccountRow key={account.last4} account={account} />
        ))}
      </Panel>

      <Panel className="mt-5 bg-[#f8fbfb] p-5">
        <div className="flex items-start gap-3">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[#e9f7f5] text-[#087f7a]">
            <Icon name="shield" size={16} />
          </span>
          <div>
            <p className="text-sm font-semibold text-[#17324d]">
              Your account information is secure
            </p>
            <p className="mt-1 text-xs leading-5 text-[#718294]">
              For your protection, only the last four digits of your account
              numbers are shown.
            </p>
          </div>
        </div>
      </Panel>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Transactions                                                               */
/* -------------------------------------------------------------------------- */

export function CustomerTransactionsPage() {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('All');

  const list = useMemo(
    () =>
      customerTransactions.filter((item) => {
        const matchesSearch = `${item.id} ${item.merchant}`
          .toLowerCase()
          .includes(query.toLowerCase());

        const matchesStatus = status === 'All' || item.status === status;

        return matchesSearch && matchesStatus;
      }),
    [query, status]
  );

  return (
    <div className="mx-auto max-w-6xl px-5 py-7 md:px-8 md:py-9">
      <Heading
        label="Activity"
        title="Transactions"
        detail="Review your payment history and transaction status."
      />

      <Panel className="overflow-hidden">
        <div className="flex flex-col gap-3 border-b border-[#e5ecee] bg-[#f8fbfb] p-4 sm:flex-row">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search merchant or transaction ID"
            className="min-w-0 flex-1 rounded-xl border border-[#d5e1e4] bg-white px-3.5 py-2.5 text-sm text-[#17324d] outline-none transition placeholder:text-[#99a7b1] focus:border-[#0a8f89] focus:ring-4 focus:ring-[#0a8f89]/10"
          />
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
            className="rounded-xl border border-[#d5e1e4] bg-white px-3.5 py-2.5 text-sm text-[#53687b] outline-none focus:border-[#0a8f89]"
          >
            <option>All</option>
            <option>Completed</option>
            <option>Pending</option>
            <option>Verification Required</option>
            <option>Blocked</option>
            <option>Denied</option>
            <option>Failed</option>
          </select>
        </div>

        <div className="hidden grid-cols-[1fr_160px_130px_30px] gap-4 border-b border-[#e7edef] px-5 py-3 text-[10px] font-bold uppercase tracking-[0.12em] text-[#8a99a6] sm:grid">
          <span>Transaction</span>
          <span>Date</span>
          <span className="text-right">Amount</span>
          <span />
        </div>

        <div className="divide-y divide-[#edf1f2]">
          {list.map((transaction) => (
            <Link
              key={transaction.id}
              to={`/customer/transactions/${transaction.id}`}
              className="grid gap-3 px-5 py-4 transition hover:bg-[#f7fbfb] sm:grid-cols-[1fr_160px_130px_30px] sm:items-center sm:gap-4"
            >
              <div className="flex min-w-0 items-center gap-3">
                <div
                  className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-xs font-bold ${
                    transaction.status === 'Verification Required' ||
                    transaction.status === 'Blocked'
                      ? 'bg-[#fff2cf] text-[#946300]'
                      : 'bg-[#eef3f5] text-[#5e7080]'
                  }`}
                >
                  {transaction.merchant.slice(0, 1)}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-[#17324d]">
                    {transaction.merchant}
                  </p>
                  <p className="mt-1 text-xs text-[#718294]">
                    {transaction.id} · {transaction.type}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between gap-3 sm:block">
                <p className="text-xs text-[#718294]">{transaction.date}</p>
                <div className="sm:hidden">
                  <StatusBadge status={transaction.status} />
                </div>
              </div>

              <div className="flex items-center justify-between sm:block sm:text-right">
                <span className="text-xs text-[#8a99a6] sm:hidden">Amount</span>
                <div>
                  <p
                    className={`text-sm font-semibold ${
                      transaction.amount > 0
                        ? 'text-[#087a5e]'
                        : 'text-[#17324d]'
                    }`}
                  >
                    {transaction.amount > 0 ? '+' : '-'}
                    {money(transaction.amount)}
                  </p>
                  <div className="mt-1 hidden sm:block">
                    <StatusBadge status={transaction.status} />
                  </div>
                </div>
              </div>

              <span className="hidden text-[#9aa8b2] sm:block">
                <Icon name="arrow" size={16} />
              </span>
            </Link>
          ))}
        </div>

        {list.length === 0 && (
          <p className="px-5 py-12 text-center text-sm text-[#718294]">
            No transactions match your search.
          </p>
        )}
      </Panel>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Transaction detail                                                         */
/* -------------------------------------------------------------------------- */

export function CustomerTransactionDetail() {
  const { id } = useParams();
  const location = useLocation();

  const transaction =
    customerTransactions.find((item) => item.id === id) ??
    customerTransactions[0];

  const [verification, setVerification] = useState<
    'idle' | 'approved' | 'denied'
  >(
    transaction.status === 'Verification Required' ||
      transaction.status === 'Blocked'
      ? 'idle'
      : 'approved'
  );

  const unusual =
    transaction.status === 'Verification Required' ||
    transaction.status === 'Blocked';

  const cameFromDashboard = location.state?.from === 'dashboard';
  const backPath = cameFromDashboard
    ? '/customer'
    : '/customer/transactions';

  return (
    <div className="mx-auto max-w-5xl px-5 py-7 md:px-8 md:py-9">
      <Link
        to={backPath}
        className="inline-flex items-center gap-1 text-sm font-semibold text-[#087f7a] hover:text-[#066c68]"
      >
        ← {cameFromDashboard ? 'Back to home' : 'Back to transactions'}
      </Link>

      <div className="mt-6 flex flex-col justify-between gap-3 md:flex-row md:items-start">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#087f7a]">
            Transaction details
          </p>
          <h1 className="mt-2 text-[28px] font-semibold tracking-tight text-[#17324d]">
            {transaction.merchant}
          </h1>
          <p className="mt-1.5 text-sm text-[#718294]">
            Transaction #{transaction.id}
          </p>
        </div>
        <StatusBadge
          status={
            verification === 'approved'
              ? 'Completed'
              : verification === 'denied'
              ? 'Denied'
              : transaction.status
          }
        />
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <Panel className="p-5 sm:p-6">
          <p className="text-xs text-[#718294]">Amount</p>
          <p
            className={`mt-1.5 text-4xl font-semibold tracking-tight ${
              transaction.amount > 0 ? 'text-[#087a5e]' : 'text-[#17324d]'
            }`}
          >
            {transaction.amount > 0 ? '+' : '-'}
            {money(transaction.amount)}
          </p>

          <div className="mt-7 grid gap-x-6 gap-y-5 sm:grid-cols-2">
            {[
              ['Merchant', transaction.merchant],
              ['Currency', transaction.currency],
              ['Date and time', transaction.date],
              ['Transaction type', transaction.type],
              ['Payment channel', transaction.channel],
              ['Location', transaction.location],
            ].map(([label, value]) => (
              <div key={label}>
                <p className="text-xs text-[#718294]">{label}</p>
                <p className="mt-1 text-sm font-medium text-[#17324d]">{value}</p>
              </div>
            ))}
          </div>
        </Panel>

        {unusual ? (
          <Panel className="border-[#eadfbc] bg-[#fffaf0] p-5 sm:p-6">
            <div className="flex items-start gap-3">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[#ffedbd] text-[#946300]">
                <Icon name="alert" size={17} />
              </span>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#9a6700]">
                  Security check
                </p>
                <h2 className="mt-1 text-lg font-semibold text-[#3e3524]">
                  Do you recognize this transaction?
                </h2>
              </div>
            </div>

            <p className="mt-4 text-sm leading-6 text-[#76664a]">
              This transaction is different from your usual activity. Please
              confirm whether you made it.
            </p>

            {verification === 'idle' && (
              <div className="mt-6 grid gap-2.5">
                <button
                  type="button"
                  onClick={() => setVerification('approved')}
                  className="w-full rounded-xl bg-[#087f7a] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#066c68]"
                >
                  Yes, I recognize it
                </button>
                <button
                  type="button"
                  onClick={() => setVerification('denied')}
                  className="w-full rounded-xl border border-[#e7b9b4] bg-white px-4 py-3 text-sm font-semibold text-[#a9433d] transition hover:bg-[#fff7f6]"
                >
                  No, this is not mine
                </button>
              </div>
            )}

            {verification === 'approved' && (
              <div className="mt-6 rounded-xl bg-[#e9f7f1] p-4 text-sm font-semibold text-[#087a5e]">
                Transaction approved.
              </div>
            )}

            {verification === 'denied' && (
              <>
                <div className="mt-6 rounded-xl bg-[#fff0ee] p-4 text-sm font-semibold text-[#a9433d]">
                  Transaction rejected. Consider reporting this transaction as
                  fraud.
                </div>
                <Link
                  to="/customer/report-fraud"
                  className="mt-4 inline-flex text-sm font-semibold text-[#b44a43] hover:text-[#963b35]"
                >
                  Report this transaction →
                </Link>
              </>
            )}
          </Panel>
        ) : (
          <Panel className="border-[#cfe9e1] bg-[#f1faf7] p-5 sm:p-6">
            <div className="flex items-start gap-3">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-white text-[#087a5e] shadow-sm">
                <Icon name="check" />
              </span>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#087a5e]">
                  Security
                </p>
                <h2 className="mt-1 text-lg font-semibold text-[#17324d]">
                  This transaction looks normal
                </h2>
              </div>
            </div>
            <p className="mt-3 text-sm leading-6 text-[#5f756f]">
              It matches your recent activity and no action is needed.
            </p>
          </Panel>
        )}
      </div>

      {unusual && (
        <Panel className="mt-5 p-5 sm:p-6">
          <h2 className="text-base font-semibold text-[#17324d]">
            Why was this flagged?
          </h2>

          <div className="mt-5 grid gap-3 md:grid-cols-3">
            <Reason
              icon="card"
              title="Amount"
              detail="The purchase amount is outside your usual spending range."
            />
            <Reason
              icon="location"
              title="Location or device"
              detail="The activity may be coming from somewhere you do not normally use."
            />
            <Reason
              icon="clock"
              title="Timing"
              detail="The transaction occurred at a time that is less typical for you."
            />
          </div>
        </Panel>
      )}
    </div>
  );
}

function Reason({
  icon,
  title,
  detail,
}: {
  icon: 'card' | 'location' | 'clock';
  title: string;
  detail: string;
}) {
  return (
    <div className="rounded-xl bg-[#f7fafb] p-4">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-white text-[#087f7a] shadow-sm">
        <Icon name={icon} size={16} />
      </span>
      <p className="mt-3 text-sm font-semibold text-[#17324d]">{title}</p>
      <p className="mt-1.5 text-xs leading-5 text-[#718294]">{detail}</p>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Normal activity                                                            */
/* -------------------------------------------------------------------------- */

function NormalBehaviorContent() {
  return (
    <div className="p-5 sm:p-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Behavior label="Typical spending" value="$20 - $120" />
        <Behavior label="Average transaction" value="$42.50" />
        <Behavior label="Typical frequency" value="3 - 5 per day" />
        <Behavior label="Typical time" value="12 PM - 8 PM" />
      </div>

      <div className="mt-7 grid gap-6 border-t border-[#e7edef] pt-6 md:grid-cols-3">
        <ActivityBars
          title="Normal locations"
          items={[
            ['New York', 82],
            ['New Jersey', 12],
            ['Other', 6],
          ]}
        />
        <ActivityBars
          title="Typical devices"
          items={[
            ['iPhone 15 Pro', 72],
            ['MacBook Pro', 18],
            ['Other', 10],
          ]}
        />
        <ActivityBars
          title="Common categories"
          items={[
            ['Groceries', 32],
            ['Restaurants', 21],
            ['Shopping', 18],
          ]}
        />
      </div>
    </div>
  );
}

function Behavior({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl bg-[#f7fafb] p-4">
      <p className="text-xs text-[#718294]">{label}</p>
      <p className="mt-2 text-sm font-semibold text-[#17324d]">{value}</p>
    </div>
  );
}

function ActivityBars({
  title,
  items,
}: {
  title: string;
  items: [string, number][];
}) {
  return (
    <div>
      <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[#8a99a6]">
        {title}
      </p>
      <div className="mt-3 space-y-3">
        {items.map(([label, percent]) => (
          <div key={label}>
            <div className="mb-1 flex justify-between text-xs text-[#53687b]">
              <span>{label}</span>
              <strong className="text-[#17324d]">{percent}%</strong>
            </div>
            <div className="h-1.5 rounded-full bg-[#e7edef]">
              <div
                className="h-1.5 rounded-full bg-[#0a8f89]"
                style={{ width: `${percent}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function NormalBehaviorPage() {
  return (
    <div className="mx-auto max-w-6xl px-5 py-7 md:px-8 md:py-9">
      <Heading
        label="Your activity"
        title="Normal activity"
        detail="These are the patterns VeriPay normally sees from your account."
      />

      <Panel className="overflow-hidden">
        <div className="border-b border-[#dce7e9] bg-[#f1faf8] px-5 py-5 sm:px-6">
          <h2 className="text-base font-semibold text-[#17324d]">
            Your usual activity
          </h2>
          <p className="mt-1 text-sm text-[#718294]">
            This information helps explain why an unusual transaction may
            require verification.
          </p>
        </div>
        <NormalBehaviorContent />
      </Panel>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Security                                                                   */
/* -------------------------------------------------------------------------- */

export function SecurityPage() {
  return (
    <div className="mx-auto max-w-6xl px-5 py-7 md:px-8 md:py-9">
      <Heading
        label="Protection"
        title="Security"
        detail="Keep your account and transactions protected."
      />

      <Panel className="border-[#cfe9e1] bg-[#f1faf7] p-5 sm:p-6">
        <div className="flex items-center gap-4">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-white text-[#087a5e] shadow-sm">
            <Icon name="shield" />
          </span>
          <div>
            <h2 className="text-base font-semibold text-[#17324d]">
              Your account is protected
            </h2>
            <p className="mt-1 text-sm text-[#5f756f]">
              No urgent security action is required.
            </p>
          </div>
        </div>
      </Panel>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <SecuritySetting
          title="Two-factor authentication"
          value="Enabled"
          detail="Extra protection is active for your sign-ins."
        />
        <SecuritySetting
          title="Transaction verification"
          value="Enabled"
          detail="Unusual transactions may require your approval."
        />
        <SecuritySetting
          title="Trusted devices"
          value="2 trusted devices"
          detail="Devices you recognize can access your account."
          link="/customer/security/devices"
        />
        <SecuritySetting
          title="Security activity"
          value="Review recent activity"
          detail="See important logins and security events."
          link="/customer/security/activity"
        />
      </div>
    </div>
  );
}

function SecuritySetting({
  title,
  value,
  detail,
  link,
}: {
  title: string;
  value: string;
  detail: string;
  link?: string;
}) {
  return (
    <Panel className="p-5">
      <p className="text-sm font-semibold text-[#17324d]">{title}</p>
      <p className="mt-2 text-sm font-semibold text-[#087a5e]">{value}</p>
      <p className="mt-1.5 text-xs leading-5 text-[#718294]">{detail}</p>
      {link && (
        <Link
          to={link}
          className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-[#087f7a] hover:text-[#066c68]"
        >
          View
          <Icon name="arrow" size={15} />
        </Link>
      )}
    </Panel>
  );
}

export function DevicesPage() {
  return (
    <div className="mx-auto max-w-5xl px-5 py-7 md:px-8 md:py-9">
      <Link
        to="/customer/security"
        className="text-sm font-semibold text-[#087f7a]"
      >
        ← Back to security
      </Link>

      <div className="mt-6">
        <Heading
          label="Security"
          title="Trusted devices"
          detail="Review devices that have access to your account."
        />
      </div>

      <div className="space-y-3">
        {customerDevices.map((device) => (
          <Panel
            key={device.name}
            className="flex flex-col justify-between gap-4 p-5 sm:flex-row sm:items-center"
          >
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-sm font-semibold text-[#17324d]">
                  {device.name}
                </h2>
                <StatusBadge
                  status={device.trusted ? 'Trusted' : 'New device'}
                />
              </div>
              <p className="mt-2 text-xs text-[#718294]">
                {device.os} · Last active {device.lastActive}
              </p>
            </div>

            <button
              type="button"
              className={`rounded-xl px-3.5 py-2 text-xs font-semibold ${
                device.trusted
                  ? 'border border-[#d5e1e4] text-[#53687b] hover:bg-[#f7fafb]'
                  : 'border border-[#e7b9b4] text-[#a9433d] hover:bg-[#fff7f6]'
              }`}
            >
              {device.trusted ? 'Remove device' : "This isn't my device"}
            </button>
          </Panel>
        ))}
      </div>
    </div>
  );
}

export function ActivityPage() {
  return (
    <div className="mx-auto max-w-5xl px-5 py-7 md:px-8 md:py-9">
      <Link
        to="/customer/security"
        className="text-sm font-semibold text-[#087f7a]"
      >
        ← Back to security
      </Link>

      <div className="mt-6">
        <Heading
          label="Security"
          title="Security activity"
          detail="Important activity on your account."
        />
      </div>

      <Panel className="divide-y divide-[#edf1f2]">
        {activityEvents.map(([time, title, detail, tone]) => (
          <div key={`${time}-${title}`} className="flex gap-4 p-5">
            <span
              className={`mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-full ${
                tone === 'attention'
                  ? 'bg-[#fff2cf] text-[#946300]'
                  : 'bg-[#e9f7f1] text-[#087a5e]'
              }`}
            >
              <Icon
                name={tone === 'attention' ? 'alert' : 'check'}
                size={15}
              />
            </span>
            <div>
              <p className="text-xs text-[#8a99a6]">{time}</p>
              <p className="mt-1 text-sm font-semibold text-[#17324d]">{title}</p>
              <p className="mt-1 text-xs leading-5 text-[#718294]">{detail}</p>
            </div>
          </div>
        ))}
      </Panel>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Notifications                                                              */
/* -------------------------------------------------------------------------- */

export function NotificationsPage() {
  const [transactionAlerts, setTransactionAlerts] = useState(true);
  const [securityAlerts, setSecurityAlerts] = useState(true);
  const [marketingAlerts, setMarketingAlerts] = useState(false);

  return (
    <div className="mx-auto max-w-5xl px-5 py-7 md:px-8 md:py-9">
      <Heading
        label="Preferences"
        title="Notifications"
        detail="Choose which account alerts you want to receive."
      />

      <Panel className="divide-y divide-[#edf1f2]">
        <NotificationSetting
          title="Transaction alerts"
          detail="Get notified when transactions are completed, pending, or flagged."
          enabled={transactionAlerts}
          onChange={setTransactionAlerts}
        />
        <NotificationSetting
          title="Security alerts"
          detail="Get notified about important sign-ins, devices, and security events."
          enabled={securityAlerts}
          onChange={setSecurityAlerts}
        />
        <NotificationSetting
          title="Product updates"
          detail="Receive occasional updates about VeriPay products and services."
          enabled={marketingAlerts}
          onChange={setMarketingAlerts}
        />
      </Panel>
    </div>
  );
}

function NotificationSetting({
  title,
  detail,
  enabled,
  onChange,
}: {
  title: string;
  detail: string;
  enabled: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-5 p-5">
      <div>
        <p className="text-sm font-semibold text-[#17324d]">{title}</p>
        <p className="mt-1 max-w-xl text-xs leading-5 text-[#718294]">{detail}</p>
      </div>

      <button
        type="button"
        onClick={() => onChange(!enabled)}
        aria-pressed={enabled}
        className={`relative h-7 w-12 shrink-0 rounded-full transition ${
          enabled ? 'bg-[#0a8f89]' : 'bg-[#c8d2d7]'
        }`}
      >
        <span
          className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow-sm transition ${
            enabled ? 'left-6' : 'left-1'
          }`}
        />
      </button>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Report fraud                                                               */
/* -------------------------------------------------------------------------- */

export function ReportFraudPage() {
  const [submitted, setSubmitted] = useState(false);

  return (
    <div className="mx-auto max-w-3xl px-5 py-7 md:px-8 md:py-9">
      <Heading
        label="Account safety"
        title="Report fraud"
        detail="Tell us about activity you do not recognize."
      />

      {submitted ? (
        <Panel className="border-[#cfe9e1] bg-[#f1faf7] p-8 text-center">
          <span className="mx-auto grid h-11 w-11 place-items-center rounded-full bg-white text-[#087a5e] shadow-sm">
            <Icon name="check" />
          </span>
          <h2 className="mt-4 text-lg font-semibold text-[#17324d]">
            Your report has been submitted
          </h2>
          <p className="mt-1 text-sm text-[#5f756f]">
            Reference number: FR-12345
          </p>
          <Link
            to="/customer"
            className="mt-5 inline-flex text-sm font-semibold text-[#087f7a]"
          >
            Return to home →
          </Link>
        </Panel>
      ) : (
        <Panel className="p-5 sm:p-6">
          <label className="block text-sm font-semibold text-[#17324d]">
            What would you like to report?
            <select className="mt-2 w-full rounded-xl border border-[#d5e1e4] bg-white px-3 py-2.5 text-sm font-normal text-[#53687b] outline-none focus:border-[#0a8f89]">
              <option>Unrecognized transaction</option>
              <option>Stolen card</option>
              <option>Suspicious account activity</option>
              <option>Unknown device</option>
              <option>Account compromise</option>
            </select>
          </label>

          <label className="mt-5 block text-sm font-semibold text-[#17324d]">
            Transaction
            <select className="mt-2 w-full rounded-xl border border-[#d5e1e4] bg-white px-3 py-2.5 text-sm font-normal text-[#53687b] outline-none focus:border-[#0a8f89]">
              <option>TX-89231 - Amazon - $850.00</option>
              <option>TX-89202 - Northstar Travel - $2,340.00</option>
            </select>
          </label>

          <label className="mt-5 block text-sm font-semibold text-[#17324d]">
            What happened?
            <textarea
              className="mt-2 min-h-32 w-full rounded-xl border border-[#d5e1e4] bg-white px-3 py-2.5 text-sm font-normal text-[#17324d] outline-none placeholder:text-[#9aa8b2] focus:border-[#0a8f89] focus:ring-4 focus:ring-[#0a8f89]/10"
              placeholder="Tell us what you noticed..."
            />
          </label>

          <button
            type="button"
            onClick={() => setSubmitted(true)}
            className="mt-5 w-full rounded-xl bg-[#17324d] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#10283d]"
          >
            Submit fraud report
          </button>
        </Panel>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Profile                                                                    */
/* -------------------------------------------------------------------------- */

export function ProfilePage() {
  return (
    <div className="mx-auto max-w-5xl px-5 py-7 md:px-8 md:py-9">
      <Heading
        label="Personal details"
        title="Profile"
        detail="View your personal information."
      />

      <Panel className="p-5 sm:p-6">
        <h2 className="text-base font-semibold text-[#17324d]">
          Personal information
        </h2>

        <div className="mt-6 grid gap-5 sm:grid-cols-2">
          {[
            ['First name', 'Jordan'],
            ['Last name', 'Lee'],
            ['Email', 'j•••••@example.com'],
            ['Phone number', '+1 (•••) •••-0198'],
            ['Customer ID', 'CUS-18492'],
          ].map(([label, value]) => (
            <div key={label}>
              <p className="text-xs text-[#718294]">{label}</p>
              <p className="mt-1 text-sm font-medium text-[#17324d]">{value}</p>
            </div>
          ))}
        </div>

      </Panel>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Help                                                                        */
/* -------------------------------------------------------------------------- */

export function HelpPage() {
  const faqs = [
    {
      question: 'Why was my transaction flagged?',
      answer:
        'VeriPay may flag activity when the amount, location, device, timing, or other behavior differs from your normal activity.',
    },
    {
      question: 'What should I do if I do not recognize a transaction?',
      answer:
        'Open the transaction, choose that you do not recognize it, and use the fraud reporting option to provide more information.',
    },
    {
      question: 'How can I review my trusted devices?',
      answer:
        'Go to Security and select Trusted devices to review devices that have access to your account.',
    },
    {
      question: 'How do I contact support?',
      answer:
        'For account or transaction concerns, use the fraud reporting flow or the support contact provided by your bank.',
    },
  ];

  return (
    <div className="mx-auto max-w-5xl px-5 py-7 md:px-8 md:py-9">
      <Heading
        label="Support"
        title="Help"
        detail="Find answers to common account and security questions."
      />

      <Panel className="divide-y divide-[#edf1f2]">
        {faqs.map((faq) => (
          <div key={faq.question} className="p-5">
            <h2 className="text-sm font-semibold text-[#17324d]">{faq.question}</h2>
            <p className="mt-2 text-xs leading-5 text-[#718294]">{faq.answer}</p>
          </div>
        ))}
      </Panel>

      <Panel className="mt-4 border-[#cfe9e1] bg-[#f1faf7] p-5">
        <h2 className="text-sm font-semibold text-[#17324d]">
          Need to report suspicious activity?
        </h2>
        <p className="mt-1.5 text-xs text-[#718294]">
          If you see something you do not recognize, report it as soon as
          possible.
        </p>
        <Link
          to="/customer/report-fraud"
          className="mt-4 inline-flex rounded-xl bg-[#087f7a] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#066c68]"
        >
          Report fraud
        </Link>
      </Panel>
    </div>
  );
}

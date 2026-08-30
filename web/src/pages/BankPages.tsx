import { useMemo, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { auditLogs, bankTransactions, customers, merchants, notifications, type BankTransaction } from '../bankData';

const btnPrimary = 'rounded-lg bg-[#43cddd] px-4 py-2 text-sm font-bold text-[#29265f] shadow-sm transition hover:bg-[#5bd8e5] disabled:cursor-not-allowed disabled:opacity-40';
const btnSecondary = 'rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-sm font-bold text-ink transition hover:bg-white/20';

const badge = (value: string) => { const normalized = value.toUpperCase(); return normalized.includes('CRITICAL') || normalized.includes('BLOCKED') || normalized.includes('DENIED') ? 'bg-red-600 text-white' : normalized.includes('HIGH') ? 'bg-orange-100 text-orange-800' : normalized.includes('BLOCK') ? 'bg-red-50 text-red-700' : normalized.includes('MEDIUM') || normalized.includes('VERIFY') || normalized.includes('REVIEW') || normalized.includes('PENDING') || normalized.includes('VERIFICATION_REQUIRED') ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'; };
const Money = ({ value }: { value: number }) => <>{new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(value)}</>;
const Pill = ({ value }: { value: string }) => <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${badge(value)}`}>{value.replaceAll('_', ' ')}</span>;
function RiskBadge({ score, level }: { score: number; level: string }) {
  const styles =
    level === 'CRITICAL'
      ? 'bg-red-50 text-red-700 border-red-200'
      : level === 'HIGH'
        ? 'bg-orange-50 text-orange-700 border-orange-200'
        : level === 'MEDIUM'
          ? 'bg-amber-50 text-amber-700 border-amber-200'
          : 'bg-emerald-50 text-emerald-700 border-emerald-200';

  return (
    <div className={`inline-flex min-w-[72px] flex-col items-center rounded-lg border px-2.5 py-1.5 ${styles}`}>
      <span className="text-sm font-bold leading-none">{score}</span>
      <span className="mt-1 text-[10px] font-extrabold uppercase tracking-wide">
        {level}
      </span>
    </div>
  );
}
function PageTitle({ eyebrow, title, detail, action }: { eyebrow: string; title: string; detail: string; action?: ReactNode }) { return <div className="mb-7 flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-700">{eyebrow}</p><h1 className="mt-2 text-3xl font-semibold tracking-tight">{title}</h1><p className="mt-2 text-sm text-slate-500">{detail}</p></div>{action}</div>; }
function Panel({ children, className = '' }: { children: ReactNode; className?: string }) { return <section className={`rounded-xl border border-slate-200 bg-white shadow-sm ${className}`}>{children}</section>; }

export function BankDashboard() {
  const highRisk = bankTransactions.filter(
    (transaction) =>
      transaction.level === 'HIGH' || transaction.level === 'CRITICAL'
  );

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <PageTitle
        eyebrow="BANK CONSOLE · 31 AUGUST 2026"
        title="Good afternoon, Admin"
        detail="A clear view of today's payment risk."
      />

      {/* PRIORITY TRANSACTIONS */}
      <Panel className="mt-6 overflow-hidden border-[#fac180]">
        <div className="flex items-center justify-between border-b border-[#fac180] px-5 py-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-red-600" />
              <h2 className="text-lg font-semibold text-[#29265f]">
                Priority transactions
              </h2>
            </div>

            <p className="mt-1 text-xs text-slate-500">
              Critical and high-risk activity requiring review now.
            </p>
          </div>

          <Link
            to="/bank/alerts"
            className="text-sm font-semibold text-[#29265f]"
          >
            View alerts -&gt;
          </Link>
        </div>

        <div className="divide-y divide-[#fac180]">
          {highRisk.slice(0, 3).map((item) => {
            const critical = item.level === 'CRITICAL';

            return (
              <div
                key={item.id}
                className={`flex items-center justify-between border-l-4 px-5 py-4 ${
                  critical
                    ? 'border-red-500 bg-red-50'
                    : 'border-orange-400 bg-orange-50/70'
                }`}
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      to={`/tx/${item.id}`}
                      className="font-semibold text-[#29265f]"
                    >
                      {item.id} · {item.merchant}
                    </Link>

                    <span
                      className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${
                        critical
                          ? 'bg-red-600 text-white'
                          : 'bg-orange-100 text-orange-800'
                      }`}
                    >
                      {item.level}
                    </span>
                  </div>

                  <p className="mt-1 text-xs text-slate-600">
                    {item.customer} · {item.reason}
                  </p>
                </div>

                <div className="ml-5 flex shrink-0 items-center gap-4">
                  <span className="font-semibold text-[#29265f]">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: item.currency,
                    }).format(item.amount)}
                  </span>

                  <span
                    className={`rounded-full px-3 py-1.5 text-xs font-bold ${
                      critical
                        ? 'bg-red-600 text-white'
                        : 'bg-orange-100 text-orange-800'
                    }`}
                  >
                    {item.score} score
                  </span>

                  <Link
                    to={`/tx/${item.id}`}
                    className="text-sm font-bold text-[#29265f] hover:underline"
                  >
                    Review -&gt;
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </Panel>

      {/* KPI SUMMARY */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi
          label="Transactions today"
          value="24,891"
          change="+6.2% vs yesterday"
        />

        <Kpi
          label="Volume today"
          value="$8.42M"
          change="+4.8% vs yesterday"
        />

        <Kpi
          label="Fraud detected"
          value="1,284"
          change="+8.4% vs yesterday"
          tone="red"
        />

        <Kpi
          label="Blocked"
          value="642"
          change="+3.7% vs yesterday"
          tone="red"
        />
      </div>

      {/* GRAPH + REVIEW QUEUE */}
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.6fr_0.9fr]">
        <Panel>
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
            <div>
              <h2 className="font-semibold">Risk activity</h2>

              <p className="mt-1 text-xs text-slate-500">
                Example authorization volume by hour
              </p>
            </div>

            <Link
              to="/bank/analytics"
              className="text-sm font-semibold text-[#29265f]"
            >
              Details -&gt;
            </Link>
          </div>

          <div className="px-5 py-6">
            <LineChart />

            <div className="mt-4 flex gap-5 text-xs text-slate-500">
              <span>
                <i className="mr-2 inline-block h-2 w-2 rounded-full bg-[#43cddd]" />
                Normal
              </span>

              <span>
                <i className="mr-2 inline-block h-2 w-2 rounded-full bg-[#fac180]" />
                Elevated
              </span>
            </div>
          </div>
        </Panel>

        <section className="rounded-xl border border-[#43cddd] bg-[#e5f8fc] p-6">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#29265f]">
            Review queue
          </p>

          <p className="mt-4 text-4xl font-semibold text-[#29265f]">
            {Math.min(highRisk.length, 3)}
          </p>

          <p className="mt-1 text-sm text-[#29265f]">
            priority cases
          </p>

          <p className="mt-5 text-sm leading-6 text-slate-600">
            Start with red critical cases, then review orange high-risk cases.
          </p>

          <Link
            to="/bank/transactions"
            className="mt-5 inline-block rounded-md bg-[#29265f] px-4 py-2.5 text-sm font-bold text-white"
          >
            Open queue
          </Link>
        </section>
      </div>
    </div>
  );
}
function Kpi({ label, value, change, tone = 'slate' }: { label: string; value: string; change: string; tone?: string }) { return <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between"><p className="text-sm font-medium text-slate-500">{label}</p><span className={`h-2 w-2 rounded-full ${tone === 'red' ? 'bg-red-500' : tone === 'amber' ? 'bg-amber-400' : tone === 'teal' ? 'bg-teal-500' : 'bg-slate-300'}`} /></div><p className="mt-3 text-2xl font-semibold tracking-tight">{value}</p><p className={`mt-2 text-xs ${change.startsWith('-') ? 'text-emerald-700' : tone === 'red' ? 'text-red-700' : 'text-teal-700'}`}>{change}</p></div>; }
function LineChart() { return <div className="relative h-52 border-b border-l border-slate-200 bg-[linear-gradient(to_bottom,transparent_49%,#e2e8f0_50%,transparent_51%)]"><svg viewBox="0 0 800 220" className="h-full w-full" role="img" aria-label="Transaction volume and fraud trend chart"><polyline fill="none" stroke="#0d9488" strokeWidth="4" points="0,145 100,128 200,150 300,100 400,112 500,70 600,95 700,56 800,72" /><polyline fill="none" stroke="#ef4444" strokeWidth="3" points="0,190 100,180 200,185 300,165 400,175 500,130 600,150 700,112 800,125" /><path d="M0 145 L100 128 L200 150 L300 100 L400 112 L500 70 L600 95 L700 56 L800 72 L800 220 L0 220Z" fill="#0d9488" opacity=".08" /></svg><div className="absolute -bottom-6 left-0 right-0 flex justify-between text-[10px] text-slate-400"><span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>Now</span></div></div>; }
function VerificationBadge({ value }: { value: string }) {
  const normalized = value.toUpperCase();

  const styles =
    normalized === 'FAILED'
      ? 'bg-red-50 text-red-700 border-red-200'
      : normalized === 'PASSED'
        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
        : normalized === 'PENDING'
          ? 'bg-amber-50 text-amber-700 border-amber-200'
          : 'bg-slate-50 text-slate-600 border-slate-200';

  return (
    <span className={`inline-flex rounded-full border px-3 py-1.5 text-[10px] font-extrabold uppercase tracking-wide ${styles}`}>
      {value.replaceAll('_', ' ')}
    </span>
  );
}

export function TransactionsPage() { const [query, setQuery] = useState(''); const [level, setLevel] = useState('ALL'); const [status, setStatus] = useState('ALL'); const filtered = useMemo(() => bankTransactions.filter((item) => `${item.id} ${item.customer} ${item.merchant}`.toLowerCase().includes(query.toLowerCase()) && (level === 'ALL' || item.level === level) && (status === 'ALL' || item.status === status)), [query, level, status]); return <div className="mx-auto max-w-7xl px-6 py-8"><PageTitle eyebrow="Operations" title="Transactions" detail="Search, filter, and review authorization activity." action={<button onClick={() => downloadCsv(filtered)} className="rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold hover:bg-slate-50">Export CSV</button>} /><Panel><div className="flex flex-col gap-3 border-b border-slate-200 p-5 lg:flex-row"><input value={query} onChange={(event) => setQuery(event.target.value)} className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-teal-600" placeholder="Search transaction ID, customer, merchant..." /><select value={level} onChange={(event) => setLevel(event.target.value)} className="rounded-md border border-slate-300 px-3 py-2.5 text-sm"><option value="ALL">All risk levels</option><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select><select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded-md border border-slate-300 px-3 py-2.5 text-sm"><option value="ALL">All statuses</option><option>PENDING</option><option>APPROVED</option><option>BLOCKED</option><option>VERIFICATION_REQUIRED</option></select></div><TransactionRows items={filtered} detailed /></Panel><p className="mt-3 text-xs text-slate-500">Showing {filtered.length} of {bankTransactions.length} transactions · Pagination connects to the transaction API.</p></div>; }
function TransactionRows({ items, detailed = false }: { items: BankTransaction[]; detailed?: boolean }) { return <div className="overflow-x-auto"><table className="min-w-[900px] w-full text-left text-sm"><thead className="bg-slate-50 text-[11px] uppercase tracking-[0.12em] text-slate-500"><tr>{(detailed ? ['Transaction', 'Date / time', 'Customer', 'Merchant', 'Amount', 'Risk', 'Decision', 'Verification', 'Status'] : ['Transaction', 'Customer', 'Merchant', 'Amount', 'Risk', 'Decision', 'Status']).map((heading) => <th key={heading} className="px-5 py-3 font-bold">{heading}</th>)}</tr></thead><tbody>{items.map((item) => <tr key={item.id} className="border-t border-slate-100 hover:bg-slate-50"> <td className="px-5 py-4"><Link className="font-semibold text-teal-700" to={`/tx/${item.id}`}>{item.id}</Link></td>{detailed && <td className="px-5 py-4 text-slate-500">Today, {item.time}</td>}<td className="px-5 py-4 text-slate-600">{item.customer}</td><td className="px-5 py-4">{item.merchant}</td><td className="px-5 py-4 font-semibold"><Money value={item.amount} /></td><td className="px-5 py-4">
  <RiskBadge score={item.score} level={item.level} />
</td><td className="px-5 py-4"><Pill value={item.decision} /> </td>{detailed && (<td className="px-5 py-4"><VerificationBadge value={item.verification} /></td> )}<td className="px-5 py-4"><Pill value={item.status} /></td></tr>)}</tbody></table>{items.length === 0 && <p className="px-5 py-10 text-center text-sm text-slate-500">No transactions match the selected filters.</p>}</div>; }
function downloadCsv(items: BankTransaction[]) { const csv = ['id,customer,merchant,amount,score,level,decision,status', ...items.map((item) => [item.id, item.customer, item.merchant, item.amount, item.score, item.level, item.decision, item.status].join(','))].join('\n'); const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'veripay-transactions.csv'; anchor.click(); URL.revokeObjectURL(url); }
function StatusBadge({ value }: { value: string }) {
  const normalized = value.toUpperCase();

  const styles =
    normalized === 'BLOCKED'
      ? 'bg-red-600 text-white border-red-600'
      : normalized === 'RESOLVED'
        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
        : normalized === 'INVESTIGATING'
          ? 'bg-blue-50 text-blue-700 border-blue-200'
          : normalized === 'OPEN'
            ? 'bg-amber-50 text-amber-700 border-amber-200'
            : normalized === 'PENDING'
              ? 'bg-amber-50 text-amber-700 border-amber-200'
              : 'bg-slate-50 text-slate-600 border-slate-200';

  return (
    <span className={`inline-flex rounded-full border px-3 py-1.5 text-[10px] font-extrabold uppercase tracking-wide ${styles}`}>
      {value.replaceAll('_', ' ')}
    </span>
  );
}
export function AlertsPage() { const [resolved, setResolved] = useState<string[]>([]); const alerts = bankTransactions.filter((item) => item.score >= 78); return <div className="mx-auto max-w-7xl px-6 py-8"><PageTitle eyebrow="Investigation" title="Fraud & Alerts" detail="Prioritize suspicious activity and assign analyst follow-up." /><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><Kpi label="Open alerts" value="38" change="+5 today" tone="amber" /><Kpi label="Critical alerts" value="6" change="2 unassigned" tone="red" /><Kpi label="Investigations" value="14" change="4 in progress" /><Kpi label="Confirmed fraud" value="92" change="+11 this week" tone="red" /></div><Panel className="mt-6 overflow-hidden"><div className="border-b border-slate-200 px-5 py-4"><h2 className="font-semibold">Active alert queue</h2></div><table className="min-w-[850px] w-full text-left text-sm"><thead className="bg-slate-50 text-[11px] uppercase tracking-[0.12em] text-slate-500"><tr>{['Alert', 'Transaction', 'Risk', 'Severity', 'Customer', 'Merchant', 'Assigned analyst', 'Status', 'Action'].map((heading) => <th key={heading} className="px-5 py-3 font-bold">{heading}</th>)}</tr></thead><tbody>{alerts.map((item, index) => { const alertId = `ALT-${4412 - index}`; const done = resolved.includes(alertId); return <tr
  key={alertId}
  className={`border-t border-slate-100 ${
    item.level === 'CRITICAL'
      ? 'bg-red-50/40'
      : item.level === 'HIGH'
        ? 'bg-orange-50/30'
        : 'hover:bg-slate-50'
  }`}
><td className="px-5 py-4 font-semibold">{alertId}</td><td className="px-5 py-4"><Link className="text-teal-700" to={`/tx/${item.id}`}>{item.id}</Link></td><td className="px-5 py-4">
  <RiskBadge score={item.score} level={item.level} />
</td><td className="px-5 py-4"><Pill value={item.level} /></td><td className="px-5 py-4">{item.customer}</td><td className="px-5 py-4">{item.merchant}</td><td className="px-5 py-4 text-slate-500">{index % 2 ? 'S. Patel' : 'Unassigned'}</td><td className="px-5 py-4">
  <StatusBadge
    value={done ? 'RESOLVED' : index % 2 ? 'INVESTIGATING' : 'OPEN'}
  />
</td><td className="px-5 py-4"><button disabled={done} onClick={() => setResolved((current) => [...current, alertId])} className="text-xs font-semibold text-teal-700 disabled:text-slate-400">{done ? 'Resolved' : 'Resolve'}</button></td></tr>; })}</tbody></table></Panel></div>; }

export function AnalyticsPage() { return <div className="mx-auto max-w-7xl px-6 py-8"><PageTitle eyebrow="Intelligence" title="Risk Analytics" detail="Measure model outcomes and fraud patterns across the portfolio." action={<select className="glass-field rounded-lg px-3 py-2.5 text-sm"><option>Last 30 days</option><option>Last 7 days</option><option>Last 90 days</option></select>} /><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><Kpi label="Average risk score" value="34.8" change="-2.4% vs prior period" tone="teal" /><Kpi label="Fraud rate" value="5.16%" change="+0.4 pts" tone="amber" /><Kpi label="False positive rate" value="2.8%" change="-0.6 pts" tone="teal" /><Kpi label="Verification rate" value="7.7%" change="+1.1 pts" tone="amber" /></div><div className="mt-6 grid gap-6 lg:grid-cols-2"><ChartPanel title="Risk score distribution"><BarChart values={[72, 18, 8, 2]} labels={['Low', 'Medium', 'High', 'Critical']} /></ChartPanel><ChartPanel title="Decision mix"><BarChart values={[72, 20, 8]} labels={['Allow', 'Verify', 'Block']} /></ChartPanel><ChartPanel title="Fraud by transaction type"><BarChart values={[62, 24, 14]} labels={['Purchase', 'Transfer', 'Withdrawal']} /></ChartPanel><ChartPanel title="Fraud by merchant category"><BarChart values={[48, 28, 16, 8]} labels={['E-commerce', 'Travel', 'Retail', 'Digital goods']} /></ChartPanel></div></div>; }
function ChartPanel({ title, children }: { title: string; children: ReactNode }) { return <Panel className="p-5"><h2 className="font-semibold text-ink">{title}</h2><p className="mt-1 text-xs text-ink-muted">Relative portfolio share</p><div className="mt-6">{children}</div></Panel>; }
function BarChart({ values, labels }: { values: number[]; labels: string[] }) { return <div className="space-y-4">{values.map((value, index) => <div key={labels[index]}><div className="mb-1 flex justify-between text-xs"><span className="text-ink-muted">{labels[index]}</span><strong className="text-ink">{value}%</strong></div><div className="h-3 rounded-full bg-ink/[0.07] dark:bg-white/10"><div className={`h-3 rounded-full ${index === values.length - 1 ? 'bg-red-500/85' : index === values.length - 2 ? 'bg-amber-400/85' : 'bg-accent/80'}`} style={{ width: `${value}%` }} /></div></div>)}</div>; }

export function CustomersPage() { const [query, setQuery] = useState(''); const list = customers.filter((item) => `${item.id} ${item.name} ${item.email}`.toLowerCase().includes(query.toLowerCase())); return <div className="mx-auto max-w-7xl px-6 py-8"><PageTitle eyebrow="Monitoring" title="Customers" detail="Review customer risk posture without exposing unnecessary sensitive data." /><Panel><div className="border-b border-slate-200 p-5"><input value={query} onChange={(event) => setQuery(event.target.value)} className="w-full max-w-lg rounded-md border border-slate-300 px-3 py-2.5 text-sm" placeholder="Search customer ID, name, email..." /></div><div className="overflow-x-auto"><table className="min-w-[900px] w-full text-left text-sm"><thead className="bg-slate-50 text-[11px] uppercase tracking-[0.12em] text-slate-500"><tr>{['Customer', 'Contact', 'Card', 'Transactions', 'Volume', 'Fraud alerts', 'Risk status', 'Account'].map((heading) => <th key={heading} className="px-5 py-3 font-bold">{heading}</th>)}</tr></thead><tbody>{list.map((item) => <tr key={item.id} className="border-t border-slate-100"><td className="px-5 py-4"><p className="font-semibold">{item.name}</p><p className="text-xs text-slate-500">{item.id}</p></td><td className="px-5 py-4 text-slate-500">{item.email}</td><td className="px-5 py-4 font-mono text-xs tracking-wider">•••• {item.cardLast4}</td><td className="px-5 py-4">{item.transactions}</td><td className="px-5 py-4 font-semibold">{item.volume}</td><td className="px-5 py-4">{item.alerts}</td><td className="px-5 py-4"><Pill value={item.risk} /></td><td className="px-5 py-4"><Pill value={item.account} /></td></tr>)}</tbody></table></div></Panel></div>; }

export function MerchantsPage() { return <div className="mx-auto max-w-7xl px-6 py-8"><PageTitle eyebrow="Monitoring" title="Merchants" detail="Monitor merchant exposure, fraud rate, and authorization outcomes." /><Panel className="overflow-hidden"><table className="min-w-[850px] w-full text-left text-sm"><thead className="bg-white/40 text-[11px] uppercase tracking-[0.14em] text-ink-subtle dark:bg-white/[0.04]"><tr>{['Merchant', 'Category', 'Volume', 'Transactions', 'Fraud rate', 'Avg risk', 'Block rate', 'Status'].map((heading) => <th key={heading} className="px-5 py-3 font-semibold">{heading}</th>)}</tr></thead><tbody>{merchants.map((item) => <tr key={item.id} className="border-t border-separator transition-colors hover:bg-white/50 dark:hover:bg-white/[0.04]"><td className="px-5 py-4"><p className="font-semibold text-ink">{item.name}</p><p className="text-xs text-ink-subtle">{item.id}</p></td><td className="px-5 py-4 text-ink-muted">{item.category}</td><td className="px-5 py-4 font-semibold text-ink">{item.volume}</td><td className="px-5 py-4 tabular-nums text-ink">{item.transactions.toLocaleString()}</td><td className="px-5 py-4"><Pill value={item.fraudRate} /></td><td className="px-5 py-4 tabular-nums text-ink">{item.score}</td><td className="px-5 py-4 text-ink">{item.blockRate}</td><td className="px-5 py-4"><Pill value={item.status} /></td></tr>)}</tbody></table></Panel></div>; }

export function PoliciesPage() { const [allow, setAllow] = useState(29); const [verify, setVerify] = useState(79); const [block, setBlock] = useState(80); const [reason, setReason] = useState(''); const [saved, setSaved] = useState(false); return <div className="mx-auto max-w-5xl px-6 py-8"><PageTitle eyebrow="Controls" title="Fraud Policies" detail="Manage decision thresholds with an auditable confirmation step." /><Panel className="p-6"><div className="flex items-start justify-between"><div><h2 className="text-lg font-semibold text-ink">Default authorization policy</h2><p className="mt-1 text-sm text-ink-muted">Version 1.2 · Last updated by Risk Manager</p></div><Pill value="ENABLED" /></div><div className="mt-6 grid gap-4 md:grid-cols-3"><PolicyInput label="Allow maximum score" value={allow} onChange={setAllow} /><PolicyInput label="Verification maximum score" value={verify} onChange={setVerify} /><PolicyInput label="Block minimum score" value={block} onChange={setBlock} /></div><div className="mt-6 rounded-xl bg-amber-400/15 p-4 text-sm text-amber-800 ring-1 ring-inset ring-amber-500/30 dark:text-amber-200"><strong>Threshold changes affect live authorization behavior.</strong><p className="mt-1">Every change requires a reason and is recorded in Audit Logs.</p></div><label className="mt-6 block text-sm font-semibold text-ink">Reason for change<input value={reason} onChange={(event) => setReason(event.target.value)} className="glass-field mt-2 w-full rounded-lg px-3 py-2.5 font-normal" placeholder="Describe why this policy is changing" /></label><button disabled={!reason.trim()} onClick={() => setSaved(true)} className={`mt-5 ${btnPrimary}`}>{saved ? 'Policy change submitted' : 'Confirm and save policy'}</button></Panel><Panel className="mt-6 overflow-hidden"><div className="border-b border-separator px-5 py-4"><h2 className="font-semibold text-ink">Policy history</h2></div><div className="divide-y divide-separator">{['v1.2 · 25 Aug 2026 · Risk Manager · Updated verification threshold', 'v1.1 · 12 Aug 2026 · Administrator · Enabled policy', 'v1.0 · 01 Aug 2026 · System · Initial policy'].map((entry) => <p key={entry} className="px-5 py-4 text-sm text-ink-muted">{entry}</p>)}</div></Panel></div>; }
function PolicyInput({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) { return <label className="text-sm font-semibold text-ink">{label}<input type="number" min="0" max="100" value={value} onChange={(event) => onChange(Number(event.target.value))} className="glass-field mt-2 block w-full rounded-lg px-3 py-2.5 font-normal" /></label>; }

export function ModelsPage() { return <div className="mx-auto max-w-7xl px-6 py-8"><PageTitle eyebrow="Intelligence" title="AI Models" detail="Monitor deployed model quality and history. Model changes require model-management access." /><Panel className="p-6"><div className="flex flex-col justify-between gap-4 md:flex-row"><div><p className="text-sm text-ink-muted">Currently deployed</p><h2 className="mt-1 text-2xl font-semibold tracking-tight text-ink">VeriPay Fraud Detection Model</h2><p className="mt-1 text-sm text-ink-muted">Version v1.2 · deployed 18 Aug 2026</p></div><Pill value="DEPLOYED" /></div><div className="mt-6 grid gap-4 sm:grid-cols-3"><Kpi label="AUC" value="0.97" change="+0.02 vs v1.1" tone="teal" /><Kpi label="Precision" value="0.91" change="+0.01 vs v1.1" tone="teal" /><Kpi label="Recall" value="0.88" change="Stable" /></div></Panel><Panel className="mt-6 overflow-hidden"><div className="border-b border-separator px-5 py-4"><h2 className="font-semibold text-ink">Model history</h2></div><table className="w-full text-left text-sm"><thead className="bg-white/40 text-[11px] uppercase tracking-[0.14em] text-ink-subtle dark:bg-white/[0.04]"><tr>{['Model', 'Version', 'AUC', 'Precision', 'Recall', 'Deployment date', 'Status'].map((heading) => <th key={heading} className="px-5 py-3 font-semibold">{heading}</th>)}</tr></thead><tbody>{[['VeriPay Fraud Detection', 'v1.2', '0.97', '0.91', '0.88', '18 Aug 2026', 'DEPLOYED'], ['VeriPay Fraud Detection', 'v1.1', '0.95', '0.90', '0.88', '02 Jul 2026', 'RETIRED'], ['VeriPay Fraud Detection', 'v1.0', '0.91', '0.84', '0.81', '14 May 2026', 'RETIRED']].map((row) => <tr key={row[1]} className="border-t border-separator transition-colors hover:bg-white/50 dark:hover:bg-white/[0.04]">{row.map((cell) => <td key={cell} className="px-5 py-4 text-ink">{cell === 'DEPLOYED' || cell === 'RETIRED' ? <Pill value={cell} /> : cell}</td>)}</tr>)}</tbody></table></Panel></div>; }

export function ReportsPage() { const [generated, setGenerated] = useState(''); return <div className="mx-auto max-w-5xl px-6 py-8"><PageTitle eyebrow="Reporting" title="Reports" detail="Generate operational and regulatory reports for your institution." /><div className="grid gap-4 md:grid-cols-2">{['Daily fraud report', 'Weekly fraud report', 'Monthly fraud report', 'Fraud prevention report', 'Transaction report', 'Risk report', 'Merchant fraud report'].map((report) => <Panel key={report} className="flex items-center justify-between p-5 transition duration-300 hover:-translate-y-0.5 hover:shadow-glass-lg"><div><h2 className="font-semibold text-ink">{report}</h2><p className="mt-1 text-xs text-ink-muted">CSV and PDF export available</p></div><button onClick={() => setGenerated(report)} className="glass-field rounded-lg px-3 py-2 text-xs font-semibold text-ink transition hover:bg-white/70 dark:hover:bg-white/15">Generate</button></Panel>)}</div>{generated && <div className="mt-5 rounded-xl bg-emerald-500/10 p-4 text-sm text-emerald-800 ring-1 ring-inset ring-emerald-500/30 dark:text-emerald-300">{generated} generated successfully. Export options are ready.</div>}</div>; }

export function AuditPage() { return <div className="mx-auto max-w-7xl px-6 py-8"><PageTitle eyebrow="Governance" title="Audit Logs" detail="Review administrative actions and access history across the bank console." action={<button className={btnSecondary}>Export logs</button>} /><Panel className="overflow-hidden"><div className="flex gap-3 border-b border-separator p-5"><input className="glass-field flex-1 rounded-lg px-3 py-2.5 text-sm" placeholder="Filter by user or action..." /><select className="glass-field rounded-lg px-3 py-2.5 text-sm"><option>All resources</option><option>Transaction</option><option>Alert</option><option>Fraud Policy</option></select></div><table className="min-w-[850px] w-full text-left text-sm"><thead className="bg-white/40 text-[11px] uppercase tracking-[0.14em] text-ink-subtle dark:bg-white/[0.04]"><tr>{['Timestamp', 'User', 'Role', 'Action', 'Resource', 'Resource ID', 'Result'].map((heading) => <th key={heading} className="px-5 py-3 font-semibold">{heading}</th>)}</tr></thead><tbody>{auditLogs.map((row) => <tr key={`${row[0]}-${row[5]}`} className="border-t border-separator transition-colors hover:bg-white/50 dark:hover:bg-white/[0.04]">{row.map((cell) => <td key={cell} className="px-5 py-4 text-ink">{cell === 'SUCCESS' ? <Pill value={cell} /> : cell}</td>)}</tr>)}</tbody></table></Panel></div>; }

export function SettingsPage() { return <div className="mx-auto max-w-5xl px-6 py-8"><PageTitle eyebrow="Administration" title="Settings" detail="Manage your profile, security, notifications, and console preferences." /><div className="space-y-5">{[['Profile', 'Avery Morgan · Risk Manager · avery.morgan@veripay.example'], ['Security', 'MFA enabled · Last password change 28 days ago · 2 active sessions'], ['Notifications', 'Critical alerts and policy changes · Email and in-console'], ['Role & Permissions', 'Risk Manager · Can review transactions, manage policies, and generate reports'], ['System Preferences', 'Timezone: UTC · Date format: DD MMM YYYY · Theme: Light']].map(([title, detail]) => <Panel key={title} className="flex items-center justify-between p-5"><div><h2 className="font-semibold">{title}</h2><p className="mt-1 text-sm text-slate-500">{detail}</p></div><button className="text-sm font-semibold text-teal-700">Edit</button></Panel>)}</div></div>; }

export function BankNotificationsPage() { const [items, setItems] = useState(notifications); const unread = items.filter((item) => item.unread).length; return <div className="mx-auto max-w-5xl px-6 py-8"><PageTitle eyebrow="Operations feed" title="Notifications" detail="Important portfolio, model, and policy events for your role." action={<button onClick={() => setItems((current) => current.map((item) => ({ ...item, unread: false })))} className="rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold">Mark all as read</button>} /><div className="mb-4 text-sm text-slate-500">{unread} unread operational alerts</div><Panel className="divide-y divide-slate-100">{items.map((item, index) => <div key={item.text} className={`flex gap-4 p-5 ${item.unread ? 'bg-teal-50/40' : ''}`}><span className={`mt-1 h-3 w-3 shrink-0 rounded-full ${item.severity === 'CRITICAL' ? 'bg-red-600' : item.severity === 'HIGH' ? 'bg-orange-500' : item.severity === 'MEDIUM' ? 'bg-amber-400' : 'bg-blue-500'}`} /><div className="flex-1"><div className="flex flex-wrap justify-between gap-2"><h2 className="font-semibold">{item.text}</h2>{item.unread && <span className="text-xs font-bold text-teal-700">Unread</span>}</div><p className="mt-2 text-sm text-slate-500">{item.detail} · Severity {item.severity}</p></div>{item.unread && <button onClick={() => setItems((current) => current.map((entry, entryIndex) => entryIndex === index ? { ...entry, unread: false } : entry))} className="self-start text-xs font-bold text-teal-700">Mark read</button>}</div>)}</Panel></div>; }

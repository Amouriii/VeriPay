// FI Ops Console page — institutional fraud operations (Expansion §1 Dev5).
import { Link } from 'react-router-dom';
import { useTransactions, useRiskScore } from '../api/transactions';
import type { RiskScoreDto, TransactionDto } from '../types';

function RiskPill({ risk }: { risk: RiskScoreDto }) {
  const style = risk.band === 'BLOCK'
    ? 'bg-red-500/10 text-red-600 ring-red-500/25 dark:bg-red-400/15 dark:text-red-300 dark:ring-red-400/30'
    : risk.band === 'VERIFY'
      ? 'bg-amber-400/15 text-amber-700 ring-amber-500/30 dark:bg-amber-400/10 dark:text-amber-300 dark:ring-amber-400/25'
      : 'bg-emerald-500/10 text-emerald-700 ring-emerald-500/25 dark:bg-emerald-400/10 dark:text-emerald-300 dark:ring-emerald-400/25';
  return <span className={`inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${style}`}><span>{risk.unifiedScore}</span><span>{risk.band}</span></span>;
}

function RiskRow({ transaction }: { transaction: TransactionDto }) {
  const { data: risk, isLoading } = useRiskScore(transaction.transactionId);
  const amount = new Intl.NumberFormat(undefined, { style: 'currency', currency: transaction.currency }).format(transaction.amountMinor / 100);
  return (
    <tr className="border-b border-separator last:border-0 transition-colors hover:bg-white/50 dark:hover:bg-white/[0.04]">
      <td className="px-5 py-4"><Link className="font-semibold text-ink transition hover:text-accent" to={`/tx/${transaction.transactionId}`}>{transaction.transactionId}</Link><div className="mt-1 text-xs text-ink-subtle">Customer {transaction.userId}</div></td>
      <td className="px-5 py-4 text-ink-muted">{transaction.merchantId || 'Unknown merchant'}</td>
      <td className="px-5 py-4 font-semibold tabular-nums text-ink">{amount}</td>
      <td className="px-5 py-4">{isLoading || !risk ? <span className="text-xs text-ink-subtle">Evaluating</span> : <RiskPill risk={risk} />}</td>
      <td className="px-5 py-4 text-right"><Link className="text-sm font-semibold text-accent transition hover:text-accent-strong" to={`/tx/${transaction.transactionId}`}>Review <span aria-hidden="true">-&gt;</span></Link></td>
    </tr>
  );
}

function Metric({ label, value, detail, accent = 'slate' }: { label: string; value: string; detail: string; accent?: 'slate' | 'amber' | 'teal' }) {
  const dot = accent === 'amber' ? 'bg-amber-400' : accent === 'teal' ? 'bg-accent' : 'bg-ink/20 dark:bg-white/25';
  return <div className="glass-panel rounded-2xl p-5 transition duration-300 hover:-translate-y-0.5 hover:shadow-glass-lg"><div className="flex items-start justify-between"><p className="text-[13px] font-medium text-ink-muted">{label}</p><span className={`h-2 w-2 rounded-full ${dot}`} /></div><p className="mt-3 text-3xl font-semibold tracking-tight text-ink">{value}</p><p className="mt-2 text-xs text-ink-muted">{detail}</p></div>;
}

function Module({ label, detail }: { label: string; detail: string }) {
  return <div className="glass-panel rounded-2xl px-4 py-4"><p className="font-semibold text-ink">{label}</p><p className="mt-1 text-sm text-ink-muted">{detail}</p><span className="mt-3 inline-block text-[11px] font-semibold uppercase tracking-[0.12em] text-ink-subtle">Backend integration pending</span></div>;
}

export function FiOpsConsole() {
  const { data: transactions, isLoading, isError } = useTransactions();
  const items = transactions ?? [];
  const totalVolume = items.reduce((sum, transaction) => sum + transaction.amountMinor, 0);
  return (
    <main className="text-ink">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <header className="glass-panel mb-8 flex flex-col justify-between gap-4 rounded-2xl px-6 py-5 md:flex-row md:items-center"><div><p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">VeriPay / FI operations</p><h1 className="mt-2 text-2xl font-bold tracking-tight">Institutional risk desk</h1></div><div className="flex items-center gap-4 text-sm text-ink-muted"><span className="hidden md:inline">Portfolio overview</span><span className="hidden md:inline text-ink-subtle">·</span><span>Bank console</span><span className="rounded-full bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-700 ring-1 ring-inset ring-emerald-500/25 dark:text-emerald-300">Operations online</span></div></header>
        <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><p className="text-sm font-semibold text-accent">Today&apos;s control room</p><h2 className="mt-1 text-3xl font-bold tracking-tight">Portfolio risk overview</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-ink-muted">Monitor authorization exposure and route high-risk activity to review.</p></div><div className="text-left text-sm text-ink-muted md:text-right"><p className="font-semibold text-ink">Live transaction feed</p><p>Risk scores are evaluated per transaction</p></div></div>
        <section aria-label="Portfolio metrics" className="grid gap-4 md:grid-cols-3"><Metric label="Transactions observed" value={isLoading ? '...' : String(items.length)} detail="Current API window" /><Metric label="Review queue" value={isLoading ? '...' : String(items.length)} detail="Requires analyst attention" accent="amber" /><Metric label="Observed volume" value={isLoading ? '...' : formatCompactAmount(totalVolume)} detail="Across returned currencies" accent="teal" /></section>
        <section className="glass-panel mt-8 overflow-hidden rounded-2xl" aria-labelledby="queue-title"><div className="flex flex-col gap-3 border-b border-separator px-5 py-5 md:flex-row md:items-center md:justify-between"><div><h3 id="queue-title" className="text-lg font-semibold text-ink">Authorization review queue</h3><p className="mt-1 text-sm text-ink-muted">Open a transaction to inspect contributing risk signals.</p></div><span className="glass-field w-fit rounded-full px-3 py-1 text-xs font-semibold text-ink-muted">{items.length} records</span></div>{isLoading && <p className="px-5 py-10 text-sm text-ink-muted">Loading portfolio activity...</p>}{isError && <p className="px-5 py-10 text-sm text-red-600 dark:text-red-400">Portfolio activity could not be loaded. Check the API connection and try again.</p>}{!isLoading && !isError && items.length === 0 && <p className="px-5 py-10 text-sm text-ink-muted">No transactions are in the current review window.</p>}{!isLoading && !isError && items.length > 0 && <div className="overflow-x-auto"><table className="min-w-[680px] w-full text-left text-sm"><thead className="bg-white/40 text-[11px] uppercase tracking-[0.14em] text-ink-subtle dark:bg-white/[0.04]"><tr><th className="px-5 py-3 font-semibold">Transaction</th><th className="px-5 py-3 font-semibold">Merchant</th><th className="px-5 py-3 font-semibold">Amount</th><th className="px-5 py-3 font-semibold">Risk</th><th className="px-5 py-3 text-right font-semibold">Action</th></tr></thead><tbody>{items.map((transaction) => <RiskRow key={transaction.transactionId} transaction={transaction} />)}</tbody></table></div>}</section>
        <section className="mt-8 grid gap-4 md:grid-cols-3" aria-label="Bank operations modules"><Module label="Settlement monitoring" detail="Issuer batches and network settlement" /><Module label="Dispute lifecycle" detail="Chargebacks, evidence, and resolution" /><Module label="Regulatory audit" detail="Immutable actions and access history" /></section>
      </div>
    </main>
  );
}

function formatCompactAmount(amountMinor: number) {
  return new Intl.NumberFormat(undefined, { notation: 'compact', maximumFractionDigits: 1 }).format(amountMinor / 100);
}
